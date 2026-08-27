# Evaluation and splitting API reference

This reference covers LightFM 1.17 ranking evaluation behavior for fitted CPU
models. The functions operate on SciPy sparse user-item matrices; non-zero
entries are treated as positives for ranking metrics.

## Core invariants

- `test_interactions` and `train_interactions` must describe the same user and
  item index spaces and normally have the same `(n_users, n_items)` shape.
- Metric calls rank only the non-zero entries in `test_interactions`.
- Any non-zero value in an evaluation matrix is treated as an interaction. If a
  source matrix encodes negative feedback with negative values, set those
  entries to zero before computing ranking metrics.
- Pass `train_interactions` when scoring a test matrix. These training positives
  are excluded from the candidate ranking so the score does not reward
  recommending already-known items.
- Keep `check_intersections=True` for offline test metrics. It catches
  train/test leakage before a score is produced.
- If the model was trained with explicit `user_features` or `item_features`,
  pass compatible matrices to `predict_rank` and to the metric helpers.

## Evaluation function signatures

| Function | Signature | Return |
| --- | --- | --- |
| `precision_at_k` | `precision_at_k(model, test_interactions, train_interactions=None, k=10, user_features=None, item_features=None, preserve_rows=False, num_threads=1, check_intersections=True)` | `numpy.ndarray` of per-user precision values. |
| `recall_at_k` | `recall_at_k(model, test_interactions, train_interactions=None, k=10, user_features=None, item_features=None, preserve_rows=False, num_threads=1, check_intersections=True)` | `numpy.ndarray` of per-user recall values. |
| `auc_score` | `auc_score(model, test_interactions, train_interactions=None, user_features=None, item_features=None, preserve_rows=False, num_threads=1, check_intersections=True)` | `numpy.ndarray` of per-user ROC AUC values. |
| `reciprocal_rank` | `reciprocal_rank(model, test_interactions, train_interactions=None, user_features=None, item_features=None, preserve_rows=False, num_threads=1, check_intersections=True)` | `numpy.ndarray` of per-user reciprocal-rank values. |

### Metric meanings

- `precision_at_k`: fraction of the top `k` ranked candidate items that are
  non-zero in the test matrix. The denominator is `k`, not the number of test
  positives and not the number of remaining candidate items.
- `recall_at_k`: fraction of that user's test positives whose rank is in the
  top `k`. The denominator is the user's number of non-zero test entries.
- `auc_score`: probability-like ranking score for test positives versus
  unobserved candidate items, after optional training positives are filtered.
  Users with no test positives are conventionally uninformative; the default
  row filtering removes them from aggregate means.
- `reciprocal_rank`: `1 / (best_rank + 1)` for the highest-ranked test positive,
  where rank `0` is best. It is `0.0` for users with no ranked test positives.

For top-k metrics, a test positive is counted as a hit when its rank is `< k`
(rank `0` through rank `k - 1`).

## Output shape and `preserve_rows`

| `preserve_rows` | Output length | Use when | Notes |
| --- | --- | --- | --- |
| `False` (default) | Number of users with at least one non-zero in `test_interactions`. | You want an aggregate over evaluable users. | Zero-test rows are removed before returning values. |
| `True` | `n_users`, aligned to the user axis of `test_interactions`. | You need to attach metric values back to original user ids or compare with other per-user arrays. | Keep a separate `row_has_test = test_interactions.getnnz(axis=1) > 0` mask before averaging. Zero-test rows are not meaningful for recall and can distort means. |

Recommended aggregate pattern for user-preserving output:

```python
row_has_test = test_interactions.getnnz(axis=1) > 0
scores = precision_at_k(
    model,
    test_interactions,
    train_interactions=train_interactions,
    k=10,
    preserve_rows=True,
)
mean_over_evaluable_users = scores[row_has_test].mean()
```

Use the same mask for recall, AUC, and reciprocal rank when the goal is a mean
over users who actually had held-out positives.

## `LightFM.predict_rank`

Signature:

```python
LightFM.predict_rank(
    test_interactions,
    train_interactions=None,
    item_features=None,
    user_features=None,
    num_threads=1,
    check_intersections=True,
)
```

Returns a SciPy CSR matrix with the same shape and sparsity pattern as
`test_interactions`. Each non-zero position `(user, item)` stores the rank of
that item in the user's recommendation list:

- `0` is the top recommendation.
- Larger values are worse ranks.
- Only positions non-zero in `test_interactions` receive stored rank values.
- `train_interactions` removes known training positives from the candidate
  ranking before ranks are assigned.
- `predict_rank` is most appropriate when a small set of user-item positives per
  user needs ranks. For dense all-item score vectors, use `LightFM.predict`
  through [model-training](../../model-training/SKILL.md).

When all item scores are tied, LightFM assigns pessimistic ranks: tied items get
worst-case ranks rather than arbitrary favorable ranks. An untrained or manually
zeroed model can therefore have `precision_at_k == 0.0` even when positives are
present.

## Intersection checking

With `train_interactions` supplied and `check_intersections=True`, LightFM
checks whether `test_interactions.multiply(train_interactions).nnz` is non-zero.
If any coordinate appears in both matrices, evaluation raises `ValueError`
because the split leaks positives across train and test.

Keep the default enabled for offline evaluation. Set `check_intersections=False`
only for controlled diagnostics, such as intentionally ranking the training
matrix, and do not report such scores as leakage-safe test metrics.

## Sparse matrix expectations

- Use SciPy sparse matrices for all interaction inputs. CSR is the documented
  evaluation format and is efficient for row operations; COO inputs are usually
  accepted because LightFM converts internally, but convert to CSR before heavy
  repeated evaluation.
- `random_train_test_split` accepts any SciPy sparse matrix and returns COO
  train/test matrices. Convert returned matrices to CSR if subsequent code does
  many row lookups.
- Keep interaction matrices two-dimensional with shape `(n_users, n_items)`.
  Mismatched dimensions between train/test matrices, model identity features,
  or supplied feature matrices will cause shape errors.
- `num_threads` must be at least `1`. The package is CPU-only; increasing thread
  count may help large evaluations on builds with multithreading support, but it
  should not exceed physical cores.

## `random_train_test_split`

Signature:

```python
random_train_test_split(interactions, test_percentage=0.2, random_state=None)
```

Returns `(train, test)` as SciPy COO matrices with the same shape and dtype as
`interactions`.

Behavior and cautions:

- Splits non-zero entries randomly at the interaction-entry level.
- Does not guarantee that every user or item in the test matrix also appears in
  the train matrix. This can create partial cold-start rows/items in test.
- Uses `int((1.0 - test_percentage) * interactions.nnz)` as the cutoff, so the
  realized test fraction is integer-rounded for small matrices.
- `random_state` may be an integer seed or a `numpy.random.RandomState`.
- To split a matching sample-weight matrix along the same entries, use a fresh
  random state with the same integer seed and ensure the weight matrix has the
  same non-zero coordinates and ordering as the interactions matrix.
- Coalesce duplicate coordinates before splitting when coordinate-level
  disjointness matters; duplicate entries for the same `(user, item)` can be
  separated by an entry-level split and then trigger intersection checks.

See [workflows](workflows.md) for split/evaluation recipes and
[troubleshooting](troubleshooting.md) for common failures.
