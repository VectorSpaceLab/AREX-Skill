# IO / Raw Troubleshooting

## `Unsupported file type (...)`

Likely causes:

- The suffix is not in MNE-Python's raw reader dispatch table.
- The path is a marker/sidecar file rather than the raw header/data file.
- The file has an extra suffix after a supported suffix, such as `raw.fif.tmp`.

Recovery:

1. Check the true file family and extension.
2. For BrainVision, pass `.vhdr` or `.ahdr`, not `.vmrk` or `.amrk`.
3. For unknown or proprietary files, use a dedicated converter outside MNE or create a `RawArray` after parsing the data yourself.
4. If the format is supported but suffix dispatch failed, call the dedicated `mne.io.read_raw_*` reader directly.

## `Could not read file using any of the possible readers`

Likely causes:

- Ambiguous suffix with multiple possible reader families (`.cnt`, `.bin`, `.dat`).
- Sidecar/header files are missing or inconsistent.
- Generic dispatch hid the real exception from a specific reader.

Recovery:

```python
# Instead of mne.io.read_raw("file.cnt"), choose the known family:
raw = mne.io.read_raw_cnt("file.cnt", preload=False)
# or
raw = mne.io.read_raw_ant("file.cnt", preload=False)
```

Then pass format-specific keyword arguments for channel types, encodings, headers, triggers, or sidecars.

## Missing optional reader or exporter package

Symptoms include `ImportError`, `ModuleNotFoundError`, or a message naming a package such as `h5py`, `neo`, `curryreader`, `pybv`, `edfio`, or `eeglabio`.

Recovery:

- Confirm whether the missing package is needed for the requested file format or only for optional export.
- If it is needed, install the smallest relevant optional package in the user's environment, then retry the same dedicated reader/exporter.
- If installation is not allowed, route to a supported format path: ask for FIF/EDF/BrainVision data already converted, or construct `RawArray` from arrays plus metadata.

## Preload and memmap problems

Symptoms:

- Operation says data must be preloaded.
- Memory error after `preload=True`.
- Filtering or direct data assignment fails on a lazily loaded raw object.
- Memmap file cannot be created or is unexpectedly slow.

Recovery:

```python
# Prefer reduce-then-load for large files.
raw = mne.io.read_raw_fif("large_raw.fif", preload=False)
work = raw.copy().crop(0, 120).pick(["eeg", "eog"])
work.load_data()

# Or use a writable memory map.
work = raw.copy().crop(0, 120)
work.load_data(memmap="work_raw.dat")
```

Notes:

- `preload=True` means RAM; `preload="path.dat"` and `load_data(memmap="path.dat")` mean memmap.
- Use `get_data(picks=..., start=..., stop=...)` for read-only slices.
- Avoid preloading a full high-density recording before picking/cropping if the task only needs a subset.

## RawArray shape, dtype, and unit errors

Symptoms:

- `ValueError: Data must be a 2D array of shape (n_channels, n_samples)`.
- `len(data) does not match len(info["ch_names"])`.
- Signals appear 1e6 too large/small.
- Copy errors with `float32` data and restrictive `copy` settings.

Recovery:

```python
# If original is (n_times, n_channels), transpose it.
data = data.T

# Convert common EEG microvolts to volts.
data_volts = data_microvolts * 1e-6

info = mne.create_info(ch_names, sfreq, ch_types)
raw = mne.io.RawArray(data_volts, info, copy="auto")
assert raw.get_data().shape[0] == len(raw.ch_names)
```

Use `copy="auto"` unless the task requires memory aliasing. `RawArray` converts non-complex data to `float64` and complex data to `complex128`.

## Bad, duplicate, or long channel names

Symptoms:

- Channel picks return empty results.
- FIF save/reload changes names or warns about names.
- Duplicate names gain suffixes.
- Expected EOG/stim channels are treated as misc/EEG.

Recovery:

```python
print(raw.ch_names)
print(raw.get_channel_types())
raw = raw.copy()
raw.rename_channels({"old name": "new_name"}, on_missing="ignore")
raw.set_channel_types({"VEOG": "eog", "STI 014": "stim"}, on_unit_change="warn")
raw.info["bads"] = [name for name in raw.info["bads"] if name in raw.ch_names]
```

When saving FIF, keep important names concise and unique. Use reader options (`eog`, `misc`, `ecg`, `emg`, `stim_channel`, `infer_types`) at read time when the format can classify channels.

## Concatenation mismatch

Symptoms:

- `Info` mismatch errors.
- Channel order differs across runs.
- Boundary annotations reject data unexpectedly later.
- Saved concatenated files behave oddly in external tools.

Recovery:

```python
raws = mne.io.match_channel_orders(raws, copy=True)
combined = mne.io.concatenate_raws(raws, preload=None, on_mismatch="raise")
print(combined.annotations)
```

- Align channel names, order, types, bads, projectors, and sampling frequency before concatenation.
- Expect `BAD boundary` and `EDGE boundary` annotations at joins. Delete only with an explicit reason.
- Remember that saving a concatenated raw stores measurement info from the first raw.

## Annotation surprises

Symptoms:

- New annotations replaced existing interactive annotations.
- Annotation onsets shift after setting them on raw.
- Downstream epoching/filtering skips segments unexpectedly.
- Annotation outside data range is missing.

Recovery:

```python
old = raw.annotations.copy()
new = mne.Annotations([1.0], [0.2], ["BAD_motion"])
raw = raw.copy().set_annotations(old + new)
```

- `set_annotations` replaces; add to existing annotations explicitly.
- `orig_time` and nonzero `raw.first_samp` affect stored onsets.
- `BAD*` descriptions are intentionally used for rejection by later processing.
- Check `raw.annotations.onset`, `duration`, and `description` after setting.

## Save/export errors

Symptoms:

- FIF save rejects filename.
- Export says dependency missing.
- EDF export complains about record lengths or physical ranges.
- Exported format loses metadata.

Recovery:

- For MNE-native preservation, use `raw.save("name_raw.fif", overwrite=True, fmt="single")`.
- FIF raw filenames should end with accepted raw endings such as `raw.fif`, `raw_sss.fif`, `_meg.fif`, `_eeg.fif`, or `_ieeg.fif` (optionally `.gz`).
- For external export, install the specific exporter dependency and check channel types/physical ranges.
- If metadata fidelity matters more than interchange, save FIF instead of exporting.
