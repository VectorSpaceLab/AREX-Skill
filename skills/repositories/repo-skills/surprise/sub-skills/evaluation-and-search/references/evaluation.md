# Evaluation API reference

This reference is self-contained for Surprise evaluation and search workflows. It assumes a `surprise.Dataset` is already loaded from a local file, dataframe, predefined folds, or a cached built-in dataset.

## Core data shapes

- A `Dataset` is the object consumed by splitters, `cross_validate`, and search classes.
- A `Trainset` is the internal training object returned by splitters or `data.build_full_trainset()`.
- A Surprise `testset` is a list of raw triples `(raw_user_id, raw_item_id, true_rating)`.
- `algo.test(testset)` returns a list of `Prediction` objects, tuple-compatible as `(uid, iid, true_r, est, details)`.
- Accuracy functions consume the full prediction list. They do not fit algorithms or create splits.

For dataset construction details, use the sibling `data-loading` sub-skill. For algorithm constructor choices and option meanings, use the sibling `prediction-algorithms` sub-skill.

## Metrics

All metric functions accept `predictions` and `verbose=True` by default. Pass `verbose=False` inside scripts/tests when you only need the returned float.

| Metric | Call | Optimized how in search | Important edge cases |
| --- | --- | --- | --- |
| Root mean squared error | `accuracy.rmse(predictions, verbose=False)` | Lower is better | Raises `ValueError("Prediction list is empty.")` on an empty list. |
| Mean squared error | `accuracy.mse(predictions, verbose=False)` | Lower is better | Same empty-list error as RMSE. |
| Mean absolute error | `accuracy.mae(predictions, verbose=False)` | Lower is better | Same empty-list error as RMSE. |
| Fraction of concordant pairs | `accuracy.fcp(predictions, verbose=False)` | Higher is better | Requires non-empty predictions and enough comparable pairs per user. It raises when no concordant/discordant denominator can be formed. |

Manual scoring pattern:

```python
from surprise import accuracy

algo.fit(trainset)
predictions = algo.test(testset)
rmse = accuracy.rmse(predictions, verbose=False)
mae = accuracy.mae(predictions, verbose=False)
```

Train-set scoring is intentionally biased but useful for diagnostics:

```python
trainset = data.build_full_trainset()
algo.fit(trainset)
train_predictions = algo.test(trainset.build_testset())
train_rmse = accuracy.rmse(train_predictions, verbose=False)
```

## One train/test split

Use `train_test_split` for one random split, not as a cross-validation iterator.

```python
from surprise.model_selection import train_test_split

trainset, testset = train_test_split(
    data,
    test_size=0.25,      # float proportion or absolute int
    train_size=None,    # complement by default
    random_state=0,
    shuffle=True,
)
algo.fit(trainset)
predictions = algo.test(testset)
```

Split-size rules:
- `test_size` and `train_size` may be floats in `(0, 1)` or positive integers.
- If either size is `None`, it becomes the complement of the other size.
- Each concrete size must be smaller than the number of ratings.
- The sum of concrete train and test sizes must not exceed the number of ratings.
- `shuffle=False` gives deterministic contiguous splits; otherwise use `random_state` for repeatability.

## CV iterators

Every CV iterator yields `(trainset, testset)` pairs from `cv.split(data)`. `cross_validate` and search classes accept either an iterator object, an integer, or `None` as the `cv` argument.

| Iterator | Constructor | Use when | Key behavior and pitfalls |
| --- | --- | --- | --- |
| `KFold` | `KFold(n_splits=5, random_state=None, shuffle=True)` | Standard k-fold evaluation | `n_splits` must be at least 2 and no greater than the number of ratings. With `shuffle=True`, fixed `random_state` makes repeated calls deterministic. |
| `ShuffleSplit` | `ShuffleSplit(n_splits=5, test_size=0.2, train_size=None, random_state=None, shuffle=True)` | Repeated random train/test samples | Folds need not cover all ratings and may overlap. Size validation is strict. |
| `RepeatedKFold` | `RepeatedKFold(n_splits=5, n_repeats=10, random_state=None)` | Multiple randomized k-fold rounds | Total folds are `n_splits * n_repeats`. A fixed seed controls the whole repeated sequence. |
| `LeaveOneOut` | `LeaveOneOut(n_splits=5, random_state=None, min_n_ratings=0)` | One test rating per user per split | Users with too few ratings may be discarded. If `min_n_ratings` is too high and no trainset can be built, it raises. |
| `PredefinedKFold` | `PredefinedKFold()` | Train/test files are already defined | Use only with `Dataset.load_from_folds(...)`. The number of folds is the number of train/test file pairs. |

Manual iterator pattern:

```python
from surprise import accuracy
from surprise.model_selection import KFold

cv = KFold(n_splits=3, random_state=0, shuffle=True)
for trainset, testset in cv.split(data):
    algo.fit(trainset)
    predictions = algo.test(testset)
    print(accuracy.rmse(predictions, verbose=False))
```

## Cross-validation

`cross_validate` orchestrates fitting, testing, metric scoring, and timing.

```python
from surprise.model_selection import KFold, cross_validate

results = cross_validate(
    algo,
    data,
    measures=["RMSE", "MAE"],
    cv=KFold(n_splits=3, random_state=0, shuffle=True),
    return_train_measures=False,
    n_jobs=1,
    verbose=False,
)
print(results["test_rmse"].mean())
```

Return keys:
- `test_<measure>`: NumPy arrays with one score per split, e.g. `test_rmse`.
- `train_<measure>`: present only when `return_train_measures=True`.
- `fit_time`: seconds spent fitting per split.
- `test_time`: seconds spent predicting/scoring per split.

`cv` semantics:
- `cv=None` means `KFold(n_splits=5)`.
- `cv=3` means `KFold(n_splits=3)`.
- A custom object is accepted if it has a `split(data)` method and is not a string.
- Anything else raises a “Wrong CV object” `ValueError`.

### `fit_and_score` semantics

`fit_and_score` is an internal helper used by `cross_validate` and search. It:
1. calls `algo.fit(trainset)` and records fit time;
2. calls `algo.test(testset)` and records test time;
3. optionally calls `algo.test(trainset.build_testset())` when train measures are requested;
4. dispatches metric names to functions in `surprise.accuracy` after lowercasing them.

Most users should call `cross_validate` or a search class rather than importing `fit_and_score` directly.

## Hyperparameter search

Use `GridSearchCV` for exhaustive combinations and `RandomizedSearchCV` for sampled combinations. Both classes evaluate algorithm constructors over CV splits and expose best-score metadata.

```python
from surprise import SVD
from surprise.model_selection import GridSearchCV

param_grid = {
    "n_epochs": [2, 5],
    "n_factors": [5],
    "lr_all": [0.002, 0.005],
    "reg_all": [0.02, 0.1],
    "random_state": [0],
}

gs = GridSearchCV(
    SVD,
    param_grid,
    measures=["rmse", "mae"],
    cv=3,
    refit=False,
    n_jobs=1,
)
gs.fit(data)
print(gs.best_score["rmse"])
print(gs.best_params["rmse"])
```

Important search attributes after `fit(data)`:
- `best_score[measure]`: best mean CV score for a measure.
- `best_params[measure]`: parameter dict that produced the best score.
- `best_index[measure]`: row index into `cv_results` for the best parameter set.
- `best_estimator[measure]`: an algorithm instance initialized with the best parameters. It is fitted on the full dataset only for the selected `refit` measure.
- `cv_results`: arrays/lists for split scores, means, standard deviations, ranks, timings, and parameters.

### Dict-valued options

Algorithm parameters that are themselves dictionaries, especially `sim_options` and `bsl_options`, must be supplied as nested dictionaries whose values are lists. Surprise expands the nested dictionary into dictionary combinations.

```python
from surprise import KNNBaseline
from surprise.model_selection import GridSearchCV

param_grid = {
    "k": [20, 40],
    "bsl_options": {
        "method": ["als", "sgd"],
        "reg": [0.02, 0.05],
    },
    "sim_options": {
        "name": ["msd", "cosine"],
        "min_support": [1, 5],
        "user_based": [False],
    },
}

gs = GridSearchCV(KNNBaseline, param_grid, measures=["rmse"], cv=3)
```

Do not pass `sim_options` or `bsl_options` as a list of already-built dictionaries; the search parser expects the nested-dict-of-lists shape.

### `refit` behavior

`refit` controls whether the best estimator is trained on the full `data` after the CV search.

| `refit` value | Behavior |
| --- | --- |
| `False` | Default. `gs.test(...)` and `gs.predict(...)` raise `ValueError`; manually fit `gs.best_estimator[measure]` before using it. |
| `True` | Refit using the first measure listed in `measures`; `gs.test` and `gs.predict` route to that fitted estimator. |
| `"rmse"`, `"mae"`, `"mse"`, or `"fcp"` | Refit using that named measure; the measure must also appear in `measures`. |

Do not use `refit=True` or a string refit measure with data loaded by `Dataset.load_from_folds(...)`; Surprise raises because a predefined-fold dataset has no single unbiased “full” dataset for refitting.

Without refit, use this pattern:

```python
gs.fit(data)
algo = gs.best_estimator["rmse"]
algo.fit(data.build_full_trainset())
```

