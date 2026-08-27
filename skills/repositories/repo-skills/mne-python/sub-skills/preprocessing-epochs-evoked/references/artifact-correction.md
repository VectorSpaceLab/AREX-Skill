# Artifact correction and cleaning decisions

This reference covers correction choices owned by the
`preprocessing-epochs-evoked` sub-skill. Route plotting/report production to
`visualization-reporting`; route raw file reading and vendor import problems to
`io-raw-data`.

## Correction order that minimizes surprises

1. **Inspect or summarize artifacts before correcting.** Decide whether the
   artifact is transient, channel-specific, physiological, reference-related,
   line-noise-like, or modality-specific.
2. **Annotate bad spans first.** `BAD*` annotations can be honored by epoching,
   ECG/EOG detection, ICA fitting, covariance, and many data-extraction
   methods.
3. **Mark bad channels before referencing or interpolation.** Update
   `inst.info['bads']`; bad channels are excluded from average references and
   many picks.
4. **Choose reference/projection strategy.** Direct rereferencing changes data;
   average-reference projectors or SSP projectors can remain inactive until
   applied.
5. **Filter only when the artifact model supports it.** High-pass for ICA and
   low/notch for drifts/line noise are common; filtering cannot fix all
   transient artifacts.
6. **Fit ICA or compute SSP on an appropriate copy.** Keep fit data choices
   separate from final analysis data when high-pass or resampling choices differ.
7. **Apply correction, then re-check baseline, rank, bad channels, and trial
   counts.** ICA and projectors can affect rank; ICA may introduce a DC shift.

## BAD annotations and amplitude-based annotation

Use annotations to reject contaminated time spans without deleting data.

```python
annotations, bads = mne.preprocessing.annotate_amplitude(
    raw,
    peak={"eeg": 500e-6},
    flat={"eeg": 1e-6},
    bad_percent=5,
)
raw.set_annotations(raw.annotations + annotations)
raw.info["bads"].extend(bads)
```

Caveats:

- `annotate_amplitude` detects consecutive-sample jumps or flat stretches, not
  arbitrary peak-to-peak excursions over moving windows. Epoch `reject`/`flat`
  thresholds use epoch-level peak-to-peak logic.
- Returned annotations and bad channels are not attached automatically.
- `annotate_break` creates `BAD_break` annotations between annotations or
  events; by default it ignores existing descriptions starting with `bad` and
  `edge`.
- `reject_by_annotation=True` in `Epochs` drops epochs that partially overlap
  `BAD*` spans in the rejection window.

## Bad channels and interpolation

```python
raw.info["bads"] = ["EEG 053"]
raw_interp = raw.copy().interpolate_bads(reset_bads=False,
                                         on_bad_position="warn")
```

Caveats:

- Interpolation mutates the object and requires meaningful sensor positions for
  most EEG/MEG/ECoG/sEEG channels. With invalid positions, use
  `on_bad_position='raise'` to fail early, or `'warn'/'ignore'` only when NaN
  fill is acceptable.
- Default methods are MEG `MNE`, EEG `spline`, and fNIRS `nearest`. ECoG and
  sEEG support spline or NaN filling.
- Decide whether to keep bad-channel labels after interpolation. Use
  `reset_bads=False` when later methods should still know which channels were
  repaired.
- Bad channels are excluded from average-reference calculations and many picks.

## EEG reference choices

```python
raw_ref = raw.copy().set_eeg_reference(ref_channels="average")
raw_proj = raw.copy().set_eeg_reference(ref_channels="average", projection=True)
```

Decision matrix:

| Goal | Recommended action | Caveat |
| --- | --- | --- |
| Existing physical reference | `set_eeg_reference(ref_channels='A1')` or a list | Mutates data; bad channels are not included. |
| Missing physical reference channel | Add a zero-valued reference channel before rereferencing | Otherwise the new reference can be biased. |
| Average reference for sensor-space analysis | `ref_channels='average'` | Ensure original reference is represented if needed. |
| Toggle average reference later | `projection=True` | Adds a projector; apply explicitly or pass projection-aware options downstream. |
| Bipolar/contralateral derivations | Use bipolar reference APIs on the instance | Verify channel names and whether old channels are dropped. |

Rank note: average reference, projectors, interpolation, and CSD can all change
rank assumptions. Recompute or pass rank for covariance/inverse workflows.

## EOG and blink artifacts

Fast event/epoch helpers:

