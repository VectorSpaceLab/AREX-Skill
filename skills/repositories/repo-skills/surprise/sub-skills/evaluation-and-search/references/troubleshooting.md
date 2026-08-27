# Evaluation and search troubleshooting

Use this when metrics, splitters, cross-validation, search, or CLI evaluation fail.

## CV and split failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Wrong CV object...` | `cv` is neither `None`, an integer, nor an object with `split(data)`; strings are rejected even though they have a `split` method. | Use `cv=None`, `cv=3`, or an iterator such as `KFold(...)`, `ShuffleSplit(...)`, `LeaveOneOut(...)`, or `PredefinedKFold()`. |
| `Incorrect value for n_splits...` | `KFold(n_splits=...)` is less than 2 or greater than the number of ratings. | Lower `n_splits`, add ratings, or use `ShuffleSplit` for repeated random splits. |
| `n_splits ... should be strictly greater than 0` | `ShuffleSplit(n_splits=0)` or negative splits. | Use at least 1 split for `ShuffleSplit`. |
| `test_size` / `train_size` errors | A size is zero, negative, not smaller than the number of ratings, or train+test exceeds available ratings. | For tiny data use explicit counts, e.g. `test_size=1`, or floats in `(0, 1)` whose rounded counts fit the dataset. |
| `LeaveOneOut` cannot build any trainset | Every user has too few ratings after applying `min_n_ratings`. | Lower `min_n_ratings`, add per-user ratings, or choose `KFold` / `ShuffleSplit`. |
| `PredefinedKFold` produces no useful folds | Data was not loaded with fold files, files are missing, or train/test pairs are malformed. | Build data with `Dataset.load_from_folds([(train_path, test_path), ...], reader)` and pass `PredefinedKFold()`. |

Debugging pattern:

```python
cv = KFold(n_splits=2, random_state=0, shuffle=True)
for trainset, testset in cv.split(data):
    print(trainset.n_ratings, len(testset))
```

## Metric failures and edge cases

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Prediction list is empty.` from `rmse`, `mse`, `mae`, or `fcp` | The testset is empty, `algo.test` was not called, or filtering removed every prediction. | Check `len(testset)` before testing and `len(predictions)` before scoring. |
| `fcp` says it cannot compute on this prediction list | FCP needs comparable pairs within users. A single prediction per user or tied/non-comparable pairs can make the denominator zero. | Use RMSE/MAE/MSE for sparse one-per-user checks, or evaluate FCP only when users have at least two useful predictions. |
| Train metrics are missing from `cross_validate` results | `return_train_measures=False` (default). | Pass `return_train_measures=True`; expect extra training-set prediction time. |
| Metric names fail unexpectedly | Search and CV lower-case metric names and dispatch to functions in `surprise.accuracy`. Unknown names do not exist. | Use `"rmse"`, `"mse"`, `"mae"`, or `"fcp"`. |

## Search failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Constructor `TypeError` during `fit` | `param_grid` or `param_distributions` contains a key that the algorithm class does not accept. | Check the target algorithm constructor and remove or rename invalid keys. For example, SVD accepts `n_epochs`, `n_factors`, `lr_all`, `reg_all`, and `random_state`; it does not accept neighbor-only options like `k`. |
| `sim_options` or `bsl_options` parsing error | The option was passed as a list of dictionaries or a scalar dict instead of a nested dictionary of lists. | Use `{"sim_options": {"name": ["msd"], "user_based": [False]}}`, not `[{"name": "msd"}]`. |
| `refit cannot be used when data has been loaded with load_from_folds()` | Search was created with `refit=True` or `refit="measure"`, but the dataset came from predefined fold files. | Use `refit=False` and manually fit a chosen estimator on the desired training data, or load a non-fold dataset for refit. |
| `refit is False, cannot use test()` or `predict()` | `gs.test(...)` / `gs.predict(...)` are only available after a refit. | Create the search with `refit=True` or `refit="rmse"`, or run `algo = gs.best_estimator["rmse"]; algo.fit(data.build_full_trainset())` before using the estimator. |
| Invalid `refit` measure error | `refit="..."` names a measure not included in `measures`. | Add the measure to `measures` or change `refit` to one of the listed measure names. |
| `RandomizedSearchCV` fails when all distributions are lists | Surprise samples list-only spaces without replacement. | Keep `n_iter` no larger than the total number of parameter combinations, or provide a distribution object for at least one parameter. |
| Search is slow or noisy | Too many parameter combinations, too many folds, verbose algorithms, or parallel job overhead. | Start with `cv=2`, tiny grids, `n_jobs=1`, and algorithm `verbose=False`; then scale deliberately. |

`cv_results` sanity checks after `fit`:

```python
n = len(gs.cv_results["params"])
assert gs.cv_results["mean_test_rmse"].shape == (n,)
assert gs.cv_results["rank_test_rmse"].min() == 1
assert gs.cv_results["params"][gs.best_index["rmse"]] == gs.best_params["rmse"]
```

## CLI failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Parser error: `No algorithm was specified.` | `-algo` is omitted. | Pass one supported algorithm name, e.g. `-algo SVD`. |
| Parser error: `-reader parameter is needed.` | `-load-custom` or `-folds-files` was used without `-reader`. | Add a trusted `Reader(...)` expression matching the file columns and separator. |
| Syntax error or unexpected exception from `-params` | The CLI evaluates the raw string with Python `eval`. Quoting or Python-literal syntax is wrong. | Quote the whole dict for your shell and use Python syntax: `"{'n_epochs': 2, 'random_state': 0}"`. |
| Reader parse error on a custom file | `line_format`, `sep`, or `skip_lines` does not match the file. | Inspect a few lines; ensure the reader fields are in the actual order and separator. |
| CLI tries to prompt or download data | Built-in dataset was requested and is not cached. | For automation, use `-load-custom` with a local fixture or pre-stage the built-in dataset cache. |
| CLI command writes files unexpectedly | `--with-dump` was enabled. | Omit `--with-dump`, or set `-dump-dir` to a temporary directory. |
| Cache data disappeared | `--clean` removes the Surprise dataset cache and exits. | Avoid `--clean` unless the task is cache cleanup. |

Security note: because the CLI evaluates `-params` and `-reader`, never pass untrusted user text directly into those flags.

## Not runtime paths

Do not treat benchmark, documentation-table generation, notebook, or maintainer “run all examples” workflows as normal runtime evaluation paths. They are useful evidence for docs maintainers but are too broad, too slow, or dependency-heavy for a safe reusable skill. Use the bundled smoke scripts and API templates in this sub-skill instead.
