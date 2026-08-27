# API reference: preprocessing, Epochs, and Evoked

This reference distills MNE-Python source and installed API signatures for the
sensor-space preprocessing surface. Source evidence paths are provenance only;
runtime use does not require opening them.

## Events and annotations

Event arrays are integer arrays of shape `(n_events, 3)`: sample index, value
before the event, and event code. Sample indices usually include
`raw.first_samp`, which matters when combining events with cropped or
concatenated raw data.

Verified signatures:

```python
mne.Annotations(onset, duration, description, orig_time=None, ch_names=None, *, extras=None)
mne.find_events(raw, stim_channel=None, output='onset', consecutive='increasing', min_duration=0, shortest_event=2, mask=None, uint_cast=False, mask_type='and', initial_event=False, verbose=None)
mne.events_from_annotations(raw, event_id='auto', regexp='^(?![Bb][Aa][Dd]|[Ee][Dd][Gg][Ee]).*$', use_rounding=True, chunk_duration=None, tol=1e-08, verbose=None)
mne.make_fixed_length_events(raw, id=1, start=0, stop=None, duration=1.0, first_samp=True, overlap=0.0)
mne.pick_events(events, include=None, exclude=None, step=False)
mne.merge_events(events, ids, new_id, replace_events=True)
mne.concatenate_events(events, first_samps, last_samps)
mne.read_events(filename, include=None, exclude=None, mask=None, mask_type='and', return_event_id=False, verbose=None)
mne.write_events(filename, events, *, overwrite=False, verbose=None)
```

Key parameter notes:

- `find_events` reads a stim channel; when `stim_channel=None` it consults
  MNE stim-channel configuration, then `'STI 014'`, then the first `stim`
  channel. If no stim channel exists but annotations exist, it raises with a
  hint to use `events_from_annotations`.
- `output='onset'|'offset'|'step'` controls which transitions are returned.
  `consecutive='increasing'` returns adjacent nonzero events only when the new
  value is larger; `True` returns every change; `False` requires a return to
  zero.
- `min_duration` is seconds; `shortest_event` is samples and raises for
  suspiciously short events. Use `min_duration` instead of lowering
  `shortest_event` unless a one-sample trigger is known to be valid.
- `mask` and `mask_type='and'|'not_and'` operate on digital trigger bits.
  `uint_cast=True` is a Neuromag STI channel workaround for negative values.
- `initial_event=True` emits an event if the first stim sample is already
  nonzero.
- `events_from_annotations` default `regexp` ignores descriptions beginning
  with `bad` or `edge` (case-insensitive). Pass `regexp=None` or a custom
  regular expression only when those annotations should become events.
- `event_id` for annotations can be a dict, callable, `None`, or `'auto'`.
  `'auto'` uses format-specific behavior when available; otherwise it maps
  descriptions like `None` (sorted unique integer values).
- `chunk_duration` converts one long annotation into repeated equally spaced
  events; annotations shorter than `chunk_duration` do not contribute events.
- `make_fixed_length_events(..., overlap=...)` requires
  `0 <= overlap < duration`; `first_samp=False` is useful when returned events
  must be combined with zero-based synthetic/sample arrays.

## Epochs and EpochsArray

Verified signatures:

```python
mne.Epochs(raw, events=None, event_id=None, tmin=-0.2, tmax=0.5, baseline=(None, 0), picks=None, preload=False, reject=None, flat=None, proj=True, decim=1, reject_tmin=None, reject_tmax=None, detrend=None, on_missing='raise', reject_by_annotation=True, metadata=None, event_repeated='error', *, on_outside='warn', verbose=None)
mne.EpochsArray(data, info, events=None, tmin=0.0, event_id=None, reject=None, flat=None, reject_tmin=None, reject_tmax=None, baseline=None, proj=True, on_missing='raise', metadata=None, selection=None, *, on_outside='warn', drop_log=None, raw_sfreq=None, verbose=None)
```

Core methods used in preprocessing pipelines:

```python
Epochs.filter(self, l_freq, h_freq, picks=None, filter_length='auto', l_trans_bandwidth='auto', h_trans_bandwidth='auto', n_jobs=None, method='fir', iir_params=None, phase='zero', fir_window='hamming', fir_design='firwin', skip_by_annotation=('edge', 'bad_acq_skip'), pad='edge', *, verbose=None)
Epochs.resample(self, sfreq, *, npad='auto', window='auto', n_jobs=None, pad='edge', method='fft', verbose=None)
Epochs.drop_bad(self, reject='existing', flat='existing', verbose=None)
Epochs.drop(self, indices, reason='USER', verbose=None)
Epochs.average(self, picks=None, method='mean', by_event_type=False)
Epochs.apply_baseline(self, baseline=(None, 0), *, verbose=None)
Epochs.decimate(self, decim, offset=0, *, verbose=None)
Epochs.get_data(self, picks=None, item=None, units=None, tmin=None, tmax=None, *, copy=True, verbose=None)
Epochs.save(self, fname, split_size='2GB', fmt='single', overwrite=False, split_naming='neuromag', verbose=None)
```

