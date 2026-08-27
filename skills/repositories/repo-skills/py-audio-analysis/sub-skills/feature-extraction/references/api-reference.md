# Feature Extraction API Reference

This reference covers pyAudioAnalysis 0.3.14 feature extraction APIs owned by this sub-skill. Use package imports, not source-file execution:

```python
from pyAudioAnalysis import audioBasicIO
from pyAudioAnalysis import ShortTermFeatures
from pyAudioAnalysis import MidTermFeatures
```

## Input audio preparation

### `audioBasicIO.read_audio_file(input_file)`

Reads an audio file and returns:

```python
sampling_rate, signal = audioBasicIO.read_audio_file(input_file)
```

- `sampling_rate`: integer Hz. Treat `<= 0` as a failed read/decode.
- `signal`: NumPy array of samples. WAV input is read through SciPy; AIFF and generic media formats use additional decoders.
- Supported by the package reader: `.wav`, `.aif`, `.aiff`, `.mp3`, `.au`, `.ogg`.
- For this sub-skill's feature workflows, prefer WAV when possible. MP3/media conversion and decoder setup belong to `cli-and-io`.

### `audioBasicIO.stereo_to_mono(signal)`

Converts common stereo arrays to mono before feature extraction:

```python
signal = audioBasicIO.stereo_to_mono(signal)
```

- If `signal.ndim == 2` and `shape[1] == 1`, it flattens to 1-D.
- If `signal.ndim == 2` and `shape[1] == 2`, it averages the two channels.
- Other multichannel layouts are returned unchanged; check `signal.ndim == 1` before calling the feature extractors.

## Unit conventions

pyAudioAnalysis mixes seconds and samples by wrapper level:

| API | Window/step units |
| --- | --- |
| `ShortTermFeatures.feature_extraction` | samples |
| `ShortTermFeatures.spectrogram` | samples |
| `ShortTermFeatures.chromagram` | samples |
| `MidTermFeatures.mid_feature_extraction` | samples |
| `MidTermFeatures.directory_feature_extraction` | seconds |
| `MidTermFeatures.mid_feature_extraction_to_file` | seconds |

Convert seconds to samples only for the low-level APIs:

```python
short_window = int(round(0.050 * sampling_rate))
short_step = int(round(0.050 * sampling_rate))
mid_window = int(round(1.0 * sampling_rate))
mid_step = int(round(1.0 * sampling_rate))
```

Before calling, assert every converted value is positive, the signal has at least one full short-term window, and `int(round(mid_step / short_step)) >= 1` for mid-term extraction.

## Short-term acoustic features

### `ShortTermFeatures.feature_extraction(signal, sampling_rate, window, step, deltas=True)`

Extracts one feature vector per short-term frame:

```python
features, feature_names = ShortTermFeatures.feature_extraction(
    signal,
    sampling_rate,
    window=short_window_samples,
    step=short_step_samples,
    deltas=True,
)
```

Return contract:

- `features`: NumPy array shaped `(n_features, n_short_windows)`.
- `feature_names`: Python list with exactly `n_features` entries.
- With default `deltas=True`, pyAudioAnalysis returns 68 rows: 34 base features plus 34 `delta ...` rows.
- With `deltas=False`, it returns the 34 base feature rows only.

Base feature rows, in order:

1. `zcr`
2. `energy`
3. `energy_entropy`
4. `spectral_centroid`
5. `spectral_spread`
6. `spectral_entropy`
7. `spectral_flux`
8. `spectral_rolloff`
9. `mfcc_1` through `mfcc_13`
10. `chroma_1` through `chroma_12`
11. `chroma_std`

Shape checks to keep in every workflow:

```python
assert features.shape[0] == len(feature_names)
assert features.shape[1] > 0
assert np.isfinite(features).all()
```

## Spectrogram and chromagram representations

### `ShortTermFeatures.spectrogram(signal, sampling_rate, window, step, plot=False, show_progress=False)`

```python
specgram, time_axis, freq_axis = ShortTermFeatures.spectrogram(
    signal,
    sampling_rate,
    short_window_samples,
    short_step_samples,
    plot=False,
    show_progress=False,
)
```

Return contract:

- `specgram`: NumPy array shaped approximately `(n_time_frames, window // 2)`.
- `time_axis`: seconds per spectrogram row.
- `freq_axis`: Hz per frequency bin.
- The 0.3.14 implementation prints `specgram.shape` to stdout even when `plot=False`; capture stdout in scripts if clean JSON/CSV output matters.

### `ShortTermFeatures.chromagram(signal, sampling_rate, window, step, plot=False, show_progress=False)`

```python
chromagram, time_axis, chroma_axis = ShortTermFeatures.chromagram(
    signal,
    sampling_rate,
    short_window_samples,
    short_step_samples,
    plot=False,
    show_progress=False,
)
```

