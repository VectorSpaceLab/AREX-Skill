# Confidence, Prototype, and Persistence Workflows

## Purpose

Use this file to choose between TrustScore, LinearityMeasure, ProtoSelect, and save/load.

## Workflow choice

| Method | Best for | Main inputs | Notes |
| --- | --- | --- | --- |
| `TrustScore` | How trustworthy a classifier prediction is | training data, labels, class count, optional filtering settings | uses k-d trees |
| `LinearityMeasure` | How linear a model is near an instance | training data, predictor, method choice, sampling settings | can use grid or kNN sampling |
| `ProtoSelect` | Condensed, interpretable prototype summaries | kernel distance, epsilon radius, dataset, labels | may optionally summarise an unlabeled candidate set `Z` |
| `save_explainer` / `load_explainer` | Persistence / round-trip checks | explainer path and predictor on load | version-sensitive, predictor must be supplied again on load |

## TrustScore notes

- Fit on labeled data first.
- Choose the filtering mode only if the user wants outlier removal.
- The score returns both trust values and the closest non-predicted class.

## LinearityMeasure notes

- The helper can infer the feature range from training data.
- Use `model_type='classifier'` for class probabilities or logits-like outputs.
- Use `agg='pairwise'` or `agg='global'` depending on whether the user wants a point-local or region-global score.

## ProtoSelect notes

- The method summarizes a dataset by selected prototypes.
- A custom kernel distance must accept batched inputs.
- The preprocessing function should convert the raw input to the feature representation the distance metric expects.
- If `y` is omitted, the workflow treats the selection as unlabeled and only optimizes coverage.

## Save/load notes

- Save creates serialized artifacts in a directory.
- Load requires the original predictor again because predictors are not stored.
- Version mismatch warnings are expected and should be explained, not hidden.

## Safe usage pattern

1. Run the bundled smoke helper first.
2. Check the shape of the labels or predictor output.
3. Confirm the explainer can be reloaded with the predictor supplied again.
4. If the task is about anchors, attribution, or counterfactuals, route elsewhere.

## Read next

- `saving.md` for the persistence details.
- `troubleshooting.md` for symptom / cause / recovery notes.
- `scripts/smoke_confidence_prototypes.py` for the bundled CPU smoke.
