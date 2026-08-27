---
name: training
description: "Routes TensorFlow Privacy users who want to train differentially
  private models with optimizers, Keras model wrappers, estimators, or
  logistic-regression helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training

Use this sub-skill when the user wants to train a differentially private model or wrap an existing TensorFlow training loop with DP behavior.

## Trigger phrases

- "use DP-SGD"
- "replace my optimizer with a DP optimizer"
- "train with TensorFlow Privacy"
- "wrap a Keras model for differential privacy"
- "DP estimator"
- "DP logistic regression"
- "vectorized optimizer"
- "sparse DP optimizer"

## What this sub-skill covers

- `DPKeras*Optimizer` and generic DP optimizer wrappers
- `DPModel` / `DPSequential` / `make_dp_model_class`
- estimator-based classifiers
- logistic-regression helpers and noise-multiplier helpers
- the training-side guidance in the MNIST and text tutorials

## What it does not cover

- privacy budget and noise calculation -> `../privacy-accounting/`
- `DPQuery` internals -> `../queries/`
- membership inference and secret-sharer analysis -> `../privacy-tests/`
- fast clipping internals -> `../fast-clipping/`

## Read this before you act

- `references/api-reference.md` for verified constructors, function signatures, and return shapes.
- `references/troubleshooting.md` for loss-shape, microbatch, and optimizer-state failures.
- `../../references/install-and-scope.md` for the minimum CPU runtime and the published package names.

## Typical workflow

1. Pick the DP training surface that matches the user's code style:
   - Keras compile/fit -> `DPKeras*Optimizer` or `DPModel`
   - custom training loop -> `DPKeras*Optimizer` or a generic DP optimizer wrapper
   - estimator-style code -> `DNNClassifier`
   - logistic-regression experiment -> `logistic_dpsgd` or `logistic_objective_perturbation`
2. Confirm the loss is per-example when the DP optimizer needs it.
3. Choose the right `num_microbatches` and clipping norm.
4. Use the bundled tiny smoke script if you need a safe training sanity check.
5. If the model uses sparse or distributed paths, read the troubleshooting page before changing the training loop.

## Cross-links

- `../fast-clipping/` owns the lower-level clipping internals and sparse-noise helpers used by `DPModel`.
- `../privacy-accounting/` owns the epsilon/noise calculation that usually follows training.

## Bundled helper

Run `scripts/tiny_dp_training_smoke.py` when you want a small, deterministic training sanity check. It trains a tiny synthetic classifier with `DPKerasSGDOptimizer` and reports the final loss.
