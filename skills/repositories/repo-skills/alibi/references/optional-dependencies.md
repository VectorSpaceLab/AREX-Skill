# Optional Dependencies

## Purpose

Read this when a user asks which Alibi extra to install, or when a public export is present only as a `MissingDependency` placeholder.

## Base install

The base package covers the CPU workflows used by the root smoke script:

- ALE
- PartialDependence
- PartialDependenceVariance
- PermutationImportance
- AnchorTabular
- TrustScore
- LinearityMeasure
- ProtoSelect
- save/load helpers

## Optional extras

| Extra | Enables | Notes |
| --- | --- | --- |
| `alibi[shap]` | KernelShap and TreeShap | Needed for SHAP wrappers and tree-based attribution workflows. |
| `alibi[tensorflow]` | IntegratedGradients, CEM, Counterfactual, CounterfactualProto, TensorFlow-backed CounterfactualRL, language-model anchor sampling, TensorFlow utility models, and `fetch_fashion_mnist` | Also the route for TensorFlow/Keras-backed explanation workflows. |
| `alibi[torch]` | Torch-backed CounterfactualRL, GradientSimilarity, and Torch utility models | Use when the user wants the PyTorch backend instead of TensorFlow. |
| `alibi[ray]` | DistributedAnchorTabular and distributed KernelShap | Needed only for distributed explanation workflows. |

## Base import note

Alibi imports `spacy` helpers from `alibi.utils`. If a base import fails with a message about `click` or spaCy CLI support, repair the Python environment before assuming Alibi itself is broken.

## How to check a placeholder

1. Run `scripts/check_optional_backends.py`.
2. If the name is listed as missing, install the matching extra.
3. Re-run the checker before using the workflow in a smoke or verification step.

## Selection tips

- Choose `alibi[shap]` for KernelShap and TreeShap.
- Choose `alibi[tensorflow]` for the classic TensorFlow-backed counterfactual and attribution workflows.
- Choose `alibi[torch]` when the workflow is implemented against PyTorch.
- Choose `alibi[ray]` only for distributed explanation tasks.
