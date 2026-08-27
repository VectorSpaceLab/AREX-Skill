# Troubleshooting preprocessing, Epochs, and Evoked workflows

Use this file when a pipeline fails, drops unexpected trials, returns empty
objects, warns about rank/filtering/fitting, or produces surprising Evoked
results. See [api-reference.md](api-reference.md) for exact signatures and
[workflows.md](workflows.md) for recipes.

## Duplicate events at the same sample

Symptoms:

- `RuntimeError: Event time samples were not unique. Consider setting the event_repeated parameter.`
- Fewer or more epochs than expected after merging event sources.

Likely causes:

- Multiple stim channels or annotations mapped to the same sample.
- Simultaneous conditions represented as separate event rows.
- Rounding annotation onsets to sample indices produced duplicates.

Fixes:

```python
epochs = mne.Epochs(raw, events, event_id, event_repeated="merge")
# or keep first and drop duplicates:
epochs = mne.Epochs(raw, events, event_id, event_repeated="drop")
```

Guidance:

- Use `'merge'` when simultaneous events are meaningful. MNE creates a combined
  key such as `aud/vis` and a new event code.
- Use `'drop'` only when the first event row is known to be the desired event.
- Use `events_from_annotations(..., use_rounding=True)` to reduce duplicate
  indices from floating-point annotation onsets.
- After construction, inspect `epochs.event_id`, `epochs.events`, and
  `epochs.drop_log` for `DROP DUPLICATE` or `MERGE DUPLICATE` entries.

## No stim channels found, or no events returned

Symptoms:

- `ValueError: No stim channel found to extract event triggers.`
- Error suggesting `mne.events_from_annotations`.
- `events_from_annotations` returns an empty `(0, 3)` event array.

Fixes:

```python
# Stim-channel route:
events = mne.find_events(raw, stim_channel="STI 014", initial_event=True)

# Annotation route:
events, event_id = mne.events_from_annotations(raw, regexp=None)
```

Guidance:

- If the data have annotations but no stim channel, use
  `events_from_annotations`.
- If annotations exist but no events are returned, list annotation descriptions
  and check the default regexp. Descriptions beginning `bad` or `edge` are
  ignored by default.
- For long block annotations, set `chunk_duration` if fixed events within a
  block are desired.
- For first-sample triggers, use `initial_event=True` with `find_events`.

## BAD annotations drop too many or too few epochs

Symptoms:

- Many epochs dropped with `BAD_*` reasons.
- Contaminated trials remain despite annotations.
- Filtering seems to include bad spans unexpectedly.

Fixes:

```python
epochs = mne.Epochs(raw, events, event_id,
                    reject_by_annotation=True,
                    reject_tmin=0.0, reject_tmax=0.5)
```

Guidance:

- `Epochs(..., reject_by_annotation=True)` drops epochs that overlap `BAD*` or
  `bad*` annotations in the rejection window.
- Use `reject_tmin`/`reject_tmax` to restrict the bad-span/rejection check to
  the time range relevant for analysis.
- `Raw.filter` does not skip all `BAD*` spans by default; its
  `skip_by_annotation` default is `('edge', 'bad_acq_skip')`.
- If you want bad annotations to become event labels, override the default
  `events_from_annotations` regexp explicitly and document the intent.

## Epoch shape, event_id, or channel mismatch

Symptoms:

- `ValueError: Data must be a 3D array...` for `EpochsArray`.
- `Info and data must have same number of channels.`
- `No matching events found for ...`.
- `The events must only contain event numbers from event_id`.

Fixes:

```python
# EpochsArray shape: n_epochs, n_channels, n_times
data = data.reshape(n_epochs, n_channels, n_times)
assert data.shape[1] == len(info["ch_names"])

# Keep event IDs synchronized with events[:, 2]
event_codes = set(events[:, 2])
event_id = {name: code for name, code in event_id.items() if code in event_codes}
epochs = mne.Epochs(raw, events, event_id, on_missing="warn")
```

Guidance:

- `EpochsArray` is 3D; `EvokedArray` is 2D.
- Event IDs map names to integers in the third event column.
- Use `on_missing='warn'` or `'ignore'` only if absent conditions are acceptable.
- Channel units must match `Info` channel types. EEG/EOG/ECG are volts, MEG
  magnetometers are tesla, gradiometers are tesla/meter.

## Baseline errors and irreversible baseline state

Symptoms:

- Baseline interval is outside epoch/evoked time range.
- Error when trying to remove baseline correction after applying it.
- ICA warns about baseline-corrected epochs.

