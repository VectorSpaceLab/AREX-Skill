# Classic Detector Model Overview

Read this when mapping a task to a PyOD detector family. This is not a full
mathematical catalog; it is an operating map for common package workflows.

## Reliable starting points

| Need | Good first choices | Notes |
|---|---|---|
| Fast general baseline | `ECOD`, `COPOD`, `HBOS` | Parameter-light, good for smoke tests and large tabular data. |
| General ensemble baseline | `IForest` | Robust starting point; set `random_state` for reproducibility. |
| Local density/proximity anomaly | `KNN`, `LOF`, `CBLOF`, `COF` | Scale numeric features first; can be slower on large n. |
| Linear/subspace structure | `PCA`, `KPCA`, `MCD`, `OCSVM`, `LMDD` | Useful when anomalies are projection/covariance/deviation based. |
| Score ensembles | `FeatureBagging`, `LSCP`, `LODA`, `INNE` | Some routes need optional `combo` or careful base estimators. |
| Supervised labels available | `XGBOD` | Requires `pyod[xgboost]`; use labels in `fit`. |
| Speed-up many detectors | `SUOD` | Requires `pyod[suod]`; route dependency handling to `model-operations`. |

## Detector families in the PyOD tree

- Probabilistic/statistical: `ECOD`, `COPOD`, `ABOD`, `MAD`, `SOS`, `QMCD`,
  `KDE`, `Sampling`, `GMM`.
- Linear models: `PCA`, `KPCA`, `MCD`, `CD`, `OCSVM`, `LMDD`.
- Proximity/density: `KNN`, `LOF`, `COF`, `CBLOF`, `LOCI`, `HBOS`, `HDBSCAN`,
  `SOD`, `ROD`.
- Ensembles: `IForest`, `INNE`, `DIF`, `FeatureBagging`, `LSCP`, `LODA`,
  `SUOD`, `XGBOD`.
- Neural/deep: `AutoEncoder`, `VAE`, `DeepSVDD`, `AnoGAN`, `ALAD`, `AE1SVM`,
  `SO_GAAL`, `MO_GAAL`, `DevNet`, `LUNAR`. These are routed to
  `specialized-modalities` for torch, device, and small-data caveats.

## Practical decision rules

1. If the request is exploratory and labels are absent, start with two or three
   diverse detectors (`ECOD`, `IForest`, `KNN` or `LOF`) or use ADEngine.
2. If features differ by orders of magnitude, scale before distance, density,
   kernel, and neural methods. ECOD/COPOD are safer as unscaled baselines.
3. If `n_samples` is small, avoid deep detectors and large ensembles. Prefer
   `ECOD`, `HBOS`, `IForest`, or `KNN` with conservative parameters.
4. If the data is high-dimensional and sparse-like, start with `ECOD`, `COPOD`,
   `PCA`, or `IForest`; proximity methods may be less meaningful.
5. If runtime matters, avoid all-pairs or heavy neural methods unless evidence
   supports the cost. Use smaller synthetic smoke tests before large runs.
6. If labels exist, do not force an unsupervised-only report. Evaluate scores
   against labels and consider `XGBOD` for a supervised detector.

## Optional extras that affect classic routes

Base PyOD does not install every optional backend. Common ImportError fixes:

- `XGBOD`: install `pyod[xgboost]`.
- `SUOD`: install `pyod[suod]`.
- Feature/score-combination helpers that import Combo: install `pyod[combo]`.
- PyThresh thresholding objects: install `pyod[pythresh]`.
- Neural detectors: install `pyod[torch]` and verify device/runtime.

Use `model-operations` for SUOD/XGBOD/thresholding/combination operations and
`specialized-modalities` for torch-backed detector guidance.

## Native verification anchors

Good focused checks for this area include:

- Synthetic helper: `scripts/classic_detector_smoke.py --detector IForest --json`.
- PyOD tests corresponding to selected detectors, such as IForest/KNN/ECOD tests.
- Data helper tests for `generate_data`, `generate_data_clusters`, categorical
  fixture generation, shape checks, and `evaluate_print`.

Do not use long benchmark scripts or notebook-scale comparison runs as routine
verification. They are useful evidence but too broad for a normal skill-guided
operation.
