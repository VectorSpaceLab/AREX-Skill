# Dataset and window API reference

## Local construction

`create_from_X_y(X, y, drop_last_window, sfreq, ch_names=None,
window_size_samples=None, window_stride_samples=None)` creates a
`BaseConcatDataset`. `X` is normally `(n_trials, n_channels, n_times)`;
`y` must align with trials. If a trial is shorter than a requested window,
choose `drop_last_window` deliberately and check the resulting length.

Use `create_from_mne_raw` for continuous local `mne.io.Raw` objects and
`create_from_mne_epochs` for already segmented `mne.Epochs`. These preserve MNE
information better than manually converting through NumPy.

## Dataset layers

- `BaseDataset` wraps one recording and exposes `raw`/`epochs`, a description,
  and a target-selection policy.
- `WindowsDataset` represents epoch-like windows; `EEGWindowsDataset` keeps
  continuous raw data plus window metadata; `RawDataset` represents continuous
  data without window metadata.
- `BaseConcatDataset` combines datasets and exposes descriptions, filtering,
  splitting, and serialization-related operations.

Inspect `dataset[0]` rather than assuming every dataset returns the same tuple:
windowed datasets may return `(X, y, crop_inds)` or an equivalent metadata-aware
form depending on construction options.

## Window entry points

- `create_fixed_length_windows` slices recordings at a fixed duration/stride.
- `create_windows_from_events` uses MNE event IDs, offsets, `window_size_samples`,
  and `window_stride_samples`.
- `create_windows_from_target_channels` reads time-series targets stored as raw
  channels and returns aligned signal/target windows.

Window sizes are in samples at the data's current sampling frequency. Convert
seconds explicitly with `round(seconds * sfreq)` and validate the resulting
integer. Do not reuse a window size after resampling without recalculation.
