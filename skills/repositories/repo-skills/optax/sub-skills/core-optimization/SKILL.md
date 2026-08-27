---
name: core-optimization
description: "Compose Optax optimizers, gradient transformations, wrappers, and
  update loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core Optimization

Use this sub-skill when the user wants to **choose, compose, or debug an Optax optimizer pipeline**. This is the main route for ordinary gradient-transformation workflows.

## Include here

- Base optimizers such as `adam`, `adamw`, `sgd`, `lamb`, `lion`, `rmsprop`, `lbfgs`, `adafactor`, and related aliases.
- Gradient transformations such as clipping, weight decay, momentum/trace-style updates, adaptive scaling, and schedule-driven scaling.
- Composition helpers: `chain`, `named_chain`, `partition`, and parameter masking or freezing workflows.
- Wrapper-style behaviors such as `lookahead`, `MultiSteps`, `apply_if_finite`, `skip_large_updates`, and `skip_not_finite`.
- The update loop itself: `init`, `update`, and `apply_updates`.

## Exclude or route elsewhere

- Loss-function selection and schedule families that are being chosen for their own sake: use `losses-and-schedules`.
- Projections, assignment, tree utilities, linear algebra helpers, second-order helpers, and contrib/experimental algorithms: use `advanced-topics`.
- Anything that is really a metric, objective, or data-splitting question rather than an optimizer question.

## Good questions for this route

- “Which Optax optimizer should I start with?”
- “How do I chain clipping with AdamW?”
- “How do I freeze some parameters but not others?”
- “How do I apply updates safely?”
- “How do I inject a schedule into an optimizer hyperparameter?”

## Read first

- `../../references/core-workflows.md` for the canonical update loop, composition patterns, and schedule injection.
- `../../references/troubleshooting.md` for shape mismatch, state reuse, and backend confusion.
- `../../scripts/optax_skill_doctor.py` when a quick import-and-smoke check is useful.

## Core workflow

1. Choose a base optimizer or low-level transform.
2. Add wrappers or composition helpers if the user needs clipping, freezing, masking, or delayed updates.
3. Decide whether schedules should be part of the optimizer hyperparameters or a separate training-loop concern.
4. Initialize the optimizer state from the parameter tree.
5. Update with gradients, then apply the returned updates back to the parameter tree.

## Signals that this route is correct

- The user is thinking about parameters, gradients, optimizer state, or `apply_updates`.
- The user wants to compare two optimizers or learn how to combine them.
- The user is debugging a training loop and the issue is about the transformation pipeline rather than the loss value.

## Common mistakes

- Reusing state from one optimizer pipeline with a different pipeline.
- Passing a parameter tree whose structure does not match the gradient tree.
- Forgetting that some transforms need the current parameters during `update(...)`.
- Treating a learning-rate schedule as if it were a loss or data-processing problem.

## Useful examples

- `../../references/examples-index.md` points to notebooks such as `mlp_mnist.ipynb`, `flax_example.ipynb`, `lbfgs.ipynb`, and `lookahead_mnist.ipynb`, which show optimizer pipelines in real training loops.
