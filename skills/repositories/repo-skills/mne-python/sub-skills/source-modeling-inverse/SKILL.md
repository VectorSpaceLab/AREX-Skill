---
name: source-modeling-inverse
description: "Guide MNE-Python source-space, BEM, forward, covariance, inverse,
  beamformer, dipole, morphing, and SourceEstimate workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MNE-Python source modeling and inverse router

Use this sub-skill when a task moves from sensor-space MNE objects to anatomy,
source spaces, forward solutions, inverse operators, beamformers, dipoles,
labels, or source estimates.

## Load order

1. For the staged anatomy → source space/BEM → forward → covariance → inverse
   workflow, read [references/workflows.md](references/workflows.md).
2. For verified signatures and parameter decision notes, read
   [references/api-reference.md](references/api-reference.md).
3. Before running any source-modeling command, read
   [references/prerequisites-and-data.md](references/prerequisites-and-data.md)
   to check `subjects_dir`, transforms, BEM/source files, optional external
   tools, and sample/testing data assumptions.
4. If a task reports file, rank, orientation, coordinate-frame, or external
   binary errors, read [references/troubleshooting.md](references/troubleshooting.md).
5. To validate source-modeling inputs without doing heavy modeling, run or
   adapt [scripts/source_inputs_check.py](scripts/source_inputs_check.py).

## Own these requests

- Build or validate FreeSurfer-style anatomy inputs, source spaces, BEM models,
  BEM solutions, transforms, covariance files, forward solutions, and inverse
  operators.
- Choose between surface, volume, mixed, and discrete source spaces.
- Compute or use forward solutions with `make_forward_solution`,
  `make_forward_dipole`, sensitivity maps, and field maps.
- Build minimum-norm inverse operators and apply MNE, dSPM, sLORETA, eLORETA,
  or label-restricted inverses to `Evoked` or `Epochs` data.
- Build LCMV/DICS beamformers, dipole fits, mixed-norm inverse estimates, and
  source morphs.
- Work with `SourceEstimate`, vector/mixed/volume source estimates, labels,
  label time courses, parcellations, morphing, and source-space adjacency.

## Route elsewhere

- Loading raw files, creating `RawArray`, or fixing channel metadata belongs to
  `io-raw-data`.
- Filtering, event extraction, `Epochs`, `Evoked`, rejection, ICA/SSP, and
  covariance preprocessing decisions belong to `preprocessing-epochs-evoked`.
- Source and brain visualization belongs to `visualization-reporting` after the
  source object exists.
- Cluster statistics, decoding, spectra/TFR, and source-level statistical
  tests belong to `timefreq-stats-decoding-simulation`.
- CLI setup commands such as `mne setup_source_space` and `mne watershed_bem`
  are introduced in `cli-datasets-config`; this sub-skill explains their data
  prerequisites and source-modeling context.

## Operating rules

- Treat source modeling as a file-graph problem before it is a computation:
  identify `Info`/epochs/evoked, `trans`, `src`, `bem`, covariance, inverse or
  forward files, subject name, `subjects_dir`, coordinate frames, and channel
  picks before calling heavy functions.
- Do not invent anatomy paths or assume sample data is present. If a task lacks
  MRI/FreeSurfer outputs, offer sphere-model or EEG-without-MRI alternatives
  only when scientifically acceptable for the user's goal.
- Keep optional external systems explicit: FreeSurfer, OpenMEEG, MNE-C tools,
  PyVista/3D rendering, and MNE sample/testing datasets are optional
  prerequisites, not base-package guarantees.
- Align rank, projectors, bad channels, reference state, and covariance with the
  data that will enter the inverse. Mismatches usually invalidate source
  estimates even if code runs.
- Never require the original MNE-Python repository checkout at runtime; bundled
  references and scripts here are the operating context.
