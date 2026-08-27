---
name: transforms-features
description: "Use GluonTS transformations, time features, samplers, splitters,
  and missing-value indicators for training and prediction data preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# transforms-features

Use this sub-skill when a task needs to prepare GluonTS `DataEntry` streams for model training or prediction with transformation chains, observed-value indicators, time features, lag selection, or instance sampling/splitting.

## Route here for

- Building `gluonts.transform.Chain` pipelines that operate on iterables of dictionaries.
- Adding missing-value observed indicators and deterministic target imputations.
- Generating calendar/time features from a frequency string and choosing model lag sequences.
- Creating training or prediction instances with `InstanceSampler` and `InstanceSplitter`.
- Diagnosing shape, length, frequency, or `is_train` mistakes in transformed datasets.

## Do not use this sub-skill for

- Constructing the original dataset from pandas/files/JSON Lines: use the data-pipelines sub-skill first.
- Choosing, training, serializing, or serving estimators/predictors: use the forecasting-models or deployment-extensions sub-skill.
- MXNet-specific transformation recipes: those legacy workflows were not selected as verified required coverage.

## Read map

1. Start with `references/api-reference.md` for API contracts, constructor signatures, field names, and shape conventions.
2. Use `references/workflows.md` for train/prediction transformation recipes and assertion checklists.
3. Use `references/troubleshooting.md` when a chain yields zero instances, wrong feature lengths, unsupported frequencies, or NaN/shape failures.
4. Run `scripts/transform_feature_smoke.py --help` and then `scripts/transform_feature_smoke.py` to check that the installed `gluonts` package can execute the core transform/time-feature path without the source checkout.

## Minimal operating pattern

- Convert raw data to a GluonTS dataset first, so entries contain `start` as a period-like value with a frequency and `target` as a numeric array.
- Build a `Chain` in feature order: target conversion/observed indicator, time/age/constant features, feature stacking if needed, then an instance splitter if the model expects windows.
- Pass `is_train=True` when creating training windows with available future target values; pass `is_train=False` for prediction-time windows and ensure known-future features have `len(target) + prediction_length` values.
- Assert field presence and shapes after transformation before handing the result to an estimator or predictor.
