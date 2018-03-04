import gc, os, sys, time
from itertools import cycle

import background
import simpleaudio as sa

background.n = 16
gc.disable()

@background.task
def async_print(s):
    print(s)


@background.task
def play_beat_at(dm, beat, at, t):
    while True:
        if time.time() - t > at:
            drift = time.time() - t - at
            beat.play()
            dm.set_drift(drift)        
            return


@background.task
def async_load(dm):
    dm.load_boops()


class DrumMachine:
    verbose = True
    beats_m_time = None

    def __init__(self, fn, tempo):
        self.gap = 30 / tempo
        print(self.gap)
        self.fn = fn

        self.bar = []
        self.samples = []
        self.beats_m_time = None

        self.load_boops()
        self.beat = 0
        self.has_new_bar = False
        self.max_drift = None
        self.drift = []

    def set_drift(self, d):
        self.drift = [round(d, 3)] + self.drift[:31]

        if self.verbose and self.beat % 16 == 0:
            async_print(f'AVG Drift: {round(sum(self.drift) / len(self.drift), 4)}')

        if not self.max_drift or d > self.max_drift:
            self.max_drift = d
            if self.verbose:
                async_print(f'MAX Drift: {self.beat}: {round(self.max_drift, 4)}')


    def load_boops(self):
        if self.beats_m_time == os.path.getmtime(self.fn):
            return

        self.beats_m_time = os.path.getmtime(self.fn)

        bars = []
        samples = []

        s = open(self.fn).read()

        for s in s.splitlines():
            s = s.strip()

            if s and not s.startswith('#'):
                fn, bar = s.lower().split(" ", 1)
                samples.append(sa.WaveObject.from_wave_file(fn))
                bars.append(bar)

        bars = [
            b.split() for b in bars
            if 'x' in b.lower()
        ]

        max_len = max([len(x) for x in bars])

        bars = [
            b * int(max_len / len(b))
            for b in bars
        ]

        for b in bars:
            async_print(b)

        bar = cycle(zip(*bars))
        self.bar = bar
        self.samples = samples
        self.has_new_bar = True

    def loop(self):
        t = time.time()
        bar, samples = self.bar, self.samples
        self.has_new_bar = False

        try:
            while True:
                if time.time() - t > self.gap / 2:
                    beats = next(bar)
                    for i, b in enumerate(beats):
                        if b == 'x':
                            play_beat_at(self, samples[i], self.gap, t)

                    t = time.time()
                    self.beat += 1
                    async_load(self)

                    if self.beat % 16 == 0:
                        if self.has_new_bar:
                            async_print('Reloading bar...')
                            bar, samples = self.bar, self.samples
                            self.has_new_bar = False
                    
                    time.sleep(self.gap / 2)

        except KeyboardInterrupt:
            return


fn = sys.argv[-1]
dm = DrumMachine(fn, 110)
dm.loop()
