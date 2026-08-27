# Analysis Workflows

Read this when an MNE-Python task needs spectra, time-frequency estimates,
statistical testing, decoding, or simulated data.

## PSD and spectra

Use object methods when the data is already in MNE containers:

```python
spectrum = raw.compute_psd(fmin=1, fmax=40, method='welch')
psds, freqs = spectrum.get_data(return_freqs=True)
```

Use array helpers when the data is a NumPy array with known sampling frequency:

```python
from mne.time_frequency import psd_array_welch
psds, freqs = psd_array_welch(data, sfreq=sfreq, fmin=1, fmax=40)
```

Checklist:

- Confirm sampling frequency and epoch length before setting `fmin`, `fmax`,
  `n_fft`, and `n_per_seg`.
- Document channel/epoch averaging explicitly; do not silently average over
  epochs, channels, or frequencies.
- Route plotting of spectra/topomaps to `visualization-reporting`.

## Time-frequency representations

Typical Morlet workflow:

```python
from mne.time_frequency import tfr_morlet

freqs = [6, 8, 10, 12, 15, 20, 30]
power = tfr_morlet(epochs, freqs=freqs, n_cycles=freqs / 2,
                   return_itc=False, average=True, decim=2)
power.apply_baseline((-0.2, 0), mode='logratio')
```

Decision points:

- `average=True` returns averaged TFR; `average=False` keeps trials for stats or
  single-trial modeling.
- `n_cycles` trades time and frequency resolution.
- `decim` reduces data size after convolution; verify timing still supports the
  task.
- Baseline mode (`ratio`, `logratio`, `percent`, `zscore`, etc.) affects
  interpretation; record it.

## Cross-spectral density

CSD feeds frequency-domain source estimates and connectivity-style analyses.
Compute CSD from epochs in the selected frequency bands, then route beamformer
filter creation/application to `source-modeling-inverse` when DICS is needed.

## Statistical inference

Typical sensor/epoch array route:

1. Build arrays with the intended observation axis first, commonly
   `(n_observations, n_times)` or `(n_observations, n_features)` per condition.
2. Select a statistic and correction strategy: permutation, cluster-based
   permutation, FDR, regression, or parametric test.
3. Build adjacency for sensors, time-frequency grids, or source spaces when
   using cluster tests.
4. Set `seed`, `n_permutations`, `tail`, and threshold deliberately.
5. Report cluster p-values/statistics and the exact dimensions they cover.

Do not run long permutation counts for exploratory routing. Use small synthetic
checks for code validation, then increase permutations for scientific analysis.

## Decoding and machine learning

MNE decoding integrates with scikit-learn-style estimators. Common routes:

- CSP + classifier for EEG/MEG class discrimination.
- `SlidingEstimator` for time-resolved decoding.
- `GeneralizingEstimator` for temporal generalization.
- Receptive field models for continuous stimulus-response relationships.
- SSD/Xdawn/EMS for spatial filtering or denoising before classification.

Leakage-safe pattern:

```python
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from mne.decoding import CSP, SlidingEstimator, cross_val_multiscore

base = make_pipeline(CSP(n_components=4, log=True), LogisticRegression(max_iter=1000))
time_decod = SlidingEstimator(base, scoring='roc_auc', n_jobs=None)
scores = cross_val_multiscore(time_decod, X, y, cv=5)
```

Fit scalers, CSP, feature selection, and classifier steps inside the pipeline,
not on the full dataset before cross-validation.

## Simulation

Use simulation when the user needs deterministic fixtures, tutorials, or method
validation without real data. For lightweight sensor-space checks, prefer
`create_info` + `RawArray` from the I/O sub-skill. For source-space simulation,
use source spaces and forward models from `source-modeling-inverse` first.

A safe helper in this sub-skill creates tiny synthetic data and validates PSD
and small statistics without downloads.

## Cross-skill integration pattern

- I/O creates `Raw`/`Info` and sets channel metadata.
- Preprocessing creates cleaned `Epochs`/`Evoked` and documents rejection/rank.
- This sub-skill computes PSD/TFR/stats/decoding/simulation outputs.
- Visualization/reporting renders plots or reports.
- Source-modeling handles forward/inverse/beamformer object construction.
