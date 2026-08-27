# ASRT audio and speech features

This reference covers ASRT's WAV readers and speech-feature extractors as self-contained operating guidance.

## WAV reader behavior

ASRT's `utils.ops` defines three relevant helpers.

### `read_wav_data(filename)`

Behavior:

1. Opens `filename` with Python's `wave` module.
2. Reads all frames.
3. Converts the raw frame bytes with `numpy.fromstring(..., dtype=numpy.short)`.
4. Reshapes the array as `(-1, num_channel)` and transposes to channel-first shape.
5. Returns `(wave_data, framerate, num_channel, num_sample_width)`.

For a mono 16-bit WAV, `wave_data` is shaped `(1, num_frames)`. For stereo it is `(2, num_frames)`.

### `read_wav_bytes(filename)`

This has the same metadata reads but returns raw bytes rather than decoded samples:

```text
(samples_data, framerate, num_channel, num_sample_width)
```

Use it when a caller needs to store or transmit WAV sample bytes separately from metadata.

### `decode_wav_bytes(samples_data, channels=1, byte_width=2)`

This decodes raw PCM bytes into the same channel-first matrix used by `read_wav_data()`.

- `byte_width == 2`: uses `numpy.short` / int16.
- `byte_width == 4`: source code uses `numpy.int`, which is removed in newer NumPy versions. Use `numpy.int32` or `numpy.int_` in new code if you need 4-byte decoding.
- Other byte widths raise an exception with an unsupported-byte-width message.

Stock ASRT assumes sample bytes reshape cleanly into `channels`. Stereo data is not mixed down; feature extractors normally use the first channel through `wavsignal[0]` or otherwise expect a mono-like input.

## Sample-rate and duration constraints

ASRT's spectrogram-style feature code enforces 16 kHz at runtime:

```text
ValueError: ASRT currently only supports wav audio files with a sampling rate of 16000 Hz
```

Repository and installed verification facts:

- A 1-second, 16 kHz, mono zero waveform passed to `Spectrogram.run()` has shape `(98, 200)`.
- `Spectrogram.run()` raises `ValueError` for 8 kHz input.
- The default speech model family expects data/features compatible with an approximately 16-second maximum audio duration; model details route to `acoustic-models`.

Duration-to-frame count for `Spectrogram` follows:

```text
frames = int(len(wavsignal[0]) / fs * 1000 - 25) // 10 + 1
frequency_bins = 200
```

At 16 kHz:

- 25 ms window = 400 samples.
- 10 ms shift = 160 samples.
- FFT magnitude keeps half of the 400-point result = 200 bins.
- 1.0 s audio: `int(16000 / 16000 * 1000 - 25) // 10 + 1 = 98` frames.

Very short clips shorter than the 25 ms window can compute a non-positive frame count and fail during array creation or downstream feature handling. Validate or pad short clips before sending them into ASRT-style spectrogram extraction.

## Feature classes

ASRT's `speech_features.speech_features` defines a common `SpeechFeatureMeta` base with `run(wavsignal, fs=16000)` and these concrete feature classes.

### `MFCC`

Constructor defaults:

```text
framesamplerate=16000, winlen=0.025, winstep=0.01, numcep=13, nfilt=26, preemph=0.97
```

Runtime behavior:

- Converts input to `float64`.
- Uses only `wavsignal[0]`.
- Computes MFCC coefficients via the bundled base feature functions.
- Computes first and second deltas with `delta(..., 2)`.
- Returns columns `[mfcc, delta, delta-delta]`, so the default feature width is `13 * 3 = 39`.

### `Logfbank`

Constructor defaults:

```text
framesamplerate=16000, nfilt=26
```

Runtime behavior:

- Converts input to `float64`.
- Calls `logfbank(wavsignal, fs, nfilt=self.nfilt)` from the base feature functions.
- Default width is `26` filters.

The source passes the full `wavsignal` array to `logfbank`, while the base function documentation expects a one-dimensional audio signal. When reproducing or troubleshooting, validate the actual input shape; mono channel data (`wavsignal[0]`) is the safer convention used by `MFCC` and `Spectrogram`.

### `Spectrogram`

Constructor defaults:

```text
framesamplerate=16000, timewindow=25, timeshift=10
```

Runtime behavior:

- Raises `ValueError` unless `fs == 16000`.
- Uses a fixed 400-sample Hamming window even though `window_length` is computed from `fs`.
- Steps by 160 samples for each 10 ms frame.
- Takes the absolute FFT and keeps the first 200 bins.
- Applies `log(x + 1)`.
- Returns shape `(num_frames, 200)`.

This is the primary data/feature compatibility path for default acoustic models.

### `SpecAugment`

Constructor and base spectrogram computation match `Spectrogram`. After `log(x + 1)`, it randomly chooses one of four modes:

- 60%: no masking.
- 15%: mask a horizontal/time span.
- 15%: mask a vertical/frequency span.
- 10%: source code attempts combined masking.

Because mask locations and widths use Python `random.randint()`, outputs are not deterministic unless the caller controls the global random seed. Use plain `Spectrogram` for deterministic data validation and `SpecAugment` only when training/evaluation logic intentionally wants augmentation.

## Base feature functions

`speech_features.base` provides reusable signal-processing functions adapted from the common `python_speech_features` style:

- `calculate_nfft(samplerate, winlen)`: smallest power-of-two FFT size that covers the analysis window.
- `mfcc(...)`: MFCC coefficients from a 1-D signal; defaults to 25 ms windows and 10 ms steps.
- `fbank(...)`: Mel-filterbank energies.
- `logfbank(...)`: log Mel-filterbank energies.
- `ssc(...)`: spectral subband centroids.
- `delta(feat, N)`: delta features with `N >= 1`.

Only `MFCC` and `Logfbank` expose a direct high-level feature class around these in the inspected feature module, besides `Spectrogram` and `SpecAugment`.

## Recording utility is reference-only

`speech_recorder.py` defines a PyAudio microphone recorder that can create ASRT-compatible WAV files with defaults:

- `duration=10`
- `channels=1`
- `sampling_rate=16000`
- `sampling_bits=16`
- `chunk_size=1024`

It has hardware, microphone, and PyAudio side effects. This sub-skill therefore documents it as reference-only and does not bundle an active recorder. If a future task needs generated test audio, prefer deterministic wave-file synthesis, existing user-provided WAVs, or the safe inspection script in this sub-skill.