Key object and parameter notes:

- `Epochs` requires a `Raw` instance. If `events=None`, event times can be
  derived from `raw.annotations.onset`; annotation durations are ignored as
  epoch durations.
- `EpochsArray` data must be 3D `(n_epochs, n_channels, n_times)` and must
  match `len(info['ch_names'])`. If `events=None`, synthetic events are
  generated. `EpochsArray` does not set annotations; use `RawArray` then
  `Epochs` when simulated annotations must be preserved.
- Baseline defaults differ: `Epochs` defaults to `(None, 0)`, while
  `EpochsArray` defaults to `None`.
- `reject` and `flat` are peak-to-peak amplitude thresholds by channel type.
  Typical keys include `grad`, `mag`, `eeg`, `eog`, and `ecg`; values use native
  SI units such as EEG volts, magnetometer tesla, and gradiometer tesla/meter.
- `reject_tmin` and `reject_tmax` restrict the time window used for rejection
  without changing the epoch time span.
- `reject_by_annotation=True` drops epochs that overlap annotations beginning
  with `BAD`/`bad` during the rejection window.
- `event_repeated='error'|'drop'|'merge'` handles duplicate sample times.
  `'merge'` creates hierarchical names such as `aud/vis` and assigns a new
  integer event code.
- Data access applies pending detrending, baseline, decimation, and projectors;
  inspect `epochs.drop_log`, `epochs.selection`, `epochs.event_id`, and
  `epochs.events` after construction.
- Channel-picking and preprocessing methods generally operate in place. Use
  `epochs.copy()` before destructive trial or channel operations.

## Evoked and EvokedArray

Verified signatures:

```python
mne.Evoked(fname, condition=None, proj=True, kind='average', allow_maxshield=False, *, verbose=None)
mne.EvokedArray(data, info, tmin=0.0, comment='', nave=1, kind='average', baseline=None, *, verbose=None)
mne.read_evokeds(fname, condition=None, baseline=None, kind='average', proj=True, allow_maxshield=False, verbose=None)
mne.write_evokeds(fname, evoked, *, on_mismatch='raise', overwrite=False, verbose=None)
mne.combine_evoked(all_evoked, weights)
mne.grand_average(all_inst, interpolate_bads=True, drop_bads=True)
```

Core methods:

```python
Evoked.filter(self, l_freq, h_freq, picks=None, filter_length='auto', l_trans_bandwidth='auto', h_trans_bandwidth='auto', n_jobs=None, method='fir', iir_params=None, phase='zero', fir_window='hamming', fir_design='firwin', skip_by_annotation=('edge', 'bad_acq_skip'), pad='edge', *, verbose=None)
Evoked.resample(self, sfreq, *, npad='auto', window='auto', n_jobs=None, pad='edge', method='fft', verbose=None)
Evoked.apply_baseline(self, baseline=(None, 0), *, verbose=None)
Evoked.decimate(self, decim, offset=0, *, verbose=None)
Evoked.detrend(self, order=1, picks=None)
Evoked.get_data(self, picks=None, units=None, tmin=None, tmax=None)
Evoked.get_peak(self, ch_type=None, tmin=None, tmax=None, mode='abs', time_as_index=False, merge_grads=False, return_amplitude=False, *, strict=True)
Evoked.save(self, fname, *, overwrite=False, verbose=None)
```

Key object and parameter notes:

- `Evoked` data are always loaded in memory as 2D `(n_channels, n_times)`.
  Unlike `Raw` and `Epochs`, selection is done with methods or `.data`, not
  square-bracket epoch indexing.
- `epochs.average(picks=...)` drops non-data channels by default unless `picks`
  asks for them. Preserve EOG/ECG/stim channels explicitly when needed.
- `EvokedArray` data must be 2D and channel count must match `info`.
  `kind` must be `'average'` or `'standard_error'`; `nave` records the number
  of averaged epochs and affects later noise-scaling assumptions.
