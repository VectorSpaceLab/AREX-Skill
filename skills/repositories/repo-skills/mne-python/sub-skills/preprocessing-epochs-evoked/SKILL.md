---
name: preprocessing-epochs-evoked
description: "Guide MNE-Python event extraction, sensor-space preprocessing,
  Epochs, Evoked, artifact correction, covariance, and rank workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MNE-Python preprocessing, Epochs, and Evoked router

Use this sub-skill when a task needs to turn continuous MNE data into events,
epochs, evoked responses, or cleaned sensor-space data before downstream
analysis.

## Load order

1. For signatures, object contracts, and parameter caveats, read
   [references/api-reference.md](references/api-reference.md).
2. For event, epoch, evoked, covariance/rank, fNIRS, and eye-tracking recipes,
   read [references/workflows.md](references/workflows.md).
3. For ICA, SSP, EOG/ECG, muscle, reference, interpolation, fNIRS, and blink
   correction decisions, read
   [references/artifact-correction.md](references/artifact-correction.md).
4. If the user reports an error, warning, dropped trials, missing events, bad
   shapes, filter issues, or fitting failures, read
   [references/troubleshooting.md](references/troubleshooting.md).
5. For a deterministic local smoke check, run or adapt
   [scripts/preprocessing_smoke.py](scripts/preprocessing_smoke.py) with a
   Python environment that has MNE-Python and NumPy installed.

## Own these requests

- Event arrays from stim channels, annotations, or fixed windows:
  `find_events`, `events_from_annotations`, `make_fixed_length_events`,
  `pick_events`, `merge_events`, event dictionaries, duplicate-event policy,
  and `BAD*` annotation behavior.
- Epoch construction and arrays: `Epochs`, `EpochsArray`, metadata, selection,
  `baseline`, `reject`, `flat`, `proj`, `detrend`, `decim`,
  `reject_by_annotation`, `on_missing`, `on_outside`, and `event_repeated`.
- Evoked construction and arrays: `epochs.average()`, `Evoked`,
  `EvokedArray`, `read_evokeds`, `write_evokeds`, `combine_evoked`,
  `grand_average`, cropping, filtering, resampling, baseline, channel picking,
  and save/load round trips.
- Sensor-space cleaning before epochs or averaging: filtering, notch filtering,
  resampling, bad-channel marking, interpolation, EEG reference changes,
  projectors, ICA, SSP, EOG/ECG/muscle artifact helpers, fNIRS preprocessing,
  and eye-tracking blink handling.
- Noise covariance and rank estimates that depend on preprocessing choices:
  `compute_covariance` and `compute_rank`.

## Route elsewhere

- File loading, vendor-specific readers, `RawArray` basics, `Info` creation,
  channel metadata ingestion, raw concatenation, and file export belong to the
  sibling `io-raw-data` sub-skill.
- Plot layout, interactive browsers, reports, topomaps, `mne.Report`, and
  headless rendering belong to `visualization-reporting`.
- Time-frequency, spectra beyond filtering, statistics, decoding, CSP,
  simulation, and source-level statistics belong to
  `timefreq-stats-decoding-simulation`.
- Source spaces, BEM/forward/inverse operators, beamformers, and source
  estimates belong to `source-modeling-inverse`.

## Operating rules

- Prefer copy-before-mutate for user data. Many MNE methods mutate in place and
  return `self` (`filter`, `resample`, `set_eeg_reference`,
  `interpolate_bads`, `apply_proj`, `ICA.apply`).
- Preserve event timing deliberately. If downsampling after extracting events,
  use `Raw.resample(..., events=events)` or recompute events from the resampled
  raw object; do not silently reuse stale event sample numbers.
- Keep artifact-correction plans evidence-based: mark bad spans/channels first,
  document whether ICA/SSP/filtering/referencing changes rank or baseline, and
  inspect `drop_log`, `info['bads']`, projector state, `epochs.selection`, and
  `evoked.nave` after each stage.
- Never require the original repository checkout at runtime. This skill is
  self-contained; source paths mentioned in reference files are provenance only.
