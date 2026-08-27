# Counterfactual and Similarity Workflows

## Purpose

Use this file to choose the right counterfactual or similarity route and to remember the backend constraints.

## Workflow choice

| Method | Best for | Main inputs | Notes |
| --- | --- | --- | --- |
| `Counterfactual` | Basic counterfactual search | predictor or TF/Keras model, input shape, distance and constraint settings | uses the TensorFlow extra |
| `CEM` | Pertinent positives / negatives | predictor or TF/Keras model, input shape, `mode`, training data for fit | uses the TensorFlow extra |
| `CounterfactualProto` | Prototype-guided counterfactuals | predictor, optional encoder/decoder, categorical constraints, fit data when needed | uses the TensorFlow extra |
| `CounterfactualRL` / `CounterfactualRLTabular` | Learned counterfactual generation with conditioning | predictor, encoder/decoder, backend choice, conditioning or immutability settings | uses TensorFlow or Torch |
| `GradientSimilarity` | Gradient-based similarity ranking | predictor, loss function, backend choice, training data, labels | uses TensorFlow or Torch |

## Counterfactual workflow notes

- The classic `Counterfactual`, `CEM`, and `CounterfactualProto` routes are TensorFlow 1.x-style implementations in the current repo.
- They are not a good fit for tree models because the decision function is not differentiable.
- `CounterfactualProto` can use either an autoencoder or k-d trees to build prototypes.
- Categorical feature constraints are handled as part of the prototype-guided route.

## CFRL workflow notes

- Choose TensorFlow or Torch up front.
- The tabular variant expects a decoder that returns a list of tensors.
- Conditioning vectors are how the user expresses immutable or range-limited features.
- The method is intended for batches and not just a single example.

## Similarity workflow notes

- Choose the backend that matches the predictor implementation.
- `precompute_grads=True` speeds up explanation time but can consume a lot of memory.
- Large models may need a smaller training subset or frozen parameters.
- The diagnostic script should be used first in a base install so the user sees which backend is missing.

## Safe usage pattern

1. Identify the backend the workflow needs.
2. Run the diagnostic script on a base install.
3. Install the requested extra if the workflow is genuinely needed.
4. If the user only needs troubleshooting advice, quote the symptom and recovery path from `troubleshooting.md`.

## Read next

- `backend-notes.md` for a concise backend matrix.
- `troubleshooting.md` for detailed error recovery.
- `scripts/check_optional_counterfactual_backends.py` for a placeholder check.
