# Workflows — optional batch generators

## 1. Check the backend

Before creating a Keras-oriented generator, confirm that the relevant package is
importable:

- `tensorflow` for the TensorFlow helper path
- `keras` for the Keras `Sequence` path

If the backend is missing, the skill should explain the skip rather than claim a
core package failure.

## 2. Choose the generator form

- Use `balanced_batch_generator(...)` when the downstream code expects a plain
  generator and a `steps_per_epoch` integer.
- Use `BalancedBatchGenerator(...)` when the downstream code expects a Keras
  `Sequence`.

## 3. Keep the smoke tiny

A good smoke check should:

1. create a small synthetic dataset,
2. create a generator with `RandomUnderSampler` or another simple sampler,
3. fetch one batch,
4. print the shapes and class counts,
5. stop.

## 4. Understand the contract

- The sampler must expose `sample_indices_`.
- Sparse batches are only preserved when `keep_sparse=True`.
- The batch count uses floor division, so it may be smaller than the raw sample
  count suggests.

## 5. Native evidence to match later

- `test_balanced_batch_generator`
- `test_balanced_batch_generator_function_sparse`
- `test_balanced_batch_generator_class`
- `test_balanced_batch_generator_function`
