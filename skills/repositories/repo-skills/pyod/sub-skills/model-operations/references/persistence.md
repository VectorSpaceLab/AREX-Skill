# Persistence and Compatibility

PyOD's recommended persistence API is `pyod.utils.persistence`. It wraps `joblib` with a versioned envelope and a conservative compatibility loader for a documented sklearn Tree dtype drift.

## Public API

```python
from pyod.utils.persistence import save, load, compat_load

save(model, path, metadata=None) -> None
load(path, strict=False, return_metadata=False, *, trusted=False) -> model_or_tuple
compat_load(path, mmap_mode=None, *, trusted=False) -> object
```

- `save(model, path, metadata=None)` writes a `joblib` artifact whose top-level object is an envelope containing the model and dependency versions.
- `load(path, trusted=True)` loads either a PyOD envelope or a legacy raw `joblib.dump` artifact. It refuses to deserialize until `trusted=True` is passed.
- `load(path, return_metadata=True, trusted=True)` returns `(model, envelope_without_model)` for PyOD envelopes, or `(model, None)` for legacy raw artifacts.
- `load(path, strict=True, trusted=True)` raises on sklearn, joblib, numpy, or scipy version drift. Python-version drift is informational only.
- `compat_load(path, trusted=True)` mirrors `joblib.load` but adds a scoped repair for sklearn Tree node dtype mismatch.

## Trust Boundary: Non-Negotiable

`pickle` and `joblib` can execute arbitrary Python code while loading. PyOD's wrapper is intentionally fail-closed:

```python
from pyod.utils.persistence import load

# Raises ValueError before opening/deserializing the file.
load("artifact.pyod.joblib")

# Use only for artifacts from a trusted model registry, training job, or owner.
clf = load("artifact.pyod.joblib", trusted=True)
```

`trusted=True` does **not** make untrusted files safe. It only records that the caller accepts the artifact source. `strict=True`, envelope schema checks, and dependency-version checks are not a sandbox.

## Recommended Save/Load Workflow

```python
from pyod.models.iforest import IForest
from pyod.utils.data import generate_data
from pyod.utils.persistence import save, load

X_train, X_test, *_ = generate_data(
    n_train=200, n_test=50, n_features=4, contamination=0.1, random_state=42
)
clf = IForest(contamination=0.1, random_state=42).fit(X_train)

save(
    clf,
    "iforest.pyod.joblib",
    metadata={
        "dataset_id": "fraud-v12",
        "feature_schema": ["amount", "age", "country_score", "velocity"],
        "training_run": "2026-01-15T00:00Z",
    },
)

loaded, env = load("iforest.pyod.joblib", trusted=True, return_metadata=True)
assert env["model_class"].endswith("IForest")
assert "sklearn_version" in env
scores = loaded.decision_function(X_test)
```

Envelope fields written by `save` include `_pyod_persistence_version`, `pyod_version`, `sklearn_version`, `numpy_version`, `scipy_version`, `joblib_version`, `python_version`, `saved_at`, `model_class`, `metadata`, and `model`.

## Compatibility With Old sklearn Tree Pickles

A common legacy failure is:

```text
ValueError: node array from the pickle has an incompatible dtype
```

This can happen when sklearn changes the internal dtype of decision-tree nodes. sklearn 1.3 added the `missing_go_to_left` Tree-node field; older pickles do not contain it.

PyOD's `compat_load` is deliberately narrow:

- It realigns sklearn `Tree` node arrays to the running sklearn dtype.
- Currently, only the safely documented missing field `missing_go_to_left` is zero-filled.
- Unknown added/removed fields, kind/signedness/itemsize/shape dtype changes, or unsupported Tree state changes raise instead of guessing.
- Byte-order-only differences are accepted.
- It warns when Tree realignment occurs and recommends re-saving or re-fitting.

`load(path, trusted=True)` automatically falls through to `compat_load(path, trusted=True)` only when the initial `joblib.load` raises the documented dtype error prefix. If recovery succeeds, re-save the model with `save` in the current environment or re-fit for the most durable fix.

```python
from pyod.utils.persistence import load, save, compat_load

try:
    clf = load("legacy-iforest.joblib", trusted=True)
except ValueError as exc:
    if "node array from the pickle has an incompatible dtype" in str(exc):
        clf = compat_load("legacy-iforest.joblib", trusted=True)
    else:
        raise

save(clf, "legacy-iforest-resaved.pyod.joblib")
```

Caveat: Tree-node realignment is best-effort. Predictions on inputs with missing values can differ because the zero-filled `missing_go_to_left` value may not reflect the original training behavior. If a production incident depends on exact behavior, re-fit on the current sklearn stack.

## Strict Mode Decision Guide

Use `strict=True` when the serving environment is supposed to match the training environment exactly.

```python
clf = load("prod.pyod.joblib", strict=True, trusted=True)
```

Strict mode:

- raises on drift in `sklearn_version`, `joblib_version`, `numpy_version`, or `scipy_version`;
- accepts Python-version drift as informational;
- rejects raw legacy artifacts because they have no envelope to compare;
- rejects artifacts that required `compat_load` repair, even if the envelope versions appear to match.

Use non-strict mode for exploratory migration, then re-save in the current environment once behavior is validated.

## Raw joblib Fallback

Raw joblib remains possible:

```python
from joblib import dump, load as joblib_load

dump(clf, "clf.joblib")
clf = joblib_load("clf.joblib")  # only for trusted artifacts
```

Caveats:

- No dependency envelope is recorded.
- Raw `joblib.load` does not enforce PyOD's `trusted=True` guard.
- Raw loading returns whatever object is in the file; if the file was written by `pyod.utils.persistence.save`, raw `joblib.load` returns the envelope dict, not the model.
- Cross-sklearn compatibility and validation are your responsibility.

Prefer raw joblib only for interoperability with systems that require a raw joblib format.

## Post-Load Validation Checklist

After loading any trusted artifact:

1. Confirm expected type or interface:
   ```python
   assert hasattr(clf, "decision_function")
   assert hasattr(clf, "predict")
   ```
2. Confirm fitted attributes when using PyOD `BaseDetector` subclasses:
   ```python
   for name in ["decision_scores_", "threshold_", "labels_"]:
       assert hasattr(clf, name), name
   ```
3. Run a representative probe batch:
   ```python
   import numpy as np
   scores = clf.decision_function(X_probe)
   assert scores.shape == (X_probe.shape[0],)
   assert np.isfinite(scores).all()
   labels = clf.predict(X_probe)
   assert set(np.unique(labels)).issubset({0, 1})
   ```
4. Compare against golden scores or metric bands if you have them.
5. Re-save with `save` after successful legacy or compat migration.

## Neural Detector Caveat

Deep-learning detectors that wrap `torch.nn.Module` may need detector-specific state handling beyond this wrapper. For those, first apply `specialized-modalities` guidance for backend and model-state constraints, then use this reference only for the PyOD/joblib trust and validation boundary.
