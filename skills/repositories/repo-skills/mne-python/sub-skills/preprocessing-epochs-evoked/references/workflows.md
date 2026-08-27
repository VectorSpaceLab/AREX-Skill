# Workflows: events, preprocessing, Epochs, Evoked, covariance, and rank

Use these recipes to design MNE-Python preprocessing pipelines without relying
on repository examples at runtime. Load [api-reference.md](api-reference.md)
for exact signatures and parameter details.

## 1. Choose the event source

### Stim-channel events

Use stim-channel extraction when the raw object contains digital trigger
channels and the user asks for experimental event codes.

```python
events = mne.find_events(
    raw,
    stim_channel="STI 014",      # or None to use config/default stim channel
    output="onset",
    consecutive="increasing",
    shortest_event=2,
)
event_id = {"auditory/left": 1, "visual/right": 4}
```

Decision checks:

- Confirm the stim channel exists and is type `stim`; if it does not exist but
  annotations exist, switch to `events_from_annotations`.
- Use `consecutive=False` when events must return to zero between triggers.
  Use `consecutive=True` or `'increasing'` when adjacent nonzero codes encode
  meaningful transitions.
- Use `mask`/`mask_type` for bit-packed triggers.
- Preserve sample timing around resampling: call `Raw.resample(..., events=events)`
  when resampling after event detection, or recompute events afterward.

### Annotation-derived events

Use annotations when the reader produced descriptions instead of stim codes, or
when the task names conditions by annotation labels.

```python
events, event_id = mne.events_from_annotations(
    raw,
    event_id={"Stimulus/S 1": 1, "Stimulus/S 2": 2},
    regexp=r"^(?![Bb][Aa][Dd]|[Ee][Dd][Gg][Ee]).*$",
)
```

Decision checks:

- The default regular expression excludes `BAD*` and `EDGE*` annotations. This
  is usually correct because bad spans should drop epochs, not become
  conditions.
- For string-coded numeric annotations, `event_id=int` maps `'1'` to `1`, etc.
- For long blocks, use `chunk_duration` only when each fixed segment should be
  an event; document that annotations shorter than the chunk do not contribute.
- If `events_from_annotations` returns no events, inspect the annotation
  descriptions and the `regexp` before changing downstream Epochs settings.

### Fixed-length windows

Use fixed-length events for resting-state, sliding-window covariance/PSD, or
artifact scans where no experimental event exists.

```python
events = mne.make_fixed_length_events(
    raw,
    id=1,
    start=0,
    stop=None,
    duration=2.0,
    overlap=0.0,
)
```

Decision checks:

- `overlap` must satisfy `0 <= overlap < duration`.
- Set `first_samp=False` when combining with zero-based synthetic events;
  otherwise keep the default so timing is consistent with `find_events`.
- The function raises if no events can fit into the requested span.

## 2. Preprocess continuous data before epoching

Preferred order for most sensor-space tasks:

1. Load or receive a `Raw` object from `io-raw-data` with the desired channels
   and metadata.
2. Preserve a copy or checkpoint before destructive operations.
3. Mark bad spans as annotations and bad channels in `raw.info['bads']`.
4. Apply channel-type corrections and montage/reference decisions.
5. Filter/notch/resample continuous data if appropriate.
6. Extract events and construct `Epochs`.
7. Reject/repair epochs and average to `Evoked`.

Canonical pattern:

```python
raw_clean = raw.copy()
raw_clean.info["bads"].extend(["EEG 053"])
raw_clean.filter(l_freq=0.1, h_freq=40.0, picks="data")
raw_clean.notch_filter(freqs=[50, 100], picks="data")

events = mne.find_events(raw_clean, stim_channel="STI 014")
epochs = mne.Epochs(
    raw_clean,
    events,
    event_id={"condition/a": 1, "condition/b": 2},
    tmin=-0.2,
    tmax=0.5,
    baseline=(None, 0),
    reject={"eeg": 150e-6},
    flat={"eeg": 1e-6},
    reject_by_annotation=True,
    preload=True,
)
```

Filtering and resampling choices:

- Filter raw before epochs when possible; filtering individual short epochs can
  produce edge artifacts and filter-length warnings.
- Use high-pass filtering before ICA fitting, commonly around 1 Hz; the ICA fit
  raw can be a copy even if the final data use a lower high-pass.
- `Raw.filter` skips annotations named `edge` and `bad_acq_skip` by default,
  not every `BAD*` label. For bad-span exclusion, rely on
  `reject_by_annotation` or explicit data extraction settings.
