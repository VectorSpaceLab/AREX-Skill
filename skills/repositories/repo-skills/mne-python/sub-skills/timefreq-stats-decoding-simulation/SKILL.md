---
name: timefreq-stats-decoding-simulation
description: "Guide MNE-Python time-frequency, spectral, statistics, decoding,
  and simulation workflows for Raw, Epochs, Evoked, and source data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MNE-Python time-frequency, statistics, decoding, and simulation router

Use this sub-skill when a task needs spectra, time-frequency transforms,
cross-spectral density, statistical inference, machine-learning/decoding, or
synthetic MNE data.

## Load order

1. For PSD/TFR/CSD, statistics, decoding, and simulation recipes, read
   [references/workflows.md](references/workflows.md).
2. For verified signatures, object shapes, and API defaults, read
   [references/api-reference.md](references/api-reference.md).
3. For permutation clusters, adjacency, regression, cross-validation, CSP, and
   scikit-learn-dependent decoding details, read
   [references/statistics-and-decoding.md](references/statistics-and-decoding.md).
4. If the task reports shape, baseline, frequency, permutation, adjacency,
   scikit-learn, or simulation errors, read
   [references/troubleshooting.md](references/troubleshooting.md).
5. For a deterministic local smoke check, run or adapt
   [scripts/analysis_smoke.py](scripts/analysis_smoke.py).

## Own these requests

- Power spectra and spectral estimates: `Raw.compute_psd`, `Epochs.compute_psd`,
  `Spectrum`, Welch/multitaper array helpers, frequency-band summaries.
- Time-frequency representations: Morlet/wavelet, multitaper, Stockwell, TFR
  objects, baseline correction, decimation, and output type choices.
- Cross-spectral density and frequency-domain beamformer inputs.
- Sensor/source statistics: permutation tests, cluster tests, adjacency,
  multiple-comparison correction, regression, and FDR.
- Decoding and machine learning: CSP, SSD, Xdawn, EMS, receptive fields,
  `SlidingEstimator`, `GeneralizingEstimator`, scikit-learn pipelines, scoring,
  leakage-safe cross-validation.
- Simulation: synthetic `Raw`, `Evoked`, `SourceEstimate`, source simulators,
  metrics, and generated data for tests/examples.

## Route elsewhere

- Reading files, channel metadata ingestion, and synthetic `RawArray` basics
  belong to `io-raw-data`.
- Filtering, artifact correction, event extraction, epochs, evoked responses,
  covariance preprocessing, and rank preparation belong to
  `preprocessing-epochs-evoked`.
- Plotting spectra/TFR/topomaps/results belongs to `visualization-reporting`
  after this sub-skill chooses the analysis output.
- Source spaces, forward models, inverse operators, and beamformer filter
  construction belong to `source-modeling-inverse`; this sub-skill owns CSD and
  statistical analysis around those outputs.
- Installation/extras and no-download dataset checks belong to
  `cli-datasets-config`.

## Operating rules

- Decide and document data shape before selecting an API. Sensor/epoch arrays,
  `Epochs`, `Evoked`, `SourceEstimate`, and NumPy arrays have different axis
  conventions and adjacency needs.
- Choose frequency parameters from sampling rate and epoch length; avoid asking
  for frequencies that cannot be resolved from the available data.
- Keep statistics independent of visualization: first compute arrays/statistics,
  then route plotting to the visualization sub-skill.
- Treat scikit-learn as an optional dependency for many decoding workflows.
  If unavailable, either install the documented extra/path or restrict the task
  to non-decoding analysis.
- Prevent data leakage. Fitting filters, scalers, CSP, feature selection, or
  decoders must happen inside cross-validation pipelines when estimating
  generalization.
- Never depend on the original repository checkout at runtime; use these
  references and bundled helpers.
