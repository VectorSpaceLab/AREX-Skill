# Cross-cutting auto-sklearn troubleshooting

Use this root reference for installation, import, and environment failures before loading a workflow-specific sub-skill. For estimator run failures, data/metric errors, parallelism issues, custom component problems, or metadata-script maintenance, route to the nearest sub-skill troubleshooting file afterward.

## Import and dependency triage

Run these checks in the Python environment that will execute the user's task:

```bash
python -m pip check
python -I -c "import autosklearn; print(autosklearn.__version__)"
python -I -c "import autosklearn.classification, autosklearn.regression, autosklearn.metrics"
```

If those pass, route to the workflow sub-skill. If they fail, diagnose with the table below.

| Symptom or message fragment | Likely cause | Safe response |
|---|---|---|
| `ModuleNotFoundError: No module named 'autosklearn'` | Package not installed in the active Python environment. | Install `auto-sklearn` into the environment that will run the task, then rerun `pip check` and the import probes. |
| `Mandatory package ... not found` from `autosklearn.util.dependencies` | auto-sklearn imported but its runtime dependency verifier could not find a required distribution. | Install/repair the missing dependency in the same environment; do not proceed to estimator workflows until the import probe passes. |
| `found ... version ... but requires ...` | Dependency version violates auto-sklearn's runtime requirement check. | Use a clean environment and install a compatible dependency set instead of forcing a single package upgrade in a shared environment. |
| `ValueError: numpy.dtype size changed` or ConfigSpace import ABI failure | Compiled ConfigSpace/scikit-learn/pyrfr extension was built against an incompatible NumPy ABI. | Reinstall a compatible wheel set in a clean environment. For older auto-sklearn/ConfigSpace stacks, pinning NumPy below 2 is often required. |
| `AttributeError: module 'pandas.core.dtypes.common' has no attribute 'is_datetime_or_timedelta_dtype'` or similar pandas API removal | The inspected 0.16.0dev stack expects a pandas 1.x API surface; pandas 2.x removed validator helpers used by the feature-validation path. | Pin pandas to a compatible 1.5.x release for this stack, or re-run the bundled validator native checks before promising DataFrame workflows on a newer pandas. |
| Import errors involving `pyrfr`, `ConfigSpace`, `smac`, or segmentation faults | Compiled dependency wheel/build mismatch, missing compiler, missing SWIG, or unsupported platform/Python. | Prefer a Linux environment with package-supported Python. Install a C++11 compiler and SWIG if source builds are required; verify `import pyrfr.regression as reg; reg.default_data_container(64)`. |
| `Detected unsupported operating system` | The package is Linux-oriented and rejects unsupported OS paths. | Use Linux, WSL/VM/container, or another package-supported environment. Do not present Windows/macOS as verified for this repo skill. |
| `Unsupported Python version` | Python is below the package minimum or outside the dependency wheel set. | Use a supported Python version for the selected auto-sklearn release; older releases are commonly safest on Python 3.7-3.9 era stacks. |
| `pkg_resources` deprecation warning | auto-sklearn imports `pkg_resources` for dependency verification and newer setuptools warns. | Treat as non-fatal if imports and runtime checks pass. Pin packaging tools only if the warning becomes an error in the user's environment. |
| `No module named autosklearn.automl_common` when working from source | Source checkout submodule was not initialized or packaged correctly. | For source-maintenance tasks, check submodule status; for ordinary package use, install the published package or a complete source distribution. |

## Build prerequisites

If the user's install must build dependencies from source, check for:

- Linux host or Linux container/VM.
- Python version supported by the target auto-sklearn release.
- C++11 compiler (`gcc`/`g++` or equivalent).
- SWIG for `pyrfr` builds when a compatible wheel is unavailable.
- Enough disk for compiled wheels and auto-sklearn temporary model artifacts.

Prefer creating a clean environment over mutating a shared one, because auto-sklearn pins older compiled ML dependencies tightly.

## Routing after imports work

- Estimator class choice, `fit`, `predict`, `refit`, temporary folders, dummy-only results: [estimators troubleshooting](../sub-skills/estimators/references/troubleshooting.md).
- pandas/NumPy/sparse/list inputs, `feat_type`, target encoding, `dataset_compression`, custom scorers, resampling: [data-metrics-validation troubleshooting](../sub-skills/data-metrics-validation/references/troubleshooting.md).
- `n_jobs`, Dask, SMAC/search callbacks, ensembles, disk growth, `leaderboard`, `show_models`, `performance_over_time_`: [search-and-parallelism troubleshooting](../sub-skills/search-and-parallelism/references/troubleshooting.md).
- Custom component properties, ConfigSpace, registry functions, include/exclude IDs: [custom-components troubleshooting](../sub-skills/custom-components/references/troubleshooting.md).
- `metadata_directory`, AutoSklearn2 selector/portfolio caches, ASLib metadata files, metadata scripts, submodule and focused repo tests: [metadata-maintenance troubleshooting](../sub-skills/metadata-maintenance/references/troubleshooting.md).

## Privacy and reproducibility reminder

Do not copy local environment paths, activation commands, private cache directories, or machine-specific install logs into user-facing code. Report public package versions, import names, and reproducible dependency constraints instead.
