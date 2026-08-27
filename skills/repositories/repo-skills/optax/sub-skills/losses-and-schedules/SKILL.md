---
name: losses-and-schedules
description: "Select Optax losses, schedules, microbatching helpers, and
  perturbation wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Losses and Schedules

Use this sub-skill when the user is deciding **which objective, learning-rate schedule, or training helper to use**. This route is about the scalar behavior of training, not about the optimizer pipeline itself.

## Include here

- Loss families in `optax.losses`: classification, regression, ranking, segmentation, KL/divergence, Fenchel-Young, contrastive, and related helpers.
- Schedule families in `optax.schedules`: constant, warmup, decay, one-cycle, SGDR, piecewise, joined schedules, and schedule injection.
- `optax.contrib.reduce_on_plateau` when the user wants a metric-driven learning-rate adjustment.
- Microbatching helpers: `microbatch`, `micro_vmap`, `micro_grad`, `reshape_batch_axis`, and accumulation helpers.
- Perturbation wrappers: `make_perturbed_fun` and the bundled noise models.

## Exclude or route elsewhere

- Ordinary optimizer selection, chaining, masking, or wrapper composition: use `core-optimization`.
- Projections, tree utilities, assignment, linear algebra, second order, and contrib algorithms that are not really schedule-like: use `advanced-topics`.

## Good questions for this route

- “Which loss fits logits vs integer labels?”
- “How do I schedule the learning rate with warmup and cosine decay?”
- “How do I accumulate gradients with microbatches?”
- “How do I add perturbations or smoothing to an objective?”

## Read first

- `../../references/losses-and-schedules.md` for the loss families, schedule families, and helper patterns.
- `../../references/examples-index.md` for notebooks that demonstrate loss/schedule and microbatching workflows.
- `../../references/troubleshooting.md` for label-shape, step-convention, and microbatch-accumulator issues.

## Core workflow

1. Identify the target family: classification, regression, ranking, segmentation, schedule, or accumulation helper.
2. Verify the tensor/label convention before writing code. Many loss functions distinguish logits, probabilities, one-hot labels, and integer labels.
3. Decide whether the schedule belongs directly in the optimizer, in the training loop, or in a wrapper such as `inject_hyperparams`.
4. If the batch is too large, choose a microbatch helper before changing the objective math.
5. If the user is asking for robustness or smoothing, consider whether `make_perturbed_fun` is the right wrapper.

## Signals that this route is correct

- The user is comparing losses or asks for the “right” loss for a task.
- The user is tuning a learning-rate curve or wants warmup/decay behavior.
- The user is dealing with gradient accumulation, microbatching, or perturbation-based objective wrappers.

## Common mistakes

- Feeding probabilities to a loss that expects logits.
- Mixing integer-label and one-hot conventions.
- Advancing the schedule with the wrong step index or wrong units.
- Treating microbatching as a trivial `vmap` without checking the accumulator semantics.

## Useful examples

- `../../references/examples-index.md` points to `gradient_accumulation.ipynb`, `gradient_accumulation_and_microbatching.ipynb`, `perturbations.ipynb`, `cifar10_resnet.ipynb`, and `contrib/reduce_on_plateau.ipynb`.
