# Surprise package overview

Surprise (`scikit-surprise`) is a compact explicit-feedback recommendation library. Its core workflow is:

1. load ratings into a `Dataset`,
2. materialize a `Trainset`,
3. choose and fit a prediction algorithm,
4. evaluate or tune predictions,
5. turn predictions into recommendations or serialized artifacts.

## Main modules

| Module | Purpose | Common route |
| --- | --- | --- |
| `surprise.reader` | Parse rating records from delimited files or build reader metadata for dataframe/fold loading. | [`sub-skills/data-loading/`](../sub-skills/data-loading/SKILL.md) |
| `surprise.dataset` | Load custom files, dataframes, predefined folds, and built-in datasets; expose dataset constructors and raw ratings. | [`sub-skills/data-loading/`](../sub-skills/data-loading/SKILL.md) |
| `surprise.trainset` | Hold the internal trainset view, raw/inner id conversion helpers, and anti-testset/build-testset utilities. | [`sub-skills/data-loading/`](../sub-skills/data-loading/SKILL.md) and [`sub-skills/recommendation-and-analysis/`](../sub-skills/recommendation-and-analysis/SKILL.md) |
| `surprise.prediction_algorithms` | Built-in predictors, `AlgoBase`, baseline options, similarity options, and `predict()`/`test()` behavior. | [`sub-skills/prediction-algorithms/`](../sub-skills/prediction-algorithms/SKILL.md) |
| `surprise.accuracy` | RMSE, MSE, MAE, and FCP scoring for prediction lists. | [`sub-skills/evaluation-and-search/`](../sub-skills/evaluation-and-search/SKILL.md) |
| `surprise.model_selection` | Train/test splitters, cross-validation iterators, `cross_validate`, and hyperparameter search. | [`sub-skills/evaluation-and-search/`](../sub-skills/evaluation-and-search/SKILL.md) |
| `surprise.dump` | Serialize and load predictions or fitted algorithms. | [`sub-skills/recommendation-and-analysis/`](../sub-skills/recommendation-and-analysis/SKILL.md) |
| `surprise.__main__` | CLI evaluation entry point behind `surprise` / `python -m surprise`. | [`sub-skills/evaluation-and-search/`](../sub-skills/evaluation-and-search/SKILL.md) |
| `surprise.builtin_datasets` | Built-in dataset cache and download helpers. | [`sub-skills/data-loading/`](../sub-skills/data-loading/SKILL.md) |

## Typical data flow

```text
Reader / dataframe / fold files
        ↓
     Dataset
        ↓
     Trainset
        ↓
 prediction algorithm
        ↓
 predictions / testset scores
        ↓
 evaluation, tuning, recommendation, or dump/load
```

## Quick routing reminders

- Need a `Reader`, dataframe load, predefined folds, or trainset conversion? Start with data loading.
- Need to choose a predictor or understand `Prediction.details`? Start with prediction algorithms.
- Need metrics, cross-validation, grid search, or CLI evaluation? Start with evaluation and search.
- Need top-N ranking, precision/recall@k, or serialization? Start with recommendation and analysis.

## Safety notes

- `Dataset.load_builtin(...)` may prompt or download if the cache is missing; prefer local files or cached data for automation.
- Raw ids are the public boundary; inner ids are for `Trainset` internals.
- Search and CLI helpers are evaluation tools, not training or serving APIs.
