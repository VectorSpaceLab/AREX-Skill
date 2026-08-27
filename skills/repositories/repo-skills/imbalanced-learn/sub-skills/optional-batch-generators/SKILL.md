---
name: optional-batch-generators
description: "Router for imbalanced-learn balanced mini-batch helpers for Keras
  and TensorFlow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# optional-batch-generators

Use this sub-skill when the task names balanced mini-batches, Keras, or
TensorFlow support in imbalanced-learn.

This sub-skill owns the optional generator helpers:

- `imblearn.tensorflow.balanced_batch_generator`
- `imblearn.keras.BalancedBatchGenerator`
- `imblearn.keras.balanced_batch_generator`

It is intentionally narrower than a deep-learning training skill. It covers the
balanced data iterator surface, not model architecture design, training loops,
or GPU acceleration strategy.

## What to do first

1. Check whether `tensorflow` or `keras` is actually importable.
2. Decide whether the user wants the TensorFlow iterator, the Keras `Sequence`,
   or both.
3. Confirm that the sampler exposes `sample_indices_`.
4. Keep the smoke tiny: generate a small batch, inspect the shapes, and stop.
5. Treat missing Keras/TensorFlow as an optional-capability skip, not a core
   package failure.

## Typical routing cues

- `balanced_batch_generator`
- `BalancedBatchGenerator`
- `keras`, `tensorflow`, `Sequence`, `fit`
- balanced mini-batches or class-balanced iterators

## When to read the bundled references

- `references/workflows.md` for import and backend decision flow.
- `references/api-reference.md` for the compact generator catalog.
- `references/troubleshooting.md` when backend imports or generator construction
  fail.

## Common choices

- Use `balanced_batch_generator` from `imblearn.tensorflow` when the workflow
  expects a simple generator/steps-per-epoch pair.
- Use `BalancedBatchGenerator` from `imblearn.keras` when the workflow wants a
  Keras `Sequence`-style object that can be passed to `fit`.
- Use the `sampler` parameter when the default `RandomUnderSampler` is not the
  desired balancing strategy.
- Use `keep_sparse=True` only when the downstream loop can consume sparse mini-
  batches.

## Native evidence to keep in mind

These repo tests are the most relevant later verification anchors for this
sub-skill:

- `imblearn/tensorflow/tests/test_generator.py::test_balanced_batch_generator`
- `imblearn/tensorflow/tests/test_generator.py::test_balanced_batch_generator_function_sparse`
- `imblearn/keras/tests/test_generator.py::test_balanced_batch_generator_class`
- `imblearn/keras/tests/test_generator.py::test_balanced_batch_generator_function`

## Package-specific cautions

- The generator helpers need a sampler with `sample_indices_`.
- `len(generator)` uses floor division by `batch_size`.
- `BalancedBatchGenerator` depends on the optional backend being importable at
  instantiation time.
- Keras and TensorFlow support is optional for the package as a whole, even
  though this sub-skill targets those APIs directly.

## Use the script

- `scripts/batch_generator_smoke.py` for a tiny optional-backend batch smoke.
