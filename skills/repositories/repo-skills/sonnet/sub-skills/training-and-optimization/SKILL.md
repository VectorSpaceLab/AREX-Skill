---
name: training-and-optimization
description: "Train Sonnet modules with TensorFlow 2 GradientTape, Sonnet
  optimizers, metrics, and tiny local smoke loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sonnet Training and Optimization

Use this sub-skill for TensorFlow 2 training loops around Sonnet modules. Sonnet provides modules, optimizers, and small metrics; it does not provide a Keras-style trainer, data pipeline, checkpoint manager, or distributed all-reduce policy.

## Start here

- [references/optimizer-api.md](references/optimizer-api.md): optimizer signatures, state behavior, dense/sparse updates, validation errors.
- [references/training-workflows.md](references/training-workflows.md): eager and `tf.function` loop recipes, metrics, and no-download data fixtures.
- [references/troubleshooting.md](references/troubleshooting.md): empty variables, `None` gradients, dtype/length mismatches, stale optimizer state, and stagnant loss.
- [scripts/sonnet_tiny_training_smoke.py](scripts/sonnet_tiny_training_smoke.py): synthetic training loop adapted from the MNIST example pattern.

## Boundaries

- Custom module construction: [../module-authoring/SKILL.md](../module-authoring/SKILL.md).
- Built-in layer/net choices: [../layers-and-nets/SKILL.md](../layers-and-nets/SKILL.md).
- Functional optimizers: [../functional-transforms/SKILL.md](../functional-transforms/SKILL.md).
- Distribution/export: [../serialization-and-distribution/SKILL.md](../serialization-and-distribution/SKILL.md).

## Core workflow

Run a first forward pass, collect `model.trainable_variables`, compute scalar loss under `tf.GradientTape`, call `tape.gradient(loss, variables)`, then call `optimizer.apply(gradients, variables)`.