Fixes:

```python
# Choose a valid interval inside [tmin, tmax]
epochs = mne.Epochs(raw, events, event_id, tmin=-0.2, tmax=0.5,
                    baseline=(None, 0))

# For ICA, fit on unbaselined high-pass data
ica_epochs = mne.Epochs(raw_for_ica, events, event_id, baseline=None,
                        preload=True)
```

Guidance:

- `Epochs` default baseline is `(None, 0)`; `EpochsArray` and `EvokedArray`
  default to no baseline.
- A baseline tuple must lie within the object time span and have start <= stop.
- Once baseline has been applied to preloaded epochs/evoked data, MNE generally
  cannot restore the original unbaselined data.
- ICA can introduce a DC shift; use `ICA.apply(..., on_baseline='reapply')` or
  reapply baseline after ICA if the input was baseline-corrected.

## Rejection and flat thresholds behave unexpectedly

Symptoms:

- All epochs dropped.
- No epochs dropped despite visible artifacts.
- Flat channels are not caught, or too many channels become bad.

Fixes:

```python
reject = {"eeg": 150e-6, "eog": 250e-6}
flat = {"eeg": 1e-6}
epochs = mne.Epochs(raw, events, event_id, reject=reject, flat=flat,
                    reject_tmin=0, reject_tmax=0.5, preload=True)
print(epochs.drop_log)
```

Guidance:

- `reject` and `flat` thresholds are peak-to-peak values in SI units per
  channel type.
- Use `reject_tmin`/`reject_tmax` to avoid rejecting trials for artifacts
  outside the analysis window.
- `drop_bad(reject='existing', flat='existing')` reuses constructor thresholds;
  pass dictionaries to override.
- `annotate_amplitude` has different logic: it detects consecutive-sample
  jumps or flats, returns annotations and bad-channel suggestions, and does not
  mutate raw automatically.

## Filtering and resampling warnings

Symptoms:

- Warning that filter length is longer than the signal.
- High-pass/low-pass frequency errors near Nyquist.
- Event timing shifts after downsampling.
- `Raw.resample` returns a tuple instead of just raw.

Fixes:

```python
# Prefer filtering continuous raw data before epoching
raw_filt = raw.copy().filter(0.1, 40.0, picks="data")

# Preserve event timing during raw resampling
raw_rs, events_rs = raw.copy().resample(200, events=events)
```

Guidance:

- Short epochs are prone to edge artifacts and filter-length warnings; filter
  raw when possible.
- Resampling applies anti-alias filtering. Do not reuse old sample indices
  blindly after resampling.
- Keep filter cutoffs below Nyquist (`sfreq / 2`) and choose transition bands
  that fit the data length.
- Notch filtering requires a known line frequency; automatic spectrum-fit notch
  behavior is not always reliable, so explicit frequencies are preferred.

## Optional dependencies for ICA and related methods

Symptoms:

- Import or runtime error for scikit-learn, Picard, or plotting dependencies.
- `FastICA did not converge` warnings.

Fixes:

```python
# Avoid Picard if it is not installed
ica = mne.preprocessing.ICA(method="infomax", random_state=97,
                            max_iter="auto")

# Or keep FastICA but increase robustness
ica = mne.preprocessing.ICA(method="fastica", random_state=97,
                            max_iter=1000, n_components=0.99)
```

Guidance:

- `method='fastica'` requires scikit-learn; `method='picard'` requires Picard;
  `method='infomax'` uses MNE-Python's implementation.
- Convergence often improves with high-pass filtering, fewer/noisy-channel
  exclusions, deterministic `random_state`, sensible `n_components`, and more
  iterations.
- If fitting on too few samples or baseline-corrected epochs, change the fit
  data rather than suppressing warnings.
- Avoid plotting-dependent ICA diagnostics in headless settings; ask
  `visualization-reporting` for `show=False` or backend-safe plans.

## ICA application fails after picking or channel changes

Symptoms:

- `Epochs don't match fitted data` or `Evoked does not match fitted data`.
- ICA apply fails after dropping/reordering channels.
- Unexpected DC offset after cleaning.

Fixes:

```python
raw_fit = raw.copy().filter(1.0, None, picks="data")
ica.fit(raw_fit)
raw_clean = raw.copy()              # same channel set/order as fit data
ica.apply(raw_clean, on_baseline="warn")
```

Guidance:

- The object passed to `ICA.apply` must contain the channels used during
  fitting, in compatible order.
