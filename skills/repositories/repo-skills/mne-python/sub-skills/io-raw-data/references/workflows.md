# IO / Raw Workflows

All examples use bundled knowledge only. Replace filenames and channel names with user-provided values.

## Choose a reader

1. Identify the actual file family, not just the suffix. Some suffixes are ambiguous (`.cnt`, `.bin`, `.dat`) or refer to sidecar files rather than data files.
2. For common unambiguous files, start with generic dispatch:

```python
import mne

raw = mne.io.read_raw("recording_raw.fif", preload=False)
print(raw)
print(raw.info["sfreq"], raw.ch_names[:5])
```

3. Switch to a format-specific reader when you need format-specific options, when generic dispatch says multiple readers could apply, or when a marker/header sidecar was supplied:

```python
raw = mne.io.read_raw_brainvision(
    "subject01.vhdr",
    eog=("HEOGL", "HEOGR", "VEOGb"),
    misc="auto",
    preload=False,
)

raw = mne.io.read_raw_edf(
    "subject01.edf",
    eog=["EOG1", "EOG2"],
    stim_channel="auto",
    infer_types=True,
    preload=False,
)
```

4. Do a cheap sanity check before expensive processing:

```python
assert raw.info["sfreq"] > 0
assert raw.info["nchan"] == len(raw.ch_names)
print(raw.get_channel_types()[:10])
print(raw.annotations[:3])
```

5. If the data will feed event extraction, epoching, filtering, ICA, statistics, or plots, route those later steps to the owning sub-skill after creating and validating `raw`.

## Build a RawArray from NumPy data

Use `RawArray` when data are already in memory, simulated, or converted by a custom parser.

```python
import numpy as np
import mne

sfreq = 250.0
n_times = int(2 * sfreq)
times = np.arange(n_times) / sfreq

# MNE expects shape (n_channels, n_times), not (n_times, n_channels).
data = np.vstack([
    20e-6 * np.sin(2 * np.pi * 10 * times),  # EEG in volts
    15e-6 * np.cos(2 * np.pi * 12 * times),  # EEG in volts
    50e-6 * (times > 1.0),                   # EOG in volts
    np.zeros(n_times),                       # stim/misc arbitrary units
])
data[3, [100, 250]] = [1, 2]

info = mne.create_info(
    ch_names=["EEG Fz", "EEG Cz", "EOG blink", "STI 014"],
    sfreq=sfreq,
    ch_types=["eeg", "eeg", "eog", "stim"],
)
raw = mne.io.RawArray(data, info)
raw.set_annotations(mne.Annotations([0.8], [0.2], ["BAD_blink"]))

assert raw.get_data().shape == (4, n_times)
assert raw.get_channel_types() == ["eeg", "eeg", "eog", "stim"]
```

Use the bundled helper for a deterministic smoke object:

```bash
python sub-skills/io-raw-data/scripts/create_synthetic_raw.py --summary-json
python sub-skills/io-raw-data/scripts/create_synthetic_raw.py --output synthetic_raw.fif --overwrite
```

If a user supplies data shaped `(n_times, n_channels)`, transpose it before `RawArray`. If the user supplies EEG-like data in microvolts, multiply by `1e-6` to convert to volts.

## Manage preload and memory

Default reader behavior is lazy/on-demand disk reads:

```python
raw = mne.io.read_raw_fif("large_raw.fif", preload=False)
print(raw.preload)  # False
```

Use this pattern for large files:

```python
raw = mne.io.read_raw_fif("large_raw.fif", preload=False)
raw = raw.copy().crop(tmin=0, tmax=120).pick(["eeg", "eog"])
raw.load_data()  # RAM only after reducing size
```

Use a memmap file when data must be writable but RAM is tight:

```python
raw = mne.io.read_raw_fif("large_raw.fif", preload=False)
raw.load_data(memmap="raw_preload.dat")
```

Rules of thumb:

- Filtering, resampling, direct item assignment, adding stim-channel events, and some analysis operations require preloaded data.
- `raw.get_data(picks=..., start=..., stop=...)` can extract a small slice without permanently preloading the whole object.
- `preload=True` loads into RAM; `preload="filename.dat"` or `load_data(memmap="filename.dat")` uses memory mapping.
- Copy before destructive changes: `work = raw.copy().crop(...).pick(...)`.

## Channel names, types, bads, and picks

Inspect:

