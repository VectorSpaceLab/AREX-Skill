# PyOD time-series workflows

## Data contract

- Input is numeric time series data as a NumPy-compatible array.
- Univariate shape: `(n_timestamps,)`.
- Multivariate shape: `(n_timestamps, n_channels)`, where rows are ordered timestamps and columns are channels.
- Output scores are timestamp-level: `decision_scores_.shape == (n_timestamps,)`; higher means more anomalous.
- Labels are produced by the usual PyOD contamination threshold: `labels_` contains `0` for inlier and `1` for outlier.
- `pyod.utils.data.generate_ts_data(...)` returns `(X_train, X_test, y_train, y_test)` and is useful for synthetic checks. It can generate `anomaly_type='point'`, `'subsequence'`, or `'both'` and returns 1-D arrays for univariate data.

## Windowing and score mapping

Windowed detectors flatten each sliding window to a row with shape `(window_size * n_channels,)`, fit or score a standard detector on those windows, then map window scores back to timestamps.

Boundary timestamps without enough window coverage are filled with the fitted `threshold_` so the public score vector still has length `n_timestamps`. This matters when comparing early/late timestamps or computing external metrics.

Valid aggregation values used by the time-series implementations are:

- `max`: a timestamp inherits the largest window score covering it.
- `mean`: a timestamp receives the average window score over covering windows.

## Detector selection table

| Detector | Import | Backend | Fit/scoring mode | Key parameters | Minimum length and caveats |
|---|---|---:|---|---|---|
| `TimeSeriesOD` | `pyod.models.ts_od.TimeSeriesOD` | Core CPU | Inductive; `decision_function(X_new)` works | `detector='IForest'` or any PyOD detector/string shortcut, `window_size`, `step`, `score_aggregation`, `contamination` | Needs at least `window_size` timestamps. Good first choice when a normal tabular detector should run on windows. |
| `SpectralResidual` | `pyod.models.ts_spectral_residual.SpectralResidual` | Core CPU | Inductive dense saliency; `decision_function(X_new)` works | `score_window`, `channel_aggregation`, `contamination` | Needs at least `max(score_window, 2)` timestamps. FFT saliency only; not the full Microsoft SR-CNN service. |
| `KShape` | `pyod.models.ts_kshape.KShape` | Core CPU | Inductive; scores new series against learned centroids | `n_clusters`, `window_size`, `max_iter`, `channel_aggregation`, `random_state` | Needs `n_timestamps - window_size + 1 >= n_clusters`. Slower than simple window bridges; reduce `max_iter` for smoke tests. |
| `MatrixProfile` | `pyod.models.ts_matrix_profile.MatrixProfile` | Core CPU | **Transductive**; use `decision_scores_` after `fit()` | `window_size`, `channel_aggregation`, `contamination` | Needs at least `window_size + 1` timestamps. `decision_function`, `predict`, `predict_proba`, and `predict_confidence` intentionally raise `NotImplementedError`. |
| `SAND` | `pyod.models.ts_sand.SAND` | Core CPU | Inductive streaming-style scoring | `window_size`, `n_clusters`, `alpha`, `batch_size`, `max_iter`, `channel_aggregation`, `random_state` | Needs `window_size + 1` timestamps and an initial batch with at least `n_clusters` subsequences. Experimental/drift-adaptation path. |
| `LSTMAD` | `pyod.models.ts_lstm.LSTMAD` | `torch` extra; CPU implementation | Inductive next-step prediction with Mahalanobis error | `window_size`, `hidden_size`, `n_layers`, `epochs`, `lr`, `batch_size` | Needs at least `window_size + 10` timestamps. First `window_size` scores are threshold-filled. Source implementation trains on CPU. |
| `AnomalyTransformer` | `pyod.models.ts_anomaly_transformer.AnomalyTransformer` | `torch` extra | Inductive Transformer reconstruction/association discrepancy | `window_size`, `d_model`, `n_heads`, `n_layers`, `epochs`, `batch_size`, `lambda_`, `step`, `device` | Needs at least `window_size` timestamps. `d_model` must be divisible by `n_heads`. Use small `d_model`, `n_layers`, and `epochs` for checks; set `device='cpu'` when GPU has not been verified. |

## Minimal examples

### Windowed PyOD detector on timestamps

```python
from pyod.models.ts_od import TimeSeriesOD
from pyod.utils.data import generate_ts_data

X_train, X_test, y_train, y_test = generate_ts_data(
    n_train=300, n_test=120, contamination=0.05, random_state=42)

clf = TimeSeriesOD(detector='ECOD', window_size=20, step=1,
                   score_aggregation='max', contamination=0.1)
clf.fit(X_train)
train_scores = clf.decision_scores_
test_scores = clf.decision_function(X_test)
test_labels = clf.predict(X_test)
```

### Transductive Matrix Profile

```python
from pyod.models.ts_matrix_profile import MatrixProfile

clf = MatrixProfile(window_size=20, contamination=0.1)
clf.fit(X_train)
scores = clf.decision_scores_   # length == len(X_train)
labels = clf.labels_            # use after fit; do not call predict(X_new)
```

### Torch-backed AnomalyTransformer with explicit CPU

```python
from pyod.models.ts_anomaly_transformer import AnomalyTransformer

clf = AnomalyTransformer(window_size=40, d_model=32, n_heads=2,
                         n_layers=1, epochs=2, batch_size=16,
                         device='cpu', contamination=0.1)
clf.fit(X_train)
scores = clf.decision_function(X_test)
```

## Validation checklist

- Confirm `X.ndim` is 1 or 2; reshape `(n_channels, n_timestamps)` data before fitting.
- Check `len(scores) == n_timestamps` after fit and test scoring.
- For multivariate data, use the same number of channels at `fit()` and `decision_function()` for `KShape`, `SAND`, `LSTMAD`, and `AnomalyTransformer`.
- For `MatrixProfile`, verify that the user accepts transductive-only scores.
- For torch detectors, verify `torch` is importable and use small CPU settings before long training.
- Run `scripts/time_series_smoke.py --detector all --json` from this sub-skill for a deterministic core-CPU check.
