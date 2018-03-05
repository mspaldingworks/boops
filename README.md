`boops` is an incredibly simple Python drum machine. It doesn't keep time well but it does make fun noises.

It's somewhat based on the [Beats Drum Machine](http://beatsdrummachine.com) project.


### Installation

Clone the repo and install the requirements with `pipenv`:

```
> pipenv install
```

Find some samples.
The included `test.boops` uses the [Hammerhead](http://beatsdrummachine.com/download/) samples from the ruby [Beats Drum Machine](http://beatsdrummachine.com).
Extract these into `samples/hammerhead` to keep things organised.

Run `boops` with your `.boops` file as the last argument (there are no other arguments):

```
> python boops.py test.boops
```

While it's running you can modify the `test.boops` file to change the beat.


### Boops file format

- Lines that start with `#` and blank lines are ignored

- Lines that start with `--` are metadata
    - `-- tempo: <xx>` will set the tempo

- All other lines must follow the format `<sample> <bar>`
    - Where `<sample>` is a WAV file for your sample
    - And `<bar>` is a space-separated list of `.` or `x`
        - `x` is a boop
    - You can use any number of whitespace characters to separate things (i.e. you want to line up multiple beats, or separate into bars)


### Discoveries

- Trying to do two things at the exact same time in Python is perilous
- Disabling garbage collection is a relatively OK thing to do
- Using numpy arrays to represent the WAV files results in much more consistent playback
- Musical terminology is not my thing
- I have very little musical talent
