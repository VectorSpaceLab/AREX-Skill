# Evaluation troubleshooting

Use the symptom → likely cause → check → recovery sequence. Keep the
protocol and information budget unchanged while repairing runtime problems.

| Symptom | Likely cause | Check | Recovery |
|---|---|---|---|
| `ImportError` for MOABB/MNE/sklearn/pyRiemann | Package or optional base dependency is missing | Run the root skill's import check and import `moabb.evaluations`, `moabb.datasets.fake`, and the selected paradigm | Repair the supported install; do not add deep-learning/Optuna/CodeCarbon extras unless the workflow needs them. |
| `ImportError: Optuna is not available` | `optuna=True` without the optional search packages | Inspect `optuna_available` or retry with `optuna=False` | Install the approved optional dependency or use ordinary grid/no search; keep the choice in the run record. |
| CodeCarbon import/tracker failure | Optional emissions dependency/configuration is unavailable | Remove `codecarbon_config` and confirm the core evaluation works | Treat emissions as optional; do not block a CPU score on it. |
| `No datasets left after paradigm and evaluation checks` | Paradigm mismatch or protocol needs more sessions/subjects | Print each dataset's `code`, `n_sessions`, `subject_list`; call `paradigm.is_valid(ds)` and `evaluation.is_valid(ds)` | Use the sibling dataset/paradigm routes to select compatible data, or change the claim. Do not pad metadata to satisfy a protocol. |
| Cross-session says at least 2 sessions | Dataset has one usable session or selection filtered sessions | Inspect `dataset.n_sessions`, selected sessions, and metadata session values | Use a multi-session dataset or choose within-session/within-subject only when that matches the claim. |
| Cross-subject says at least 2 subjects | Only one subject remains after selection | Inspect `dataset.subject_list` and metadata subject values | Select at least two subjects; for a single subject report only within-subject protocols. |
| `ValueError` from stratified CV about class counts | Too few examples in a class for the requested folds or curve size | Count labels per subject/session; compare with `n_splits` or `data_size` | Reduce folds/curve sizes, add data, or use a justified group/custom CV. Do not set `error_score` to hide split construction errors. |
| Learning curve rejects `data_size` | Missing `policy`/`value`, unsupported policy, non-increasing values, invalid ratio, or too-large per-class value | Check policy is `ratio` or `per_class`; values strictly increase; `n_perms` has matching length and non-increasing values | Correct the configuration. A one-class training subset is skipped with a warning; report missing points. |
| Cross-subject score unexpectedly high | Subject leakage or a target-aware mode was mistaken for source-only | Materialize `CrossSubjectSplitter`; compare train/test subject sets; record `cs_mode` and calibration columns | Use default `CrossSubjectMode.TRAIN`, group by subject, fit preprocessing inside the pipeline, and rerun with a new suffix. |
| Cross-subject mode rejects manual calibration kwargs | `cs_mode` and `cv_kwargs` describe two different transfer protocols | Inspect `cs_mode`, `calibration_size`, and `calibration_labeled` | Choose one: a named `CrossSubjectMode`, or manual calibration kwargs with default `TRAIN`. |
| Trialwise mode rejects scorer or scores whole blocks | Trialwise mode supports only built-in `accuracy`/`roc_auc` and uses frozen leave-one-out predictions | Check the paradigm's `scoring` and the pipeline's response method | Select a supported scorer or use blockwise `TRAIN`; never silently substitute `scoring=None`. |
| `groups` has no effect or warning appears | Custom sklearn CV does not consume `groups`, or group spec names a missing metadata column | Inspect `issubclass(cv_class, GroupsConsumerMixin)` behavior and metadata columns | Use a group-aware CV class and a valid string/list/callable group spec. For cross-subject use `groups="subject"` by default. |
| Unexpected subject-session folds | A compound grouping changed the holdout unit | Print the unique values of `metadata[list(groups)]` and inspect test fold metadata | Use `groups="subject"` for subject transfer or explicitly document `groups=["subject", "session"]` as subject-session transfer. |
| `mne_labels` validation error | Original labels requested without MNE Epochs | Inspect `return_epochs` | Set `return_epochs=True` only for an epoch-consuming pipeline, or leave `mne_labels=False`. |
| Pipeline shape/fit error | Paradigm output and estimator input do not agree, or preprocessing was fit outside CV | Print `X.shape`, `y.shape`, metadata length, and pipeline steps; check sibling pipeline route | Build the preprocessing in the sklearn pipeline and choose `return_epochs`/`return_raws` only as needed. Run one fold with `error_score="raise"`. |
| Empty or repeated results despite `overwrite=False` | A matching pipeline/process digest was cached, or result path/suffix was reused | Call `evaluation.get_results()`, inspect HDF5 path and `suffix`, and compare pipeline names/params | Reuse intentionally, or select a new suffix/base directory. Do not use `overwrite=True` on a shared result file. |
| HDF5 lock, “unable to open file,” or cache collision | Two processes write the same result/data cache, stale writer, filesystem lock, or identical run identity | Stop competing jobs; identify the exact base path and result file; check for a stale process and filesystem write permission | Preserve the file, use one writer and `n_jobs=1`; rerun with a unique base/suffix. If corrupt/empty, copy it aside and use a fresh result path; overwrite only an approved disposable file. |
| Result HDF5 exists but DataFrame is empty | Incomplete/empty cache state or digest mismatch | `evaluation.get_results()` and `Results.to_dataframe(...)`; compare pipeline/process objects and expected dataset code | The parallel path can recompute an empty cache state; otherwise choose a fresh suffix and rerun. Do not infer “zero performance.” |
| Saved models are missing | `save_model=True` but `hdf5_path=None`, or run never reached a fitted fold | Check logs and the model path under `Models_<Evaluation>`/`GridSearch_<Evaluation>` | Set an explicit writable `hdf5_path`, use a unique suffix, and rerun. Verify the pipeline actually fits before enabling model persistence. |
| Parallel run runs out of memory or differs during diagnosis | `n_jobs=-1` multiplies folds, grids, and loaded arrays | Check worker count, grid size, data shape, and process memory | Return to `n_jobs=1`; bound the dataset/pipeline/grid, then increase cautiously. Keep the same `random_state`. |
| `error_score` appears in result rows | Fit or scoring raised a `ValueError` and fallback was requested | Filter `is_error` before aggregation where available and inspect logs/traceback | Prefer `error_score="raise"` for diagnosis; fix data/pipeline/protocol. A numeric fallback is not a successful score. |
| Benchmark says no compatible paradigms/datasets | YAML `paradigms` names do not match exported classes, or include list has no compatible code | Parse the pipeline config, print generated paradigm names and dataset codes | Correct config/selection; start with one known compatible fake/local dataset. Do not trigger all catalog downloads to discover a typo. |
| Benchmark has duplicate pipeline-name error | Two YAML files use the same `name` for one paradigm | List parsed configs and names | Rename the pipeline entries; stable names also make cache identity and comparison clearer. |
| Benchmark unexpectedly downloads or takes hours | Real catalog defaults and all three evaluation types were selected | Inspect `evaluations`, `paradigms`, include/exclude selection, and pipeline directory | Stop and rerun bounded: one protocol, one dataset, `plot=False`, `n_jobs=1`, and an explicit data/download approval. |
| Plot or output failure after a successful evaluation | `plot=True`, headless Matplotlib, or output directory is not writable | Retry with `plot=False`; check output permissions and backend | Keep evaluation separate from analysis; route plotting to the analysis skill and use a non-interactive backend when approved. |

## Cache collision recovery procedure

1. Stop other MOABB writers targeting the same result or data-cache path.
2. Record the exact evaluation class, paradigm, dataset code, pipeline names,
   suffix, `hdf5_path`, `cache_config`, and whether model saving was active.
3. Copy the HDF5 file aside if it may contain useful rows; do not delete user
   data or a dataset cache as a first reaction.
4. Read with `evaluation.get_results()` or `Results.to_dataframe()` if safe.
   An empty DataFrame is incomplete state, not evidence of no score.
5. Re-run in a new run-specific base path and suffix with `n_jobs=1` and
   `overwrite=False`. If the old file is explicitly disposable, `overwrite=True`
   may initialize that isolated path.
6. Compare row identities and protocol metadata before combining results. Never
   merge source-only and target-calibration modes without a protocol column.

## Network and optional boundaries

A dataset constructor or paradigm `get_data()` may download missing data. This
route does not authorize network access. Use fake data for smoke checks and
route data directory/provider/authentication failures to dataset management.
Long real-data benchmark examples, deep-learning pipelines, Optuna search,
CodeCarbon tracking, plotting, and paper-result tables are not core CPU smoke
checks. A skipped optional path is not a verified pass; record it as untested.