```python
eog_events = mne.preprocessing.find_eog_events(raw, ch_name="EOG 061")
eog_epochs = mne.preprocessing.create_eog_epochs(
    raw,
    ch_name="EOG 061",
    tmin=-0.5,
    tmax=0.5,
    reject_by_annotation=True,
)
```

ICA-based EOG repair:

```python
raw_fit = raw.copy().filter(1.0, None, picks="data")
ica = mne.preprocessing.ICA(n_components=0.99, random_state=97,
                            method="fastica", max_iter="auto")
ica.fit(raw_fit, reject_by_annotation=True)
eog_inds, scores = ica.find_bads_eog(raw_fit, ch_name="EOG 061")
ica.exclude = eog_inds
raw_clean = raw.copy()
ica.apply(raw_clean)
```

Caveats:

- `find_eog_events` requires an EOG channel unless a valid `ch_name` points to
  an ocular proxy channel; it filters only for detection.
- `create_eog_epochs` returns epochs around detected blink events but does not
  filter the returned data beyond the raw object's existing filter state.
- ICA EOG detection uses correlation against filtered EOG data. With
  `measure='zscore'`, threshold is adaptive z-scoring; with
  `measure='correlation'`, threshold is absolute correlation.
- For eye-tracking blink dropouts, use eye-tracking helpers below rather than
  EOG-only assumptions.

## ECG and heartbeat artifacts

Fast event/epoch helpers:

```python
ecg_events, ecg_ch, pulse = mne.preprocessing.find_ecg_events(
    raw,
    ch_name="ECG 001",
    qrs_threshold="auto",
)
ecg_epochs = mne.preprocessing.create_ecg_epochs(raw, ch_name="ECG 001")
```

ICA-based ECG repair:

```python
raw_fit = raw.copy().filter(1.0, None, picks="data")
ica = mne.preprocessing.ICA(n_components=40, random_state=97,
                            method="fastica", max_iter="auto")
ica.fit(raw_fit, reject_by_annotation=True)
ecg_inds, scores = ica.find_bads_ecg(raw_fit, method="ctps")
ica.exclude.extend(ecg_inds)
raw_clean = raw.copy()
ica.apply(raw_clean)
```

Caveats:

- If no ECG channel exists, ECG can be synthesized from MEG only when suitable
  magnetometer or gradiometer channels exist. Without ECG and without MEG,
  require a provided channel or a different detector.
- `find_ecg_events` maps detection times back to original raw samples even when
  `reject_by_annotation=True` omits bad spans during detection.
- `ICA.find_bads_ecg(method='ctps')` supports Raw/Epochs; use
  `method='correlation'` for Evoked.
- `qrs_threshold='auto'` targets plausible heart rates; document if threshold
  is manually adjusted.

## ICA planning caveats

Recommended ICA fit plan:

```python
raw_for_ica = raw.copy().filter(l_freq=1.0, h_freq=None, picks="data")
ica = mne.preprocessing.ICA(
    n_components=0.99,
    method="fastica",
    random_state=97,
    max_iter="auto",
)
ica.fit(raw_for_ica, reject_by_annotation=True, decim=3)
# choose components via automatic scores plus human/visual review when possible
raw_clean = raw.copy()
ica.apply(raw_clean, on_baseline="warn")
```

Rules:

- Fit on high-pass-filtered data, commonly 1 Hz. If the final analysis uses a
  lower high-pass, fit on a filtered copy and apply to the final raw/epochs only
  after confirming channel compatibility.
- Avoid fitting ICA on baseline-corrected epochs. MNE warns because baseline
  correction can harm ICA quality.
- `method='fastica'` requires scikit-learn; `method='picard'` requires Picard;
  `method='infomax'` is available in MNE-Python. If optional dependencies are
  absent, change method or install dependencies outside the skill guidance.
- `n_components=None` uses a variance threshold near 1.0 to avoid numerical
  instability with rank-deficient data. Floats select enough PCA components to
  exceed that cumulative variance; integers select an exact count.
- `n_pca_components` in `ICA.apply` is a reconstruction-rank control, not the
  same as fit-time `n_components`. Do not reduce it casually.
- If `noise_cov` is used for pre-whitening, document projector compatibility;
  temporally remove EOG/ECG projectors before fitting if those artifacts should
  be found by ICA.
- `ICA.apply` mutates data and can introduce a DC shift. If applying to
  baseline-corrected Epochs/Evoked, use `on_baseline='reapply'` or reapply
  baseline after cleaning.