```python
print(raw.ch_names)
print(raw.get_channel_types())
print(raw.info["bads"])
```

Pick or drop channels in-place, preferably on a copy:

```python
eeg_eog = raw.copy().pick(picks=["eeg", "eog"])
subset = raw.copy().pick(["EEG Fz", "EEG Cz"])
without_bad = raw.copy().drop_channels(["MEG 2443"], on_missing="ignore")
ordered = raw.copy().reorder_channels(["EOG blink", "EEG Fz", "EEG Cz"])
```

Rename and type-fix channels:

```python
raw = raw.copy()
raw.rename_channels({"EOG 061": "EOG_blink"})
raw.set_channel_types({"EEG_001": "eog"})
raw.info["bads"] = ["EEG 053"]
```

Selection utilities:

```python
eeg_idx = mne.pick_types(raw.info, meg=False, eeg=True, exclude="bads")
explicit_idx = mne.pick_channels(raw.ch_names, include=["EEG Fz", "EEG Cz"])
data, times = raw.get_data(picks=eeg_idx, start=0, stop=1000, return_times=True)
```

Keep FIF name limits in mind when saving to FIF: long or duplicate names may be renamed for compatibility by MNE methods. If the task depends on exact names, check `raw.ch_names` after creation, rename, and save/reload.

## Add raw-level annotations

```python
ann = mne.Annotations(
    onset=[1.0, 3.5],
    duration=[0.25, 0.5],
    description=["BAD_motion", "task/rest"],
)
raw = raw.copy().set_annotations(ann)
```

Important behavior:

- `raw.set_annotations(ann)` replaces existing annotations. Preserve first when appending: `raw.set_annotations(raw.annotations + ann)`.
- Descriptions beginning with `BAD` or `bad` are treated as bad spans by many downstream operations with `reject_by_annotation` controls.
- `orig_time=None` means annotation onsets are interpreted relative to the recording's first sample and measurement date; `raw.first_samp / raw.info['sfreq']` can shift stored onsets for files with nonzero first sample.
- Annotations outside the raw time range are omitted or warned/error depending on method options.
- Annotation file I/O is separate from Raw file I/O: `raw.annotations.save("annotations.csv", overwrite=True)` and `mne.read_annotations("annotations.csv")`.

## Concatenate Raw objects

Use MNE helpers rather than stacking arrays by hand:

```python
raw1 = raw.copy().crop(0, 10)
raw2 = raw.copy().crop(20, 30)
combined = mne.io.concatenate_raws([raw1, raw2], preload=None, on_mismatch="raise")
```

Behavior to account for:

- If all input objects have the same concrete raw type, the first object is modified in-place and returned.
- If input raw types differ, MNE preloads and returns a new `RawArray`.
- Boundary annotations `BAD boundary` and `EDGE boundary` are added at joins. Remove them only if the task explicitly treats the result as continuous and downstream methods should not reject boundaries.
- `Info` objects must be compatible. Channel names/order/types, SSP projectors, compensation, and other critical metadata are checked.
- Saving a concatenated raw object stores measurement info from the first raw, which may be unsuitable for some external tools.

## Save and export boundaries

Native MNE save:

```python
saved = raw.save("subject01_processed_raw.fif", overwrite=True, fmt="single")
# saved is a list of one or more FIF paths when splitting is needed
```

Use `raw.save()` when you need to preserve MNE metadata, annotations, projections, and reload later with `mne.io.read_raw_fif()`.

External export:

```python
raw.export("subject01.vhdr", fmt="brainvision", overwrite=True)
raw.export("subject01.edf", fmt="edf", overwrite=True)
raw.export("subject01.set", fmt="eeglab", overwrite=True)
```

Use `raw.export()` only when the required exporter dependency is installed and when the external format can represent the needed channel types, annotations, precision, and record lengths. For simple numerical interchange, extract arrays or a DataFrame instead:

```python
np.save("data.npy", raw.get_data(picks="eeg"))
df = raw.to_data_frame(picks="eeg", start=0, stop=1000)
df.to_csv("data.csv")
```

## Read or write only Info

Use Info-only FIF files when metadata must be stored separately:

```python
info = mne.create_info(["EEG Fz", "EEG Cz"], sfreq=250.0, ch_types="eeg")
info.save("subject-info.fif", overwrite=True)
info2 = mne.io.read_info("subject-info.fif")
```

Prefer saving full Raw objects when metadata and samples must stay synchronized.