With refit, use this pattern:

```python
gs = GridSearchCV(SVD, param_grid, measures=["rmse", "mae"], cv=3, refit="rmse")
gs.fit(data)
prediction = gs.predict("raw-user-id", "raw-item-id")
```

### RandomizedSearchCV

`RandomizedSearchCV` accepts the same search controls as `GridSearchCV`, plus:

```python
RandomizedSearchCV(
    algo_class,
    param_distributions,
    n_iter=10,
    random_state=0,
    measures=["rmse", "mae"],
    cv=3,
)
```

`param_distributions` values may be lists or distribution objects exposing `rvs`. If all values are lists, Surprise samples parameter combinations without replacement; keep `n_iter` no larger than the total number of combinations. If at least one value is a distribution object, sampling is with replacement.

## `cv_results` guide

After `fit(data)`, `cv_results` is a dictionary whose per-parameter rows can be converted to a dataframe.

```python
import pandas as pd

results_df = pd.DataFrame.from_dict(gs.cv_results)
print(results_df[["mean_test_rmse", "rank_test_rmse", "params"]])
```

Common keys:
- `split<i>_test_<measure>`: one score array per split and measure.
- `split<i>_train_<measure>`: present only when `return_train_measures=True`.
- `mean_test_<measure>` and `std_test_<measure>`: aggregate scores per parameter combination.
- `mean_train_<measure>` and `std_train_<measure>`: train aggregates when requested.
- `rank_test_<measure>`: rank 1 is best. RMSE/MSE/MAE are ranked low-to-high; FCP is ranked high-to-low.
- `mean_fit_time`, `std_fit_time`, `mean_test_time`, `std_test_time`: timing aggregates per parameter combination.
- `params`: list of parameter dictionaries, one per row.
- `param_<name>`: list of values for an individual top-level parameter.

Shape expectations:
- Each `mean_*`, `std_*`, `rank_*`, `param_*`, and `params` entry has one row per parameter combination.
- Each `split<i>_*` entry has the same row count.
- `gs.cv_results["params"][gs.best_index["rmse"]] == gs.best_params["rmse"]` should hold after a successful RMSE search.

## Unbiased tuning and evaluation split

When tuning hyperparameters, do not report the grid-search CV score as the final unbiased estimate if you selected parameters using that same data. Hold out a raw-rating set first.

```python
import random
from surprise import accuracy, SVD
from surprise.model_selection import GridSearchCV

raw_ratings = list(data.raw_ratings)
random.Random(0).shuffle(raw_ratings)

cut = int(0.9 * len(raw_ratings))
tuning_raw = raw_ratings[:cut]
holdout_raw = raw_ratings[cut:]

data.raw_ratings = tuning_raw

param_grid = {"n_epochs": [2, 5], "n_factors": [5], "random_state": [0]}
gs = GridSearchCV(SVD, param_grid, measures=["rmse"], cv=3, refit=True)
gs.fit(data)

# `refit=True` fitted the best RMSE estimator on all tuning data.
algo = gs.best_estimator["rmse"]

holdout_testset = data.construct_testset(holdout_raw)
holdout_predictions = algo.test(holdout_testset)
unbiased_rmse = accuracy.rmse(holdout_predictions, verbose=False)
```

Practical cautions:
- Make a copy of `data.raw_ratings` before shuffling or replacing it.
- Use the holdout set only after search and refit; do not inspect it while choosing parameters.
- Ensure the holdout contains enough ratings for the metrics you plan to compute. FCP needs multiple comparable predictions per user.
- For very small datasets, prefer RMSE/MAE over FCP and use explicit split counts.

## API choice checklist

- Need one quick score after a custom split? Use `train_test_split` plus `accuracy`.
- Need mean/stdev over folds? Use `cross_validate`.
- Need to inspect fold sizes or inject custom logic? Iterate a CV object manually.
- Need parameter tuning? Use `GridSearchCV` for exhaustive grids or `RandomizedSearchCV` for sampled spaces.
- Need shell-only evaluation? Use the CLI reference, but remember it does not perform search.

## Bundled scripts

- `scripts/cross_validate_smoke.py`: local-file `cross_validate` with train/test metrics.
- `scripts/cv_iterators_smoke.py`: `train_test_split`, all main CV iterators, and `PredefinedKFold` on temporary files.
- `scripts/grid_search_smoke.py`: tiny `GridSearchCV` using nested `sim_options` and `bsl_options`, `cv_results`, and `refit`.
- `scripts/unbiased_split_smoke.py`: safe holdout-before-search workflow.
- `scripts/cli_eval_smoke.py`: CLI help, missing-reader error, and happy-path local-file evaluation.