- For repeated subjects/sessions, `corrmap` can label similar components across
  ICA solutions; keep `plot=False`/`show=False` if operating headlessly.

## SSP projectors for EOG/ECG and noise

EOG/ECG SSP pattern:

```python
projs, eog_events = mne.preprocessing.compute_proj_eog(
    raw,
    n_grad=2,
    n_mag=2,
    n_eeg=2,
    average=True,
    reject={"eeg": 500e-6},
)
raw_ssp = raw.copy().add_proj(projs)
# projectors are inactive until applied or used by proj-aware methods
raw_ssp.apply_proj()
```

Caveats:

- `compute_proj_eog` requires preloaded raw data. `compute_proj_ecg` may load
  raw if needed.
- Detection filters (`eog_l_freq/eog_h_freq`, `ecg_l_freq/ecg_h_freq`) are
  separate from filters applied to data channels (`l_freq/h_freq`) before SSP
  computation.
- Use `proj='delayed'` in `Epochs` when you want rejection decisions before
  final projector application.
- Projectors reduce effective rank. Recompute rank before covariance or inverse
  steps.
- `meg='combined'` requires equal `n_mag` and `n_grad` and computes joint MEG
  projectors.

## Muscle, line noise, and stimulus artifacts

Muscle annotation:

```python
annot_muscle, scores = mne.preprocessing.annotate_muscle_zscore(
    raw,
    threshold=4,
    ch_type="eeg",        # or mag/grad; None chooses first available mag, grad, eeg
    filter_freq=(110, 140),
)
raw.set_annotations(raw.annotations + annot_muscle)
```

Other helpers:

```python
raw.notch_filter(freqs=[50, 100], picks="data")
mne.preprocessing.fix_stim_artifact(inst, events=events, tmin=0, tmax=0.01,
                                    mode="linear")
```

Caveats:

- Muscle detection needs sufficient sampling frequency for the requested
  `filter_freq` band and only operates on one channel type.
- Notch filters are appropriate for narrow line noise, not broad or transient
  artifacts.
- `fix_stim_artifact` modifies a short time interval around events. Verify
  that `tmin`/`tmax` span only the acquisition artifact, not the neural
  response of interest.

## fNIRS artifact and physiology helpers

Typical steps:

1. Convert intensity to optical density with `nirs.optical_density`.
2. Optionally repair motion artifacts with
   `nirs.temporal_derivative_distribution_repair`/`nirs.tddr`.
3. Compute `nirs.scalp_coupling_index` and mark low-quality channels bad.
4. Convert to hemoglobin with `nirs.beer_lambert_law`.
5. Filter for hemodynamic frequency content and epoch from annotations.

Caveats:

- Short source-detector channels can be detected with
  `nirs.short_channels(info, threshold=0.01)`; whether to remove them depends
  on the analysis goal.
- Do not apply EEG/MEG ICA assumptions to fNIRS hemoglobin traces without a
  modality-specific justification.
- fNIRS epochs often use several seconds of pre/post-stimulus data and slower
  filters than EEG/MEG.

## Eye-tracking blink and unit helpers

```python
from mne.preprocessing import eyetracking

blink_annots = eyetracking.find_blinks(
    raw_et,
    method="dropout",
    dropout_value=0,
    description="BAD_blink",
)
raw_et.set_annotations(raw_et.annotations + blink_annots)
eyetracking.interpolate_blinks(raw_et, buffer=(0.05, 0.2),
                               match="BAD_blink",
                               interpolate_gaze=False)
```

Caveats:

- `find_blinks` returns annotations; attach them explicitly.
- `interpolate_blinks` mutates raw and matches annotation descriptions by
  default against `BAD_blink`.
- Pupil interpolation is safer than gaze interpolation. Use
  `interpolate_gaze=True` only when the analysis tolerates possible gaze motion
  during blinks.
- `convert_units` needs calibration and screen geometry to convert gaze to
  visual angle. Calibration loading belongs to the file/IO workflow; this
  sub-skill uses the resulting calibration object.

## Choosing no correction

It is valid to return a plan that does not correct an artifact when:

- The artifact is outside the analysis window or excluded by annotations.
- Correction would remove signal of interest or change rank/baseline more than
  the downstream model can tolerate.
- The requested dependency or modality-specific evidence is absent.
- The user asked only for event/epoch/evoked construction and not data repair.

When choosing no correction, state the evidence, the expected residual artifact,
and the sanity checks the user should inspect downstream.
