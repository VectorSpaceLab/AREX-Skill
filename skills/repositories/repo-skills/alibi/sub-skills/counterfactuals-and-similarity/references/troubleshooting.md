# Troubleshooting

## The workflow is a placeholder in the current environment

**Symptoms**
- The requested class is a `MissingDependency` placeholder.
- The diagnostic script says the backend is missing.

**Likely cause**
- The TensorFlow, Torch, or related optional extra is not installed.

**Fix**
- Run `scripts/check_optional_counterfactual_backends.py`.
- Install the backend that the script points to.

## TF1-style counterfactuals clash with TF2 workflows

**Symptoms**
- The user wants to mix classic counterfactuals with TF2-only attribution in one interpreter session.

**Likely cause**
- The classic Counterfactual / CEM / CFProto implementations in this repo are TF1-style.

**Fix**
- Explain the compatibility boundary and run the workflows in separate sessions if needed.

## Tree models are a poor fit for gradient counterfactuals

**Symptoms**
- The user asks why no counterfactual is found for a tree model.

**Likely cause**
- Gradient-based counterfactual methods need differentiability.

**Fix**
- Recommend the similarity or RL route if it matches the task, or explain that the model is not a good fit for the gradient-based route.

## CFRL decoder or conditioning is wrong

**Symptoms**
- CFRL explodes when fitting or explaining tabular data.

**Likely cause**
- The decoder does not return a list of tensors, or the conditioning vector does not match the feature constraints.

**Fix**
- Re-check the decoder contract and the feature-constraint description in `backend-notes.md`.

## Similarity runs out of memory

**Symptoms**
- `precompute_grads=True` causes an out-of-memory error.

**Likely cause**
- The model is too large for full gradient precomputation.

**Fix**
- Reduce the training set, freeze parameters, or avoid precomputing gradients.

## Where to go next

- Read `references/workflows.md` to pick the right backend route.
- Use the diagnostic script before trying any heavy backend run.
