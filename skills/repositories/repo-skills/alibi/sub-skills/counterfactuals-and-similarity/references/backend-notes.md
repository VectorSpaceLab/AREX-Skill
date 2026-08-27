# Backend Notes

## Purpose

Use this file when a user asks which optional backend is needed for a counterfactual or similarity workflow.

## Backend matrix

| Workflow | Backend | Why it matters |
| --- | --- | --- |
| `Counterfactual`, `CEM`, `CounterfactualProto` | TensorFlow | The classic implementations in this repo are TF1-style and rely on TensorFlow support. |
| `CounterfactualRL`, `CounterfactualRLTabular` | TensorFlow or Torch | The method can run on either backend, but the backend must match the model and decoder implementation. |
| `GradientSimilarity` | TensorFlow or Torch | The predictor and loss function backend must match the implementation used for gradients. |
| `AnchorText` language-model sampling | TensorFlow | Mentioned here only because the same repo extra often appears in workflow questions. |

## Selection guidance

- Choose TensorFlow when the task is the classic counterfactual family or a TensorFlow-backed similarity model.
- Choose Torch when the predictor and gradient workflow are already implemented in PyTorch.
- Do not say a base CPU install has verified these workflows if the corresponding extra is absent.

## Diagnostic behavior

- The placeholder checker should report the missing backend and the name of the gated workflow.
- If a single interpreter must mix TF1-style counterfactuals with TF2-only flows, explain the compatibility limit instead of trying to run both at once.
