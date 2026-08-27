# Optional Extras for Model Operations

PyOD's base install covers core persistence and many classic detectors. Several model-operation surfaces are intentionally optional. Install only the extras needed for the workflow; do not assume `pyod[all]` is required.

## Exact Extra Names

Use exact names; pip only warns on unknown extras.

| Need | Extra | Installs | Enables |
|---|---|---|---|
| Score combination wrappers | `combo` | `combo` | `pyod.models.combination`, FeatureBagging internals that depend on combo |
| Data-driven thresholding | `pythresh` | `pythresh` | `pyod.models.thresholds.*` factories |
| SUOD acceleration | `suod` | `suod` | `pyod.models.suod.SUOD` acceleration framework |
| XGBOD supervised detector | `xgboost` | `xgboost` | `pyod.models.xgbod.XGBOD` |
| Neural threshold/detector components | `torch` | `torch>=2.0` | torch-based detectors and some PyThresh/VAE paths |

Install examples:

```bash
pip install 'pyod[combo]'
pip install 'pyod[pythresh]'
pip install 'pyod[suod]'
pip install 'pyod[xgboost]'
pip install 'pyod[combo,pythresh,suod,xgboost]'
```

Quote extras in zsh or any shell where brackets may expand.

## Base-Environment Import Facts

A verified base PyOD environment did **not** install `combo`, `pythresh`, `suod`, or `xgboost`. In that environment:

- importing `pyod.models.thresholds` succeeded because each factory imports `pythresh` lazily only when called;
- calling a threshold factory such as `FILTER()` would require `pythresh`;
- importing `pyod.models.combination` failed with `ModuleNotFoundError: No module named 'combo'` after an install hint;
- importing `pyod.models.suod` failed before reaching `SUOD` construction because `suod.py` imports `pyod.models.combination`, which needs `combo`;
- importing `pyod.models.xgbod` failed with `ModuleNotFoundError: No module named 'xgboost'`.

Operationally, report these as optional-extra gaps. Do not rewrite detector code or treat them as base PyOD breakage.

## SUOD Acceleration

`pyod.models.suod.SUOD` wraps the external SUOD framework for scalable unsupervised detector training and prediction.

Key constructor arguments from source:

```python
SUOD(
    base_estimators=None,
    contamination=0.1,
    combination="average",
    n_jobs=None,
    rp_clf_list=None,
    rp_ng_clf_list=None,
    rp_flag_global=True,
    target_dim_frac=0.5,
    jl_method="basic",
    bps_flag=True,
    approx_clf_list=None,
    approx_ng_clf_list=None,
    approx_flag_global=True,
    approx_clf=None,
    verbose=False,
)
```

Default `base_estimators` are a heterogeneous list including LOF, HBOS, COPOD, and IForest variants. `combination` supports at least `"average"` and `"maximization"` in the PyOD wrapper.

Minimal pattern:

```python
from pyod.models.suod import SUOD
from pyod.models.lof import LOF
from pyod.models.iforest import IForest
from pyod.models.copod import COPOD

base = [LOF(n_neighbors=15), COPOD(), IForest(n_estimators=100, random_state=42)]
clf = SUOD(base_estimators=base, n_jobs=2, combination="average", contamination=0.1)
clf.fit(X_train)
scores = clf.decision_function(X_test)
labels = clf.predict(X_test)
```

Install guidance:

```bash
pip install 'pyod[suod,combo]'
```

Why include `combo`: the PyOD `suod.py` module imports `average` and `maximization` from `pyod.models.combination`, and that module depends on the external `combo` package.

Troubleshooting:

- `No module named 'combo'` while importing SUOD: install `pyod[combo]` in addition to `pyod[suod]`.
- `pyod.models.suod requires the optional suod package`: install `pyod[suod]`.
- Parallel issues: set `n_jobs=1` for debugging and ensure every base estimator can fit independently.
- Shape issues after scoring: verify `decision_function(X)` returns one score per sample and that base-estimator score matrices have expected dimensions.

## XGBOD Supervised Detector

`pyod.models.xgbod.XGBOD` is a semi-supervised/supervised detector. It augments original features with scores from unsupervised detectors, then trains an XGBoost classifier.

Constructor highlights from source:

```python
XGBOD(
    estimator_list=None,
    standardization_flag_list=None,
    max_depth=3,
    learning_rate=0.1,
    n_estimators=100,
    objective="binary:logistic",
    booster="gbtree",
    n_jobs=1,
    nthread=None,
    random_state=0,
    **kwargs,
)
```

Operational pattern:

```python
from pyod.models.xgbod import XGBOD

clf = XGBOD(random_state=42, n_estimators=100)
clf.fit(X_train, y_train)  # y is required and must be binary: 0 inlier, 1 outlier
scores = clf.decision_function(X_test)
labels = clf.predict(X_test)
proba = clf.predict_proba(X_test)
```

Install guidance:

```bash
pip install 'pyod[xgboost]'
```

Validation notes:

- Unlike most unsupervised PyOD detectors, `fit(X, y)` requires labels.
- `estimator_list` and `standardization_flag_list` must have equal lengths if provided.
- Default unsupervised feature generators include ranges of KNN, LOF, HBOS, OCSVM, and IForest settings, with invalid neighbor counts filtered by sample size.
- For tiny datasets, default KNN/LOF ranges may be limited; validate after fit that `n_detector_ > 0`.

## Combo Score Combination

`pyod.models.combination` requires the `combo` package and provides `average`, `maximization`, `median`, `majority_vote`, `aom`, and `moa`. See [thresholding-and-combination.md](thresholding-and-combination.md) for shapes and workflow details.

Install:

```bash
pip install 'pyod[combo]'
```

If importing `pyod.models.combination` prints `please install combo first` and then raises `ModuleNotFoundError`, the fix is dependency installation, not an API rename.

## PyThresh Thresholders

`pyod.models.thresholds` factories import `pythresh.thresholds.*` lazily. Install:

```bash
pip install 'pyod[pythresh]'
```

Operational caveats:

- Some thresholders have method-specific dependencies inside pythresh.
- The `VAE` thresholder uses a torch-backed workflow; install/validate the relevant torch stack if selected.
- Some pythresh resource-loading bugs can be version/Python-specific. If a threshold factory imports but fails while loading internal `.pkl` resources, capture `python --version`, `pythresh` version, and the exact thresholder name, then try a newer pythresh wheel or a Python version supported by that wheel.

## Optional Extra Probe Snippet

Use this quick diagnostic in a user's environment:

```python
import importlib.util

for pkg in ["combo", "pythresh", "suod", "xgboost"]:
    print(pkg, "available" if importlib.util.find_spec(pkg) else "missing")
```

Then install the missing extras that match the workflow. Avoid installing all extras just to fix one missing optional package unless the task genuinely needs the whole stack.
