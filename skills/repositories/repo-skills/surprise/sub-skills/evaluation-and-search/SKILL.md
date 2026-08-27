---
name: evaluation-and-search
description: "Evaluate Surprise predictions, cross-validate algorithms, split
  data, tune hyperparameters, inspect cv_results, and run the Surprise CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Evaluation and search

Use this sub-skill when a future agent must score Surprise predictions, build train/test or cross-validation splits, run `cross_validate`, tune algorithms with `GridSearchCV` or `RandomizedSearchCV`, inspect `cv_results`, or evaluate a dataset from the `surprise` command line.

## Boundaries

In scope:
- `surprise.accuracy.rmse`, `mse`, `mae`, and `fcp` on `Prediction` lists.
- `train_test_split`, `KFold`, `ShuffleSplit`, `RepeatedKFold`, `LeaveOneOut`, and `PredefinedKFold`.
- `cross_validate` and the minimal `fit_and_score` semantics needed to reason about returned measures and timings.
- `GridSearchCV`, `RandomizedSearchCV`, `best_score`, `best_params`, `best_estimator`, `best_index`, and `cv_results`.
- A safe unbiased tuning/evaluation split workflow.
- The `surprise` CLI for evaluation on built-in, custom-file, or predefined-fold datasets.

Out of scope:
- Algorithm internals, baseline formulas, and similarity formulas. For algorithm choice or options, use the sibling [prediction-algorithms](../prediction-algorithms/) sub-skill.
- Dataset parsing depth, raw/inner id conversion, and built-in dataset cache management. For those, use the sibling [data-loading](../data-loading/) sub-skill.
- Top-N recommendation, precision/recall@k, dump/load, and exported prediction analysis. Use the sibling [recommendation-and-analysis](../recommendation-and-analysis/) sub-skill.
- Benchmark table generation, documentation table generation, notebooks, and maintainer “run all examples” harnesses; they are not runtime evaluation paths.

## Read path

1. Start with [references/evaluation.md](references/evaluation.md) for API workflows and code templates.
2. Read [references/cli-reference.md](references/cli-reference.md) for `surprise` command-line evaluation and safe quoting.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when a split, metric, search, or CLI call fails.
4. Use the bundled scripts as tiny, deterministic smoke checks when validating an environment or demonstrating a workflow:
   - `python scripts/cross_validate_smoke.py`
   - `python scripts/cv_iterators_smoke.py`
   - `python scripts/grid_search_smoke.py`
   - `python scripts/unbiased_split_smoke.py`
   - `python scripts/cli_eval_smoke.py`

The scripts create temporary local rating files and do not download built-in datasets.

## Task routing quick map

| User task | Use | Key reference |
| --- | --- | --- |
| “Compute RMSE/MAE/MSE/FCP for predictions” | `accuracy.<metric>(predictions, verbose=False)` | [Metrics](references/evaluation.md#metrics) |
| “Split once into train/test” | `train_test_split(data, test_size=..., random_state=...)` | [One train/test split](references/evaluation.md#one-train-test-split) |
| “Run k-fold CV” | `cross_validate(algo, data, cv=KFold(...), measures=[...])` | [Cross-validation](references/evaluation.md#cross-validation) |
| “Manually control folds” | Iterate `for trainset, testset in cv.split(data)` | [CV iterators](references/evaluation.md#cv-iterators) |
| “Tune hyperparameters” | `GridSearchCV` or `RandomizedSearchCV` | [Search](references/evaluation.md#hyperparameter-search) |
| “Inspect all grid-search results” | `gs.cv_results`, optionally `pandas.DataFrame.from_dict` | [cv_results](references/evaluation.md#cv_results-guide) |
| “Tune, then report unbiased performance” | Hold out raw ratings before search; fit on tuning set; test on untouched holdout | [Unbiased split](references/evaluation.md#unbiased-tuning-and-evaluation-split) |
| “Evaluate from shell” | `surprise -algo ... -load-custom ... -reader ... -n-folds ...` | [CLI reference](references/cli-reference.md) |

## Safety notes

- Prefer local files, dataframes, or predefined folds for examples and tests. `Dataset.load_builtin()` may prompt for or download data if the cache is missing.
- Keep `n_jobs=1` while debugging custom algorithms, tiny examples, or failures; increase parallelism only after a serial run is correct.
- Use explicit `random_state` or CLI `-seed` for reproducible folds and algorithm initialization.
- The CLI evaluates Python expressions supplied to `-params` and `-reader`. Only pass trusted strings.
- Search objects expose `test()` and `predict()` only when `refit` is enabled; without `refit`, manually fit `best_estimator[measure]` before using it.
