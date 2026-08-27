# Cross-cutting troubleshooting

## Start with the right sub-skill

Many tslearn failures are workflow-specific. Before debugging the code itself, route the issue to the sub-skill that owns the task family:

- data prep and conversions -> `sub-skills/data-preparation/`
- metrics/backends/barycenters -> `sub-skills/metrics-backends/`
- clustering -> `sub-skills/clustering/`
- supervised models -> `sub-skills/supervised-models/`
- forecasting -> `sub-skills/forecasting/`
- matrix profile / persistence -> `sub-skills/analysis-and-persistence/`

## Install and import failures

**Symptoms**
- `ModuleNotFoundError: No module named 'tslearn'`
- imports succeed in one shell but fail in another
- editable installs or local checkouts appear stale

**Fix**
1. Re-run the root smoke helper: `python scripts/check_tslearn_env.py`
2. Confirm the active Python is the one you installed tslearn into.
3. Reinstall tslearn if necessary with `python -m pip install tslearn` or `python -m pip install -e .` from a checkout.
4. Use `python -m pip check` if the environment has dependency conflicts.

## Optional dependency failures

**Symptoms**
- `ImportError` mentioning pandas, stumpy, h5py, keras, torch, or cesium
- a route works for the base package but not for an optional format/backend

**Fix**
- Install the missing package only for the workflow that needs it.
- Do not treat a CPU-only import as proof that a tensor/autodiff or GPU path is ready.
- Use the owning sub-skill's troubleshooting page for exact recovery steps.

## Shape and data-layout failures

**Symptoms**
- `ValueError` about equal-length input, invalid shapes, or mismatched timestamps
- `TimeSeriesMLP*` fails on ragged input
- converters appear to change the data layout unexpectedly

**Fix**
- Normalize with `to_time_series_dataset(...)` first.
- Resample or pad before equal-length-only workflows.
- Check the sub-skill-specific API reference for the expected `(n_ts, sz, d)` or DataFrame layout.

## Backend confusion

**Symptoms**
- `tslearn.backend.Backend("torch")` fails because torch is missing
- `LearningShapelets` fails because Keras chose the wrong backend
- CUDA is available but the workflow still needs CPU-level correctness checks

**Fix**
- Treat NumPy as the baseline backend unless the workflow explicitly needs torch tensors or gradients.
- For shapelets, set `KERAS_BACKEND` before the first `keras` import.
- For GPU acceleration questions, first prove the CPU path is correct, then confirm whether the optional CUDA path is actually required.

## Dataset download and cache failures

**Symptoms**
- UCR/UEA download warnings
- cached datasets appear to be missing
- the same dataset is re-downloaded repeatedly

**Fix**
- Use `CachedDatasets` for deterministic offline samples.
- Check `UCR_UEA_datasets(root_dir=...)`, `XDG_DATA_HOME`, and `use_cache`.
- Treat network-dependent downloads as optional; do not block a local smoke check on them.

## Persistence failures

**Symptoms**
- `to_hdf5` or `from_hdf5` raises `ImportError`
- an unfitted estimator raises `NotFittedError` on save
- a round trip changes predictions or fitted attributes

**Fix**
- Fit the estimator first.
- Use JSON or Pickle if HDF5 support is unavailable.
- Install h5py only when you need the HDF5 path.

## Use the bundled smoke helpers

If you need a fast sanity check instead of a full test run, prefer the sub-skill smoke helpers:

- `python sub-skills/data-preparation/scripts/data_preparation_smoke.py`
- `python sub-skills/metrics-backends/scripts/metrics_smoke.py all`
- `python sub-skills/clustering/scripts/clustering_smoke.py`
- `python sub-skills/supervised-models/scripts/supervised_smoke.py --mode all`
- `python sub-skills/forecasting/scripts/forecasting_smoke.py`
- `python sub-skills/analysis-and-persistence/scripts/analysis_smoke.py`
