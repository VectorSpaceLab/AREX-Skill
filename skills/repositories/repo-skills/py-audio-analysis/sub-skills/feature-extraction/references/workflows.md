# Feature Extraction Workflows

These workflows are self-contained operating recipes for pyAudioAnalysis 0.3.14 feature extraction. They assume the package and its Python dependencies are importable in the active environment.

## 1. Extract short-term features from a WAV file

Use this when the user needs frame-level acoustic descriptors from one file.

```python
import numpy as np
from pyAudioAnalysis import audioBasicIO, ShortTermFeatures

sampling_rate, signal = audioBasicIO.read_audio_file("clip.wav")
if sampling_rate <= 0 or signal.size == 0:
    raise ValueError("Could not decode audio file")

signal = audioBasicIO.stereo_to_mono(signal)
if getattr(signal, "ndim", 1) != 1:
    raise ValueError("Expected mono or stereo audio; convert multichannel input first")

short_window = int(round(0.050 * sampling_rate))
short_step = int(round(0.050 * sampling_rate))
if short_window <= 0 or short_step <= 0 or len(signal) < short_window:
    raise ValueError("Audio is too short for the requested short-term window")

features, names = ShortTermFeatures.feature_extraction(
    signal,
    sampling_rate,
    short_window,
    short_step,
    deltas=True,
)

assert features.shape[0] == len(names)
assert features.shape[1] > 0
assert np.isfinite(features).all()
```

Default output orientation is feature rows by time-window columns. Transpose when writing table rows by frame:

```python
np.savetxt("clip_short.csv", features.T, delimiter=",")
np.save("clip_short.npy", features)
```

## 2. Extract short-term and mid-term matrices from an in-memory array

Use this when the caller already has PCM samples or synthetic data.

```python
import numpy as np
from pyAudioAnalysis import ShortTermFeatures, MidTermFeatures

sampling_rate = 16000
t = np.arange(int(2.0 * sampling_rate)) / sampling_rate
signal = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

short_window = short_step = int(round(0.050 * sampling_rate))
mid_window = mid_step = int(round(1.0 * sampling_rate))

# Guard against mid_step / short_step rounding to zero inside pyAudioAnalysis.
if int(round(mid_step / short_step)) < 1:
    raise ValueError("mid_step must be at least about one short_step")

short_features, short_names = ShortTermFeatures.feature_extraction(
    signal, sampling_rate, short_window, short_step
)
mid_features, short_features_from_mid, mid_names = MidTermFeatures.mid_feature_extraction(
    signal, sampling_rate, mid_window, mid_step, short_window, short_step
)

assert short_features.shape[0] == len(short_names)
assert mid_features.shape[0] == len(mid_names)
assert short_features_from_mid.shape[0] == short_features.shape[0]
```

Interpretation:

- `short_features` rows are the base/delta feature series.
- `mid_features` rows are mean/std summaries of the short-term rows.
- `mid_features.T` is the usual table orientation when each row should be one mid-term window.

## 3. Extract spectrogram and chromagram matrices

Use this for visualization-ready representations or downstream experiments that need spectral/chroma matrices.

```python
import contextlib
import io
from pyAudioAnalysis import ShortTermFeatures

# Reuse `signal`, `sampling_rate`, `short_window`, and `short_step` from earlier workflows.

# spectrogram() prints its shape in pyAudioAnalysis 0.3.14; capture stdout if needed.
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    specgram, spec_time, spec_freq = ShortTermFeatures.spectrogram(
        signal,
        sampling_rate,
        short_window,
        short_step,
        plot=False,
        show_progress=False,
    )

chromagram, chroma_time, chroma_labels = ShortTermFeatures.chromagram(
    signal,
    sampling_rate,
    short_window,
    short_step,
    plot=False,
    show_progress=False,
)

assert specgram.shape[0] == len(spec_time)
assert specgram.shape[1] == len(spec_freq)
assert chromagram.shape[0] == len(chroma_time)
assert chromagram.shape[1] == len(chroma_labels) == 12
```

Keep `plot=False` for automation. If the user asks for image display, first make sure a Matplotlib backend/display is configured; plotting behavior itself is not validated by this sub-skill's smoke helper.

## 4. Extract one averaged feature vector per file in a folder

Use this for dataset summarization or as the feature stage before handing off to classification/regression.

```python
import numpy as np
from pyAudioAnalysis import MidTermFeatures

features, accepted_files, feature_names = MidTermFeatures.directory_feature_extraction(
    "audio_folder",
    mid_window=1.0,
    mid_step=1.0,
    short_window=0.050,
    short_step=0.050,
    compute_beat=True,
)

features = np.atleast_2d(features)
if features.size == 0 or len(accepted_files) == 0:
    raise ValueError("No usable audio files were accepted")

assert features.shape[1] == len(feature_names)
```

Notes:

- Folder wrapper window/step arguments are seconds.
- Files shorter than roughly 0.2 seconds are skipped.
- `compute_beat=True` appends `bpm` and `ratio` to the feature vector.
- Training labels, model selection, and class/regression target handling belong to `classification-regression`.

## 5. Export mid-term and optional short-term features to NPY/CSV

Use the package wrapper when the user asks for matrix files from one audio file.

```python
from pathlib import Path
from pyAudioAnalysis import MidTermFeatures

prefix = Path("features/clip")
prefix.parent.mkdir(parents=True, exist_ok=True)

MidTermFeatures.mid_feature_extraction_to_file(
    file_path="clip.wav",
    mid_window=1.0,
    mid_step=1.0,
    short_window=0.050,
    short_step=0.050,
    output_file=str(prefix),
    store_short_features=True,
    store_csv=True,
    plot=False,
)
```

Expected outputs:

- `features/clip_mt.npy`
- `features/clip_mt.csv`
- `features/clip_st.npy`
- `features/clip_st.csv`

If the user needs a custom output set that also includes spectrogram or chromagram matrices, use the bundled `scripts/feature_smoke.py --output-prefix ... --store-csv` helper as a safe template.

## 6. Use the bundled smoke helper

The helper verifies imports, synthesizes a non-silent tone unless a WAV path is provided, extracts short/mid/spectral/chroma matrices, checks row/name consistency, and prints JSON.

```bash
python scripts/feature_smoke.py --duration 2.0
python scripts/feature_smoke.py --input-wav clip.wav --output-prefix features/clip --store-csv
python scripts/feature_smoke.py --compute-beat --duration 4.0
```

Use the JSON fields to confirm:

- `short_features.shape[0] == short_features.name_count`
- `mid_features.shape[0] == mid_features.name_count`
- every reported `finite` field is `true`
- optional `written_files` paths exist when an output prefix was requested

## Boundary reminders

- Do not expand these recipes into classifier/regression training. Extract matrices here, then route training and prediction to `classification-regression`.
- Do not use this sub-skill for diarization, HMM segmentation, silence removal, or thumbnailing even though those workflows consume mid-term features internally; route to `segmentation-diarization`.
- Do not use legacy top-level scripts as runtime dependencies. Prefer package imports and the bundled helper in this sub-skill.
