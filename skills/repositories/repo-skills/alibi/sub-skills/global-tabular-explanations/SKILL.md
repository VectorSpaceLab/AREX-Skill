---
name: global-tabular-explanations
description: "Routes requests for ALE, partial dependence, PD variance,
  permutation importance, and other global tabular explanation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Global Tabular Explanations

Use this sub-skill for Alibi tasks that explain tabular model behavior with global feature-effect methods.

## Trigger phrases

Open this sub-skill when the user asks for any of the following:

- ALE curves or accumulated local effects
- partial dependence or ICE plots
- tree-based partial dependence
- PD variance feature importance or feature interaction
- permutation importance on tabular data
- feature-effect plots for scikit-learn-style predictors

## What this sub-skill owns

- `ALE`
- `PartialDependence`
- `TreePartialDependence`
- `PartialDependenceVariance`
- `PermutationImportance`
- plotting helpers for those methods

## What it does not own

- anchors or local explanations
- SHAP or integrated gradients
- counterfactual methods
- confidence scores or prototype selection
- persistence / save-load guidance

## Read next

- `references/workflows.md` for method choice and execution flow
- `references/api-reference.md` for verified signatures and parameter notes
- `references/troubleshooting.md` for predictor, grid, and plotting failures
- `scripts/smoke_global_tabular.py` for a safe CPU smoke

## Typical flow

1. Wrap the model as a batch predictor that returns `numpy` outputs.
2. Decide whether the task is ALE, PD, PD variance, or permutation importance.
3. Pass feature names and categorical names when the plot needs readable labels.
4. Use the smoke script on iris-sized data before trying a larger dataset.
5. If the user actually needs SHAP or TensorFlow attribution, route them to the attribution sub-skill and its optional-dependency notes.

## Good fits

- global feature effects on tabular data
- interpreting class probabilities or regression outputs with a small predictor wrapper
- comparing feature importance across model families
- understanding feature interactions with PD variance

## Common failure signals

- `predictor` returns a list, scalar, or wrong class/probability shape
- categorical features are passed with the wrong index or encoding
- a custom grid has unsorted or incompatible values
- the model is tree-based but the method expects a generic predictor or vice versa
- plotting fails because a feature name is missing or misaligned