Return contract:

- `chromagram`: NumPy array shaped `(n_time_frames, 12)`.
- `time_axis`: seconds per chromagram row.
- `chroma_axis`: the 12 chroma labels `A`, `A#`, `B`, `C`, `C#`, `D`, `D#`, `E`, `F`, `F#`, `G`, `G#`.

Keep `plot=False` in headless or automated environments. Use plotting only when an interactive display or non-interactive Matplotlib backend is already configured.

## Mid-term feature extraction

### `MidTermFeatures.mid_feature_extraction(signal, sampling_rate, mid_window, mid_step, short_window, short_step)`

Computes short-term features first, then mean/std statistics over mid-term windows:

```python
mid_features, short_features, mid_feature_names = MidTermFeatures.mid_feature_extraction(
    signal,
    sampling_rate,
    mid_window_samples,
    mid_step_samples,
    short_window_samples,
    short_step_samples,
)
```

Return contract:

- `mid_features`: NumPy array shaped `(2 * n_short_feature_rows, n_mid_windows)`.
- `short_features`: the underlying short-term matrix shaped `(n_short_feature_rows, n_short_windows)`.
- `mid_feature_names`: row names ending in `_mean` and `_std`.
- pyAudioAnalysis applies `np.nan_to_num` to the mid-term matrix, but you should still check finiteness and signal variance for silent/constant inputs.

With default short-term deltas inside this function, typical row counts are:

- `short_features.shape[0] == 68`
- `mid_features.shape[0] == len(mid_feature_names) == 136`

## Directory-level averaged features and beat features

### `MidTermFeatures.directory_feature_extraction(folder_path, mid_window, mid_step, short_window, short_step, compute_beat=True)`

Extracts one long-term averaged feature vector per audio file in a folder:

```python
features, file_paths, feature_names = MidTermFeatures.directory_feature_extraction(
    folder_path,
    mid_window=1.0,
    mid_step=1.0,
    short_window=0.050,
    short_step=0.050,
    compute_beat=True,
)
```

Important behavior:

- Window/step arguments are seconds, not samples.
- Supported file patterns include `.wav`, `.aif`, `.aiff`, `.mp3`, `.au`, `.ogg`.
- Zero-byte files, failed decodes, and files shorter than roughly 0.2 seconds are skipped.
- `compute_beat=True` appends `bpm` and `ratio` to `feature_names` and to each averaged feature vector.
- If only one file is accepted, `features` may be returned as a 1-D vector; normalize with `np.atleast_2d(features)` when writing tabular output.

For direct beat extraction from an existing short-term matrix, pyAudioAnalysis also exposes:

```python
bpm, ratio = MidTermFeatures.beat_extraction(short_features, short_step_seconds, plot=False)
```

Use beat values as summary descriptors, not as a tempo-tracking benchmark, unless you add domain-specific validation.

## File-to-NPY/CSV export

### `MidTermFeatures.mid_feature_extraction_to_file(file_path, mid_window, mid_step, short_window, short_step, output_file, store_short_features=False, store_csv=False, plot=False)`

Reads an audio file, extracts mid-term features, and writes output files with suffixes derived from `output_file`:

```python
MidTermFeatures.mid_feature_extraction_to_file(
    file_path="clip.wav",
    mid_window=1.0,
    mid_step=1.0,
    short_window=0.050,
    short_step=0.050,
    output_file="features/clip",
    store_short_features=True,
    store_csv=True,
    plot=False,
)
```

Outputs:

| Flag combination | Files written |
| --- | --- |
| default | `features/clip_mt.npy` |
| `store_csv=True` | `features/clip_mt.csv` in addition to NPY |
| `store_short_features=True` | `features/clip_st.npy` |
| both flags | `_mt.npy`, `_mt.csv`, `_st.npy`, `_st.csv` |

CSV files are transposed so rows correspond to time windows and columns correspond to feature rows.

## Minimal array recipe

```python
import numpy as np
from pyAudioAnalysis import ShortTermFeatures, MidTermFeatures

sampling_rate = 16000
t = np.arange(2 * sampling_rate) / sampling_rate
signal = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

short_window = short_step = int(round(0.050 * sampling_rate))
mid_window = mid_step = int(round(1.0 * sampling_rate))

short_features, short_names = ShortTermFeatures.feature_extraction(
    signal, sampling_rate, short_window, short_step
)
mid_features, _, mid_names = MidTermFeatures.mid_feature_extraction(
    signal, sampling_rate, mid_window, mid_step, short_window, short_step
)

assert short_features.shape[0] == len(short_names)
assert mid_features.shape[0] == len(mid_names)
```