- Do channel dropping/reordering either before both fit and apply, or after
  cleaning.
- If applying to baseline-corrected Epochs/Evoked, reapply baseline after
  cleaning or use `on_baseline='reapply'`.

## SSP projectors appear to have no effect

Symptoms:

- Projectors are present in `info['projs']` but data look unchanged.
- Rank seems unchanged before applying projectors.

Fixes:

```python
projs, events = mne.preprocessing.compute_proj_eog(raw)
raw.add_proj(projs)
raw.apply_proj()  # actually modifies data and activates projectors
```

Guidance:

- Projectors are inactive until applied, unless a method temporarily applies
  them via `proj=True`, `proj='delayed'`, or interactive projection settings.
- `no_proj=True` in projector computation excludes existing projectors.
- After applying projectors, recompute rank and covariance assumptions.

## EOG/ECG event detection returns no or implausible events

Symptoms:

- No EOG events detected.
- No ECG events detected or implausible heart rate.
- Helper asks for an EOG/ECG channel.

Fixes:

```python
eog_events = mne.preprocessing.find_eog_events(raw, ch_name="EOG 061",
                                               thresh=None)
ecg_events, ch_ecg, pulse = mne.preprocessing.find_ecg_events(
    raw, ch_name="ECG 001", qrs_threshold="auto")
```

Guidance:

- Provide explicit `ch_name` when automatic channel-type detection fails.
- EOG `thresh` controls blink peak detection; higher values detect fewer
  events.
- ECG synthesis only works from suitable MEG channels when no ECG channel is
  available.
- Rejection by annotation can omit long segments during detection; inspect bad
  annotations if too few events are found.

## fNIRS problems

Symptoms:

- Scalp coupling values are poor or all channels marked bad.
- Beer-Lambert conversion fails or produces unexpected units.
- Epoch windows seem too short or baseline is invalid.

Guidance:

- Confirm raw fNIRS channel metadata and source-detector distances before
  preprocessing. File-reader setup belongs to `io-raw-data`.
- Use optical density before Beer-Lambert conversion.
- Treat scalp coupling as a QC metric; choose and document the bad-channel
  threshold.
- fNIRS epoch windows are usually seconds long. Check the baseline interval
  against the chosen `tmin`/`tmax`.

## Eye-tracking blink or unit problems

Symptoms:

- Blink annotations are missing.
- Interpolation does not affect expected blink spans.
- Gaze units are pixels when radians are expected.

Guidance:

- `find_blinks` returns annotations; attach them with `set_annotations`.
- `interpolate_blinks` matches annotation descriptions such as `BAD_blink` and
  mutates raw.
- Pupil dropouts can be `0` for EyeLink-style data or `NaN` for other systems;
  set `dropout_value` accordingly.
- Use `convert_units` with a valid calibration object and screen geometry for
  visual-angle conversion.

## Covariance and rank warnings

Symptoms:

- Few-sample warning from `compute_covariance` or `compute_rank`.
- Rank mismatch after interpolation, average reference, SSS, or projections.
- Downstream inverse/whitening looks unstable.

Fixes:

```python
rank = mne.compute_rank(epochs, proj=True)
noise_cov = mne.compute_covariance(epochs, tmax=0, rank=rank,
                                   on_few_samples="warn")
```

Guidance:

- Few-sample warnings are meaningful for real analyses. Suppress only in small
  synthetic smoke tests.
- Recompute rank after changing projectors, bad channels, interpolation,
  reference, or channel picks.
- Use the same channel set and projector state for covariance as for the
  evoked/inverse workflow.

## Empty or surprising Evoked outputs

Symptoms:

- `evoked.nave == 0` or condition average is missing.
- EOG/ECG/stim channels disappeared after averaging.
- `combine_evoked` fails due to channel/time mismatch.

Fixes:

```python
assert len(epochs["condition/a"]) > 0
evoked = epochs["condition/a"].average(picks="all")
# Align channels before combining
mne.channels.equalize_channels([evoked_a, evoked_b])
contrast = mne.combine_evoked([evoked_a, evoked_b], weights=[1, -1])
```

Guidance:

- Check event IDs, `epochs.selection`, and `drop_log` before averaging.
- `epochs.average()` keeps data channels by default. Use `picks='all'` only
  when non-data channels are intentionally needed.
- `combine_evoked` requires matching channels and times; crop, pick, reorder,
  or equalize channels deliberately before combining.
- Numeric weights can make `nave` assumptions unsuitable for later inverse
  scaling; document contrasts.
