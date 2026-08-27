# Cross-cutting MOABB troubleshooting

Diagnose in this order: active interpreter → package imports and versions →
selected dataset/data boundary → paradigm shapes/events → evaluation protocol
and storage → analysis metric/output. Keep the first exception and the exact
selection parameters; do not mask failures with `error_score` or a different
protocol.

| Symptom | Likely cause | Check | Recovery |
|---|---|---|---|
| `ModuleNotFoundError: moabb` or imports come from an unexpected checkout | Wrong Python or incomplete install | `python -c "import sys, moabb; print(sys.executable, moabb.__version__, moabb.__file__)"` and `python -m pip check` | Install MOABB into the same interpreter used for the run; avoid relying on `PYTHONPATH` or a stale editable checkout |
| Import fails inside `mne`, `mne_bids`, `pyriemann`, or `sklearn` | Base dependency mismatch | Run the root environment helper, then import the named module individually | Repair the supported base environment; install only the optional extra that owns the requested feature |
| A request unexpectedly starts a download | Missing local subject/session data or a real dataset method was called | Identify whether `data_path()`/`get_data()` is being called and inspect the configured MNE data root | Switch to `FakeDataset`/local BIDS for offline work, or obtain explicit network/license/storage approval |
| Dataset is invalid for a paradigm | Task family, event labels, interval, channels, or session requirements disagree | Print `dataset.paradigm`, `dataset.event_id`, `dataset.interval`, and call `paradigm.is_valid(dataset)` | Choose a compatible paradigm/dataset or pass an evidence-backed event subset; do not coerce labels silently |
| Pipeline has shape or fit errors | A 3-D epoch array was passed directly to a 2-D estimator, or a transform was fitted outside CV | Inspect `X.shape`, `y.shape`, estimator tags, and pipeline steps | Add the correct transformer (`LogVariance`, `Vectorizer`, CSP/covariance, or `FilterBank`) inside the sklearn pipeline |
| Reported score is implausibly high | Subject/session leakage or target-aware transfer mode | Inspect train/test group ids and `CrossSubjectMode`; record all preprocessing steps | Use the correct group-aware evaluation and rerun with a new result suffix |
| HDF5 result collision or corrupted cache | Concurrent writers, reused suffix/path, or interrupted run | Stop writers; inspect result path and file lock; preserve a copy | Use a unique writable `hdf5_path`/suffix and rerun; use `overwrite=True` only when the old result is disposable |
| Plotting fails over SSH/CI | Interactive Matplotlib backend or unwritable output | Check `MPLBACKEND` and output directory | Set `MPLBACKEND=Agg` before importing plotting modules and write to an existing writable directory |
| Chance reference disagrees with the metric | Binary ROC-AUC and multiclass accuracy were conflated | Confirm paradigm scorer, `n_classes`, `samples_test`, and score semantics | Use 0.5 for a balanced binary AUC null, `1/n_classes` for multiclass accuracy, and adjusted thresholds only for valid count/proportion data |
| Optional Plotly, Optuna, or CodeCarbon path fails | Extra was not installed or feature is outside core scope | Import the optional package and inspect the requested flag/config | Install the named extra only with approval, or disable the optional feature and state the limitation |
| A real result cannot be reproduced | Dataset version/cache, seed, pipeline, protocol, or optional settings were not recorded | Compare dataset/provider/path, subjects/sessions, random state, pipeline config, evaluation, and result suffix | Recreate the same data and configuration; do not compare scores with different information budgets |

## Safety boundaries

MOABB's data methods can contact external providers, prompt for license
acceptance, create caches, and write BIDS or HDF5 outputs. Keep network,
credential, large-data, and destructive operations explicit. The bundled runtime
helpers are offline-first and do not download data. Optional deep-learning and
accelerator capability is not claimed by the core CPU graph.