- Resampling applies anti-aliasing. If precise event timing is critical, prefer
  finding events after final resampling or pass events into `Raw.resample`.

## 3. Construct Epochs deliberately

```python
epochs = mne.Epochs(
    raw,
    events,
    event_id,
    tmin=-0.2,
    tmax=0.8,
    baseline=(None, 0),
    picks="data",
    preload=True,
    reject={"eeg": 150e-6, "eog": 250e-6},
    flat={"eeg": 1e-6},
    reject_tmin=0.0,
    reject_tmax=0.6,
    detrend=None,
    decim=1,
    proj=True,
    on_missing="warn",
    reject_by_annotation=True,
    event_repeated="merge",
)
```

Decision table:

| Situation | Use | Check |
| --- | --- | --- |
| Baseline correction desired | `baseline=(None, 0)` or a task-specific interval | Baseline interval must lie inside `[tmin, tmax]`; cannot always be removed after application. |
| High-amplitude artifacts | `reject={ch_type: threshold}` | Thresholds use SI units and peak-to-peak within each epoch. |
| Flat or disconnected channels | `flat={ch_type: threshold}` or `annotate_amplitude` before epochs | Flat thresholds are minimum peak-to-peak values. |
| Bad spans should remove epochs | `reject_by_annotation=True` | Only annotations beginning `BAD`/`bad` are auto-rejecting. |
| Duplicate event samples | `event_repeated='drop'` or `'merge'` | `'merge'` creates a combined event key; `'drop'` keeps the first event. |
| Some event IDs absent | `on_missing='warn'` or `'ignore'` | Use only when absent conditions are acceptable. |
| Events outside raw bounds | `on_outside='warn'|'raise'|'ignore'` | Prefer `raise` when events are expected to be fully valid. |
| Lower sample count | `decim` at construction or `.resample()` | Decimation can alias; resampling filters. |
| Delayed projector decision | `proj='delayed'` | Useful for rejection before final SSP application. |

After construction:

```python
len(epochs)                 # accepted epochs
epochs.drop_log             # why each original event was dropped
epochs.selection            # indices of kept original events
epochs.event_id             # possibly changed by merged duplicates
epochs.get_data(copy=True)  # shape (n_epochs, n_channels, n_times)
```

## 4. Synthetic EpochsArray and EvokedArray

Use array constructors when no raw object exists and the user already has
well-defined NumPy arrays.

```python
info = mne.create_info(["Cz", "Pz"], sfreq=250.0, ch_types="eeg")
events = np.array([[0, 0, 1], [250, 0, 2]], dtype=int)
data = np.zeros((2, 2, 126))  # n_epochs, n_channels, n_times
epochs = mne.EpochsArray(data, info, events=events, tmin=-0.1,
                         event_id={"a": 1, "b": 2}, baseline=None)
```

Array rules:

- `EpochsArray`: data shape is `(n_epochs, n_channels, n_times)`.
- `EvokedArray`: data shape is `(n_channels, n_times)`.
- Channel units must match the `Info` channel types: EEG/EOG/ECG in volts,
  magnetometers in tesla, gradiometers in tesla/meter, fNIRS hemoglobin in
  molar concentration, and misc in arbitrary units.
- `EpochsArray` does not preserve annotations; if annotation behavior matters,
  build a `RawArray`, set annotations, then call `Epochs`.

## 5. Average, combine, and save Evoked responses

```python
evoked_a = epochs["condition/a"].average(picks="data")
evoked_b = epochs["condition/b"].average(picks="data")
contrast = mne.combine_evoked([evoked_a, evoked_b], weights=[1, -1])
contrast.apply_baseline((None, 0))
contrast.save("subject-aud-vis-ave.fif", overwrite=True)
```

Decision checks:

- `evoked.nave` should match the number of averaged epochs. Use it to sanity
  check rejected trials and condition indexing.
- Use `epochs.average(by_event_type=True)` when a separate evoked response is
  needed for each event type.
- Use `combine_evoked(..., weights='nave')` for weighted group/condition
  averages by trial count, `weights='equal'` for equal instance weights, and
  numeric weights for explicit contrasts.
- When combining evokeds, channels and times must match. Bad channels are
  unioned into the output.
- Route plotting (`plot`, `plot_topomap`, reports) to `visualization-reporting`.

## 6. Compute covariance and rank after preprocessing

Noise covariance and rank depend on projectors, reference, interpolation,
filtering, and channel selection.

