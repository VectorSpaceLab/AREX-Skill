# Evaluation API reference

This reference records the public signatures and observed behavior for the
MOABB 1.5 development package used during extraction. Use it as an API map;
choose the protocol from [workflows](workflows.md) before copying knobs.

## Public imports and signatures

```python
from moabb.evaluations import (
    CrossSessionEvaluation,
    CrossSubjectEvaluation,
    CrossSubjectMode,
    WithinSessionEvaluation,
    WithinSubjectEvaluation,
)
from moabb.evaluations.splitters import (
    CrossDatasetSplitter,
    CrossSessionSplitter,
    CrossSubjectSplitter,
    LearningCurveSplitter,
    WithinSessionSplitter,
    WithinSubjectSplitter,
)
from moabb.datasets.base import CacheConfig
from moabb import benchmark
```

The verified constructors are:

```text
WithinSessionEvaluation(
    paradigm, datasets=None, random_state=None, n_jobs=1,
    overwrite=False, error_score="raise", suffix="", hdf5_path=None,
    additional_columns=None, return_epochs=False, return_raws=False,
    mne_labels=False, n_splits=None, cv_class=None, cv_kwargs=None,
    groups=None, save_model=False, cache_config=None, optuna=False,
    time_out=900, verbose=None, codecarbon_config=None,
)
CrossSessionEvaluation(same arguments)
WithinSubjectEvaluation(same arguments)
CrossSubjectEvaluation(*args, cs_mode=CrossSubjectMode.TRAIN, **kwargs)
```

`CrossSubjectEvaluation` accepts the common `BaseEvaluation` keyword arguments
above, plus the `cs_mode` enum/string. Its mode is converted to splitter
calibration settings; do not combine a non-`TRAIN` mode with manual
`cv_kwargs["calibration_size"]` or `cv_kwargs["calibration_labeled"]`.

All four evaluations expose:

```python
results = evaluation.process(
    pipelines: dict[str, sklearn.base.BaseEstimator],
    param_grid: dict[str, dict] | None = None,
    postprocess_pipeline: sklearn.base.BaseEstimator | None = None,
)  # pandas.DataFrame
```

`pipelines` must be a dictionary of sklearn estimators. Grid-search keys must
match pipeline names. `postprocess_pipeline` is fixed (it is transformed, not
fit, by the evaluation). The lower-level `evaluate(dataset, pipelines,
param_grid, process_pipeline, postprocess_pipeline=None)` yields result
mappings for one dataset; ordinary callers should use `process()`.

## Evaluation knobs

| Argument | Default | Effect and caution |
|---|---:|---|
| `datasets` | paradigm datasets | A list or one `BaseDataset`; incompatible datasets are removed, and an empty remainder errors. |
| `random_state` | `None` | Seed for shuffle/permutation behavior. Set an integer for repeatable folds. |
| `n_jobs` | `1` | Joblib fitting parallelism. Start at 1; each fold can hold a fitted pipeline and large arrays. |
| `overwrite` | `False` | Reuse matching result rows when false; true truncates the selected HDF5 result file at construction. |
| `error_score` | `"raise"` | A numeric fallback can preserve a run after scoring/fitting `ValueError`; `"raise"` is safer for first debugging. |
| `suffix` | `""` | Adds `_suffix` to the result filename and separates protocol/configuration variants. |
| `hdf5_path` | `None` | Base result/model directory. With none, MOABB uses its configured result location. |
| `additional_columns` | `None` | Result columns to preserve; splitter metadata columns are added automatically for learning curves. |
| `return_epochs` | `False` | Request MNE Epochs. Some pipelines require them automatically. |
| `return_raws` | `False` | Request raw objects; only use if the selected pipeline requires it. |
| `mne_labels` | `False` | Keep original labels when returning epochs; it is invalid unless `return_epochs=True`. |
| `n_splits` | `None` | Within evaluations use this as inner fold count; cross-subject uses GroupKFold when set, otherwise LOSO. |
| `cv_class` | evaluation default | Stock sklearn CV class or `LearningCurveSplitter`. Confirm it accepts the supplied kwargs. |
| `cv_kwargs` | `None` | Arguments passed to `cv_class`; callable values can be resolved from metadata. |
| `groups` | `None` | Column/list/callable forwarded to group-aware custom CV. It does not make a non-group-aware CV safe by itself. |
| `save_model` | `False` | Save each fitted fold model under the HDF5 base path; set `hdf5_path` explicitly. |
| `cache_config` | `None` | Dataset raw/epoch/array cache policy; see below. |
| `optuna` | `False` | Optional search backend; construction raises `ImportError` if unavailable. |
| `time_out` | `900` | Optuna cutoff seconds; ignored with `optuna=False` (and warns if changed). |
| `verbose` | `None` | Overrides MOABB logging level. |
| `codecarbon_config` | package defaults | Optional emissions tracker configuration; not part of the core CPU scope. |

## Splitter signatures

