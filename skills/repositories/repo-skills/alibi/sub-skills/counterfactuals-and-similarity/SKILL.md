---
name: counterfactuals-and-similarity
description: "Routes Alibi requests for Counterfactual, CEM,
  CounterfactualProto, CounterfactualRL, and GradientSimilarity workflows and
  their backend gating."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Counterfactuals and Similarity

Use this sub-skill when a user wants to generate counterfactual examples or compare instances with gradient-based similarity.

## Trigger phrases

Open this sub-skill when the user mentions:

- counterfactual explanations or recourse
- CEM, Counterfactual, or CounterfactualProto
- CounterfactualRL or CFRL
- GradientSimilarity or similarity explanations
- TensorFlow 1.x vs 2.x compatibility, torch backend choice, or gradient memory pressure

## What this sub-skill owns

- `Counterfactual`
- `CEM`
- `CounterfactualProto`
- `CounterfactualRL`
- `CounterfactualRLTabular`
- `GradientSimilarity`

## What it does not own

- global tabular explainers
- anchors
- SHAP / IntegratedGradients
- confidence scores or prototype summarization as a standalone family
- save/load guidance

## Read next

- `references/workflows.md` for the backend and method matrix
- `references/api-reference.md` for the verified Counterfactual, CEM, CFProto, CFRL, and GradientSimilarity signatures
- `references/backend-notes.md` for TF / Torch selection guidance
- `references/troubleshooting.md` for known counterfactual and similarity failures
- `scripts/check_optional_counterfactual_backends.py` before promising a runtime path

## Typical flow

1. Decide whether the request is a basic counterfactual, a prototype-guided counterfactual, or a similarity explanation.
2. Check whether the requested backend is TensorFlow or Torch and whether the environment already has it.
3. If the user only needs to know why the workflow is unavailable, run the diagnostic script instead of attempting a full training run.
4. Use the workflow reference to explain the backend and tensor shape expectations.

## Good fits

- recourse-style counterfactuals on tabular or image-like data
- TF/Keras counterfactual search with gradient support
- model-similarity workflows that use gradients over parameters

## Common failure signals

- TF1-style counterfactual methods collide with TF2-only workflows
- the model is a tree and the method expects differentiability
- the CFRL decoder does not return a list of tensors for tabular data
- similarity workflows run out of memory when precomputing gradients
- the requested backend is not installed yet