```python
rank = mne.compute_rank(epochs, rank=None, proj=True)
noise_cov = mne.compute_covariance(
    epochs,
    tmax=0,
    method="empirical",
    rank=rank,
    on_few_samples="warn",
)
```

Decision checks:

- Use a pre-stimulus window (`tmax=0`) when the covariance should model noise
  rather than evoked response.
- If data were average-referenced, interpolated, SSS/tSSS processed, or had
  projectors applied, do not assume full channel rank. Compute or pass rank.
- For tiny synthetic examples, `on_few_samples='ignore'` can keep smoke tests
  quiet; for real analysis, warn the user that estimates may be unstable.
- Route forward/inverse use of covariance to `source-modeling-inverse` after
  this sub-skill has prepared valid evoked/covariance/rank objects.

## 7. fNIRS preprocessing into epochs/evokeds

Typical fNIRS flow after raw loading:

```python
from mne.preprocessing import nirs

raw_od = nirs.optical_density(raw.copy())
sci = nirs.scalp_coupling_index(raw_od)
raw_od.info["bads"].extend([
    ch for ch, score in zip(raw_od.ch_names, sci) if score < 0.5
])
raw_haemo = nirs.beer_lambert_law(raw_od, ppf=6.0)
raw_haemo.filter(0.05, 0.7, h_trans_bandwidth=0.2,
                 l_trans_bandwidth=0.02)
events, event_id = mne.events_from_annotations(raw_haemo)
epochs = mne.Epochs(raw_haemo, events, event_id, tmin=-5, tmax=15,
                    baseline=(-5, 0), reject_by_annotation=True,
                    preload=True)
```

Decision checks:

- Exclude short source-detector channels when they are not meant to capture
  neural responses: `nirs.short_channels(info, threshold=0.01)`.
- Scalp coupling index is a quality-control metric, not an automatic mutation;
  add bad channels deliberately.
- `temporal_derivative_distribution_repair`/`tddr` can repair motion artifacts
  on optical-density data; document when it is used.
- fNIRS responses are slower than EEG/MEG; epoch windows and baselines are
  usually seconds long, not hundreds of milliseconds.

## 8. Eye-tracking blink handling before epoching

Typical flow after eye-tracking raw loading:

```python
from mne.preprocessing import eyetracking

blink_annots = eyetracking.find_blinks(
    raw_et,
    method="dropout",
    dropout_value=0,
    description="BAD_blink",
)
raw_et.set_annotations(raw_et.annotations + blink_annots)
eyetracking.interpolate_blinks(
    raw_et,
    buffer=(0.05, 0.2),
    match="BAD_blink",
    interpolate_gaze=True,
)
events = mne.find_events(raw_et, stim_channel="DIN")
```

Decision checks:

- Eye-tracking readers and calibration-file loading route to `io-raw-data`; this
  workflow starts once a valid MNE eye-tracking raw object exists.
- Pupil dropouts can be interpolated; gaze interpolation during blinks is less
  reliable because eyes may move while closed. Use `interpolate_gaze=True` only
  when appropriate for the analysis.
- If calibration metadata is available, `convert_units` can convert gaze to
  radians; provide screen geometry via a `Calibration` object.
- If eye-tracking and EEG systems share a photodiode/stim channel, extract
  common events from that channel and preserve timing across both raws.

## 9. Common end-to-end recipe

```python
# Raw loading is owned by io-raw-data.
raw = raw.copy().load_data()
raw.info["bads"].extend(user_bad_channels)
raw.set_eeg_reference("average", projection=True)
raw.filter(0.1, 40.0, picks="data")

events, event_id = mne.events_from_annotations(raw)
# or: events = mne.find_events(raw, stim_channel="STI 014")

epochs = mne.Epochs(
    raw, events, event_id,
    tmin=-0.2, tmax=0.5,
    baseline=(None, 0),
    reject=reject,
    flat=flat,
    reject_by_annotation=True,
    event_repeated="merge",
    preload=True,
)

epochs.drop_bad()
evoked = epochs.average()
rank = mne.compute_rank(epochs)
noise_cov = mne.compute_covariance(epochs, tmax=0, rank=rank)
```

Sanity checks before returning results:

- Event counts per condition match expectations.
- `epochs.drop_log` explains rejected trials.
- `epochs.baseline`, `epochs.info['bads']`, projector state, and channel picks
  match the stated analysis plan.
- `evoked.nave` is nonzero and plausible.
- Rank and covariance were computed after the same projector/reference/channel
  decisions that will be used downstream.