- `read_evokeds(..., baseline=None)` does not remove an existing baseline
  saved in the FIF file; it only avoids adding another correction.
- `combine_evoked` requires matching channels and time instants. Weights can
  be `'equal'`, `'nave'`, or numeric. Numeric weights other than simple
  addition/subtraction can make the resulting `nave` unsuitable for inverse
  noise scaling; document that choice.
- `grand_average` can interpolate or drop bad channels across instances.

## Filtering, notch filtering, resampling, references, and interpolation

Relevant instance methods exist on `Raw`, `Epochs`, and `Evoked` unless noted.
Verified method shapes:

```python
inst.filter(l_freq, h_freq, picks=None, filter_length='auto', l_trans_bandwidth='auto', h_trans_bandwidth='auto', n_jobs=None, method='fir', iir_params=None, phase='zero', fir_window='hamming', fir_design='firwin', skip_by_annotation=('edge', 'bad_acq_skip'), pad=..., verbose=None)
Raw.notch_filter(freqs, picks=None, filter_length='auto', notch_widths=None, trans_bandwidth=1.0, n_jobs=None, method='fir', iir_params=None, mt_bandwidth=None, p_value=0.05, phase='zero', fir_window='hamming', fir_design='firwin', pad='reflect_limited', skip_by_annotation=('edge', 'bad_acq_skip'), verbose=None)
Raw.resample(sfreq, *, npad='auto', window='auto', stim_picks=None, n_jobs=None, events=None, pad='auto', method='fft', verbose=None)
Epochs.resample(sfreq, *, npad='auto', window='auto', n_jobs=None, pad='edge', method='fft', verbose=None)
Evoked.resample(sfreq, *, npad='auto', window='auto', n_jobs=None, pad='edge', method='fft', verbose=None)
inst.set_eeg_reference(ref_channels='average', projection=False, ch_type='auto', forward=None, *, joint=False, verbose=None)
inst.interpolate_bads(reset_bads=True, mode='accurate', origin='auto', method=None, exclude=(), on_bad_position='warn', verbose=None)
inst.set_channel_types(mapping, *, on_unit_change='warn', verbose=None)
```

Decision notes:

- Filtering mutates the object. For raw data, filter before epoching when
  possible to avoid edge effects across every epoch; use `copy()` for
  comparison or quality control.
- Resampling includes anti-alias filtering. For raw event timing, either pass
  `events` to `Raw.resample` or recompute events afterward.
- `set_eeg_reference(ref_channels='average', projection=True)` adds an average
  reference projector instead of immediately subtracting it. Direct reference
  changes do not include channels in `info['bads']`.
- If a physical reference channel was not saved, add it before re-referencing;
  otherwise average/reference estimates can be biased.
- `interpolate_bads` requires sensor positions for most channel types. Method
  defaults are MEG `MNE`, EEG `spline`, fNIRS `nearest`; `method='nan'` fills
  with NaNs and should usually be paired with `reset_bads=False`.

## Covariance and rank

Verified signatures:

```python
mne.compute_covariance(inst=None, keep_sample_mean=True, tmin=None, tmax=None, projs=None, *, epochs=None, on_few_samples='warn', method='empirical', method_params=None, cv=3, scalings=None, n_jobs=None, return_estimators=False, on_mismatch='raise', rank=None, verbose=None)
mne.compute_rank(inst, rank=None, scalings=None, info=None, tol='auto', *, proj=True, tol_kind='absolute', on_rank_mismatch='ignore', on_few_samples=None, verbose=None)
```

Notes:

- `compute_covariance` consumes `Epochs` and should use the intended baseline or
  pre-stimulus window (`tmax=0` for many evoked workflows). Use
  `rank='info'` or an explicit rank when projectors, interpolation,
  referencing, SSS/tSSS, or dropped channels affect rank.
- `compute_rank` helps choose a rank for covariance and inverse workflows.
  `proj=True` accounts for active projectors.
- Sparse or tiny synthetic epochs can trigger few-sample warnings; for real
  analysis, do not suppress them without documenting the statistical limit.

## ICA and SSP artifact APIs

Verified signatures:

```python
mne.preprocessing.ICA(n_components=None, *, noise_cov=None, random_state=None, method='fastica', fit_params=None, max_iter='auto', allow_ref_meg=False, verbose=None)
ICA.fit(self, inst, picks=None, start=None, stop=None, decim=None, reject=None, flat=None, tstep=2.0, reject_by_annotation=True, verbose=None)
ICA.apply(self, inst, include=None, exclude=None, n_pca_components=None, start=None, stop=None, *, on_baseline='warn', verbose=None)
ICA.find_bads_eog(self, inst, ch_name=None, threshold=3.0, start=None, stop=None, l_freq=1, h_freq=10, reject_by_annotation=True, measure='zscore', verbose=None)
ICA.find_bads_ecg(self, inst, ch_name=None, threshold='auto', start=None, stop=None, l_freq=8, h_freq=16, method='ctps', reject_by_annotation=True, measure='zscore', verbose=None)
ICA.find_bads_muscle(self, inst, threshold=0.5, start=None, stop=None, l_freq=7, h_freq=45, sphere=None, verbose=None)
ICA.find_bads_ref(self, inst, ch_name=None, threshold=3.0, start=None, stop=None, l_freq=None, h_freq=None, reject_by_annotation=True, method='together', measure='zscore', verbose=None)
mne.preprocessing.corrmap(icas, template, threshold='auto', label=None, ch_type='eeg', *, sensors=True, show_names=False, contours=6, outlines='head', sphere=None, image_interp='cubic', extrapolate='auto', border='mean', cmap=None, plot=True, show=True, verbose=None)
mne.preprocessing.compute_proj_eog(raw, raw_event=None, tmin=-0.2, tmax=0.2, n_grad=2, n_mag=2, n_eeg=2, l_freq=1.0, h_freq=35.0, average=True, filter_length='10s', n_jobs=None, reject={'grad': 2e-10, 'mag': 3e-12, 'eeg': 0.0005, 'eog': inf}, flat=None, bads=(), avg_ref=False, no_proj=False, event_id=998, eog_l_freq=1, eog_h_freq=10, tstart=0.0, filter_method='fir', iir_params=None, ch_name=None, copy=True, return_drop_log=False, meg='separate', verbose=None)
mne.preprocessing.compute_proj_ecg(raw, raw_event=None, tmin=-0.2, tmax=0.4, n_grad=2, n_mag=2, n_eeg=2, l_freq=1.0, h_freq=35.0, average=True, filter_length='10s', n_jobs=None, ch_name=None, reject={'grad': 2e-10, 'mag': 3e-12, 'eeg': 5e-05, 'eog': 0.00025}, flat=None, bads=(), avg_ref=False, no_proj=False, event_id=999, ecg_l_freq=5, ecg_h_freq=35, tstart=0.0, qrs_threshold='auto', filter_method='fir', iir_params=None, copy=True, return_drop_log=False, meg='separate', verbose=None)
```

ICA notes:

- ICA should be fit on high-pass-filtered data; 1 Hz is the common starting
  point. For Epochs, fit on data that are high-pass filtered but not baseline
  corrected.
- `method='fastica'` requires scikit-learn; `method='picard'` requires Picard;
  `method='infomax'` is implemented in MNE-Python.
- `n_components` controls the number of PCA components passed to ICA; it is not
  the same as `n_pca_components` in `ICA.apply`, which controls reconstruction
  rank.
- `ICA.apply` mutates the provided Raw/Epochs/Evoked object and can introduce a
  DC shift. If data were baseline-corrected, use `on_baseline='reapply'` or
  reapply baseline explicitly after cleaning.
- `find_bads_ecg(method='ctps')` supports Raw/Epochs; use
  `method='correlation'` for Evoked.

SSP notes:

- `compute_proj_eog` and `compute_proj_ecg` detect artifacts, epoch around
  them, and compute projectors. EOG requires preloaded raw data; ECG can load
  if needed.
- `meg='combined'` requires matching `n_mag == n_grad` and returns a joint MEG
  projector count.
- Projectors are inert until applied with `apply_proj()` or used by methods
  with `proj=True`/`proj='delayed'`/interactive projection settings.

## EOG, ECG, muscle, amplitude, breaks, stim, fNIRS, and eye-tracking

Verified signatures:

```python
mne.preprocessing.find_eog_events(raw, event_id=998, l_freq=1, h_freq=10, filter_length='10s', ch_name=None, tstart=0, reject_by_annotation=False, thresh=None, verbose=None)
mne.preprocessing.create_eog_epochs(raw, ch_name=None, event_id=998, picks=None, tmin=-0.5, tmax=0.5, l_freq=1, h_freq=10, reject=None, flat=None, baseline=None, preload=True, reject_by_annotation=True, thresh=None, decim=1, verbose=None)
mne.preprocessing.find_ecg_events(raw, event_id=999, ch_name=None, tstart=0.0, l_freq=5, h_freq=35, qrs_threshold='auto', filter_length='10s', return_ecg=False, reject_by_annotation=True, verbose=None)
mne.preprocessing.create_ecg_epochs(raw, ch_name=None, event_id=999, picks=None, tmin=-0.5, tmax=0.5, l_freq=8, h_freq=16, reject=None, flat=None, baseline=None, preload=True, keep_ecg=False, reject_by_annotation=True, decim=1, verbose=None)
mne.preprocessing.annotate_muscle_zscore(raw, threshold=4, ch_type=None, min_length_good=0.1, filter_freq=(110, 140), n_jobs=None, verbose=None)
mne.preprocessing.annotate_break(raw, events=None, min_break_duration=15.0, t_start_after_previous=5.0, t_stop_before_next=5.0, ignore=('bad', 'edge'), *, verbose=None)
mne.preprocessing.annotate_amplitude(raw, peak=None, flat=None, bad_percent=5, min_duration=0.005, picks=None, *, verbose=None)
mne.preprocessing.fix_stim_artifact(inst, events=None, event_id=None, tmin=0.0, tmax=0.01, *, baseline=None, mode='linear', stim_channel=None, picks=None)
mne.preprocessing.compute_current_source_density(inst, sphere='auto', lambda2=1e-05, stiffness=4, n_legendre_terms=50, copy=True, *, verbose=None)
```

fNIRS signatures:

```python
mne.preprocessing.nirs.source_detector_distances(info, picks=None)
mne.preprocessing.nirs.short_channels(info, threshold=0.01)
mne.preprocessing.nirs.optical_density(raw, *, verbose=None)
mne.preprocessing.nirs.scalp_coupling_index(raw, l_freq=0.7, h_freq=1.5, l_trans_bandwidth=0.3, h_trans_bandwidth=0.3, verbose=False)
mne.preprocessing.nirs.temporal_derivative_distribution_repair(raw, *, verbose=None)
mne.preprocessing.nirs.tddr(raw, *, verbose=None)
mne.preprocessing.nirs.beer_lambert_law(raw, ppf=6.0, *, sd_distances=None)
```

Eye-tracking signatures:

```python
mne.preprocessing.eyetracking.find_blinks(inst, *, chs_src=None, method='dropout', dropout_value=None, description='BAD_blink', chs_dest=None, verbose=None)
mne.preprocessing.eyetracking.interpolate_blinks(raw, buffer=0.05, match='BAD_blink', interpolate_gaze=False)
mne.preprocessing.eyetracking.convert_units(inst, calibration, to='radians', *, verbose=None)
mne.preprocessing.eyetracking.set_channel_types_eyetrack(inst, mapping)
mne.preprocessing.eyetracking.read_eyelink_calibration(fname, screen_size=None, screen_distance=None, screen_resolution=None)
mne.preprocessing.eyetracking.Calibration(*, onset, model, eye, avg_error, max_error, positions, offsets, gaze, screen_size=None, screen_distance=None, screen_resolution=None)
```

Notes:

- EOG and ECG helpers filter only the detection channel(s) while finding events;
  the returned artifact epochs have the input raw data's filter state.
- If no ECG channel exists, `find_ecg_events` can synthesize ECG from MEG, but
  only when suitable MEG channels exist.
- `annotate_muscle_zscore` chooses the first available of `mag`, `grad`, `eeg`
  unless `ch_type` is provided. It returns annotations and score values; it
  does not attach them to raw automatically.
- `annotate_amplitude` returns annotations and bad-channel names; attach them
  with `raw.set_annotations(...)` and update `raw.info['bads']` deliberately.
- fNIRS and eye-tracking steps are usually modality-specific preprocessing
  before generic event/epoch/evoked handling.

## Source evidence

Distilled from MNE-Python source files `mne/event.py`, `mne/annotations.py`,
`mne/epochs.py`, `mne/evoked.py`, `mne/filter.py`, `mne/channels/channels.py`,
`mne/_fiff/reference.py`, `mne/preprocessing/ica.py`,
`mne/preprocessing/eog.py`, `mne/preprocessing/ecg.py`,
`mne/preprocessing/ssp.py`, `mne/preprocessing/artifact_detection.py`,
`mne/preprocessing/_annotate_amplitude.py`, `mne/preprocessing/stim.py`,
`mne/preprocessing/nirs`, `mne/preprocessing/eyetracking`, focused tutorials
under `tutorials/raw`, `tutorials/epochs`, `tutorials/evoked`, and
`tutorials/preprocessing`, focused tests under `mne/tests` and
`mne/preprocessing/tests`, plus installed signature inspection.
