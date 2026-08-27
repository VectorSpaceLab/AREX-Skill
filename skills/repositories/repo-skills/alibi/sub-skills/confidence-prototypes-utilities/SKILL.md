---
name: confidence-prototypes-utilities
description: "Routes Alibi requests for TrustScore, LinearityMeasure,
  ProtoSelect, save/load round-trips, and the small shared utilities they rely
  on."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Confidence, Prototypes, and Utilities

Use this sub-skill when a user wants to score prediction confidence, summarize a dataset with prototypes, or save and reload an explainer.

## Trigger phrases

Open this sub-skill when the user mentions:

- TrustScore or trust scores
- LinearityMeasure or linearity measure
- ProtoSelect or prototype selection
- save/load explainer, `load_explainer`, or explanation persistence
- category map, `gen_category_map`, or `save_explainer`

## What this sub-skill owns

- `TrustScore`
- `LinearityMeasure`
- `ProtoSelect`
- `save_explainer` and `load_explainer`
- the shared utility helpers that support those workflows

## What it does not own

- anchors
- SHAP / IntegratedGradients
- counterfactuals or similarity
- any heavier optional-backend family

## Read next

- `references/workflows.md` for the confidence / prototype / persistence flow map
- `references/api-reference.md` for the verified TrustScore, LinearityMeasure, ProtoSelect, and persistence signatures
- `references/saving.md` for save/load behavior and version sensitivity
- `references/troubleshooting.md` for label, range, kernel, and persistence errors
- `scripts/smoke_confidence_prototypes.py` for the bundled CPU smoke

## Typical flow

1. Decide whether the user wants a confidence score, a prototype summary, or a persistence check.
2. Make sure the classifier labels and input shape match the chosen helper.
3. Run the smoke script on iris-sized data to confirm the environment and the API contract.
4. If the user only needs a round-trip or a utility check, keep the example small and deterministic.

## Good fits

- warning flags for classifier predictions
- model linearity around a point
- dataset summarization and prototype selection
- save/load round-trips for explainer objects

## Common failure signals

- TrustScore label count does not match the class structure
- LinearityMeasure cannot infer the feature range or the model type is wrong
- ProtoSelect distance or preprocess settings are incompatible with the data
- a saved explainer cannot be reloaded without passing the original predictor
