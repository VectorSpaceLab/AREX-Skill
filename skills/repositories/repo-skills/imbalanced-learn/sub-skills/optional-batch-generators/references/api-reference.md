# API Reference — optional batch generators

## Core signatures confirmed in the private inspection environment

| Symbol | Signature / key arguments | Notes |
|---|---|---|
| `balanced_batch_generator` | `balanced_batch_generator(X, y, *, sample_weight=None, sampler=None, batch_size=32, keep_sparse=False, random_state=None)` | TensorFlow-style generator + steps-per-epoch. |
| `BalancedBatchGenerator` | `BalancedBatchGenerator(X, y, *, sample_weight=None, sampler=None, batch_size=32, keep_sparse=False, random_state=None)` | Keras `Sequence`-style balanced batch generator. |

## Behavior notes

- If `sampler` is omitted, both helpers use `RandomUnderSampler`.
- The sampler must expose `sample_indices_` after fitting.
- The generator length is computed with floor division by `batch_size`.
- `keep_sparse=False` converts sparse batches to dense arrays.
- The Keras path is optional and may fail to instantiate when Keras/TensorFlow
  is absent.

## Routing notes

- This sub-skill is about balanced mini-batches, not about building or tuning a
  neural network.
- If the user only needs an imbalanced sampler or pipeline, route to the
  sampling or model-workflow sub-skills instead.
