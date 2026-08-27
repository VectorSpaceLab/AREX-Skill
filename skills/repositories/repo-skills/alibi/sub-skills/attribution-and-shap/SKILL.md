---
name: attribution-and-shap
description: "Routes Alibi requests for KernelShap, TreeShap, and
  IntegratedGradients, including optional-backend selection and attribution
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Attribution and SHAP

Use this sub-skill when a user wants to explain predictions with SHAP-style or gradient-based attribution methods.

## Trigger phrases

Open this sub-skill when the user mentions:

- SHAP values, KernelShap, or TreeShap
- IntegratedGradients or gradient attribution
- background data, summarization, or categorical grouping
- `link='logit'`, `model_output`, baselines, or targets
- distributed SHAP or category summarization for encoded features

## What this sub-skill owns

- `KernelShap`
- `TreeShap`
- `IntegratedGradients`
- background summarization and categorical grouping guidance for those workflows

## What it does not own

- anchors or local rules
- counterfactual methods
- confidence scores or prototype selection
- save/load guidance

## Read next

- `references/workflows.md` for method choice and workflow flow
- `references/api-reference.md` for verified signatures and output notes
- `references/troubleshooting.md` for backend and shape failures
- `scripts/check_optional_attribution_backends.py` before promising a runtime path

## Typical flow

1. Decide whether the user needs SHAP-style attribution or gradient attribution.
2. Check whether the chosen export is a real class or a `MissingDependency` placeholder.
3. If SHAP is required, install the SHAP extra before trying to use KernelShap or TreeShap.
4. If IntegratedGradients is required, install the TensorFlow extra and confirm the model and baseline shapes.
5. Use the diagnostic script on a base install to make the missing-backend status explicit.

## Good fits

- local feature attribution for tabular or tree-based models
- categorical grouping or summarization for encoded features
- TensorFlow / Keras gradient attribution with baselines and targets

## Common failure signals

- the export is a placeholder because the extra is missing
- the background data has the wrong shape or is too large for the chosen summarization mode
- tree-model output or model_output does not match the TreeShap path
- IntegratedGradients baselines or targets do not match the model output shape
