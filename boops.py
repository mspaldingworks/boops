import gc, os, sys, time
import importlib

from itertools import cycle

import background

import numpy as np

from scipy.io import wavfile
import simpleaudio as sa

import filters

background.n = 16
gc.disable()

filters_m_time = os.path.getmtime('filters.py')


@background.task
def async_reload_filters():
    global filters_m_time
    try:
        if not filters_m_time or filters_m_time < os.path.getmtime('filters.py'):
            importlib.reload(filters)
            filters_m_time = os.path.getmtime('filters.py')
            print('> Reloaded filter')
    except Exception as e:
        print(e)


@background.task
def async_print(s):
    print(s)


@background.task
def play_beat_at(dm, beat, at, t):
    while True:
        if time.time() - t > at:
            try:
                snd = filters.run(beat)
                drift = time.time() - t - at
                sa.play_buffer(snd, 1, 2, 44100)
                dm.set_drift(drift)
            except Exception as e:
                print(e)
            return


@background.task
def async_load(dm):
    dm.load_boops()


class DrumMachine:
    verbose = True
    beats_m_time = None

    def __init__(self, fn, tempo):
        self.fn = fn

        self.beat = 0
        self.drift = []
        self.bar = []
        self.samples = []

        self.has_new_bar = False

        self.max_drift = None
        self.beats_m_time = None

        self.set_tempo(tempo)
        self.load_boops()

    def set_tempo(self, tempo):
        self.tempo = tempo
        self.gap = 30 / tempo

    def set_drift(self, d):
        self.drift = [round(d, 3)] + self.drift[:31]

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
                if s.startswith('--'):
                    if 'tempo:' in s:
                        _, tempo = s.split('tempo:', 1)
                        self.set_tempo(int(tempo.strip()))
                else:
                    fn, bar = s.lower().split(" ", 1)

                    if 'x' in bar.lower():
                        fs, data = wavfile.read(fn)
                        samples.append(data)
                        bars.append(bar)

        bars = [
            b.split() for b in bars
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
                        async_reload_filters()
                        async_print(f'AVG Drift: {round(sum(self.drift) / len(self.drift), 4)}')

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