```text
WithinSessionSplitter(
    n_folds=5, shuffle=True, random_state=None,
    cv_class=StratifiedKFold, groups=None, **cv_kwargs
)
WithinSubjectSplitter(
    n_folds=5, shuffle=True, random_state=None,
    cv_class=StratifiedKFold, groups=None, **cv_kwargs
)
CrossSessionSplitter(
    cv_class=LeaveOneGroupOut, shuffle=False, random_state=None,
    groups="session", **cv_kwargs
)
CrossSubjectSplitter(
    cv_class=LeaveOneGroupOut, groups="subject", random_state=None,
    calibration_size=0.0, calibration_labeled=False, **cv_kwargs
)
CrossDatasetSplitter(
    cv_class=LeaveOneGroupOut, groups="dataset", group_column=None,
    random_state=None, **cv_kwargs
)
LearningCurveSplitter(
    data_size, n_perms, test_size=0.2, random_state=None,
    n_splits=None, shuffle=True
)
```

For every splitter, `split(y, metadata)` yields arrays of index labels. The
metadata must have `subject` and `session` columns for the standard splitters.
Group specifications are a string column, a list/tuple of columns joined into a
compound group, or a callable `metadata -> array`. `CrossSubjectSplitter` can
yield `(train, calibration, test)` when `calibration_size > 0`; ordinary mode
yields `(train, test)`. `CrossDatasetSplitter` records `test_dataset` and
`train_datasets` metadata and retains deprecated `group_column` compatibility.

## CrossSubjectMode values

| Mode | Calibration | Labels routed | Scoring |
|---|---:|---|---|
| `TRAIN` (`"train"`) | 0% | no | normal held-out target block |
| `TRAIN_TRIALWISE` (`"train_trialwise"`) | 0% | no | one target trial at a time; `accuracy` or `roc_auc` only |
| `TRAIN_AND_TARGET_UNLABELED_20P` | 20% | no | remaining target trials |
| `TRAIN_AND_TARGET_UNLABELED_50P` | 50% | no | remaining target trials |
| `TRAIN_AND_TARGET_UNLABELED_FULL` | 100% | no | the same target block is adapted and scored; transductive |
| `TRAIN_AND_TARGET_LABELED_20P` | 20% | yes | remaining target trials |
| `TRAIN_AND_TARGET_LABELED_50P` | 50% | yes | remaining target trials |

A labeled calibration fraction above 0.5 is rejected. Calibration is only
routed to pipeline steps that opt in through sklearn metadata routing; it is not
silently added to source training. Record the mode with the result because
scores from different target-access budgets are not comparable as one claim.

## Result, cache, and model paths

`Results` stores one file per paradigm/evaluation/suffix below the selected
base directory:

```text
<hdf5_path>/results/<ParadigmClass>/<EvaluationClass>/results[_<suffix>].hdf5
```

`evaluation.get_results()` and `evaluation.process(...)` return a DataFrame.
Typical columns are `dataset`, `subject`, `session`, `pipeline`, `score`,
`time`, `n_samples`, `n_samples_test`, `n_classes`, and `n_channels`; a
multi-metric scorer adds `score_<metric>`. Learning curves add `data_size` and
`permutation`. `benchmark()` additionally adds `paradigm` and `evaluation`.

Model saving uses a parallel tree below `hdf5_path`:

```text
Models_<Evaluation>/<dataset-code>/<subject>/<session>/<pipeline>/fitted_model_<fold>.pkl
GridSearch_<Evaluation>/...                 # when a grid search is active
```

For cross-session and cross-subject evaluations the session path is omitted.
If no `hdf5_path` is supplied, model saving cannot produce a path and MOABB
warns rather than creating a portable model bundle.

`CacheConfig` is a dataclass accepted as an object or dictionary:

```python
CacheConfig(
    save_raw=False, save_epochs=False, save_array=False,
    use=False,
    overwrite_raw=False, overwrite_epochs=False, overwrite_array=False,
    path=None, verbose=None,
)
```

`CacheConfig.make(None|dict|CacheConfig)` normalizes the value. `use=True`
reads disk cache when available; `save_*` controls writes and `overwrite_*`
reprocesses the selected cached stage. This cache is distinct from HDF5 result
rows and must not be used as a substitute for a unique result suffix.

## Benchmark signature

```text
benchmark(
    pipelines="./pipelines/", evaluations=None, paradigms=None,
    results="./results/", overwrite=False, output="./benchmark/",
    suffix="", n_jobs=-1, plot=False, contexts=None,
    include_datasets=None, exclude_datasets=None, n_splits=None,
    cache_config=None, optuna=False, codecarbon_config=None,
) -> pandas.DataFrame
```

The wrapper recognizes `WithinSession`, `CrossSession`, and `CrossSubject`.
It parses a YAML directory/single file or a list of dictionaries with
`name`, `pipeline`, and `paradigms`. It supplies `random_state=42` to the
underlying evaluations, filters by `paradigms`, and writes analysis output to
`output`; `plot=True` delegates plotting and therefore needs the analysis
surface and a suitable headless/display setup. `include_datasets` and
`exclude_datasets` are mutually exclusive homogeneous lists of dataset codes
or dataset objects; duplicates and incompatible selections are rejected or
skipped with warnings. The default `n_jobs=-1` is intentionally not the
starting point for a constrained reproducibility check.
