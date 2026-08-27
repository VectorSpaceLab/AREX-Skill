# Evaluation and splitting troubleshooting

Use this guide when LightFM ranking metrics fail, look too good to be true, or
produce confusing shapes/values. For API signatures and return semantics, see
[api-reference](api-reference.md). For full recipes, see [workflows](workflows.md).

## Train/test intersection `ValueError`

**Symptom**

Metric calls or `predict_rank` raise a message like:

```text
Test interactions matrix and train interactions matrix share ... interactions.
This will cause incorrect evaluation, check your data split.
```

**Cause**

At least one `(user_id, item_id)` coordinate is non-zero in both
`test_interactions` and `train_interactions`. LightFM detects this when
`check_intersections=True` and `train_interactions` is supplied.

**Fix**

```python
overlap = train_interactions.multiply(test_interactions).nnz
if overlap:
    raise ValueError(f"{overlap} train/test coordinates overlap")
```

Then rebuild the split so every positive entry belongs to exactly one side.
Common root causes are duplicate COO coordinates, merging train/test files twice,
using the training matrix as the test matrix, or splitting interactions and
weights with different random states.

Only set `check_intersections=False` for intentional diagnostics, not for
reported leakage-safe test scores.

## Test metrics look unrealistically high

**Likely causes**

- `train_interactions` was omitted, so already-known positives remained in the
  recommendation candidate set.
- Train and test matrices overlap, and intersection checks were disabled.
- Evaluation is being run on the training matrix but reported as test quality.
- Negative feedback values are non-zero and are therefore being treated as
  positives.
- Random entry-level splitting is too easy for the production question; temporal
  leakage may remain even when coordinates are disjoint.

**Fix**

Pass `train_interactions=train`, keep `check_intersections=True`, zero-out
non-positive feedback before ranking metrics, and use a split policy that
matches the intended deployment setting.

## Empty metric arrays or missing users

**Symptom**

A metric returns an empty array, or its length is smaller than `n_users`.

**Cause**

The default `preserve_rows=False` removes users with no non-zero entries in
`test_interactions`. This is usually desirable for aggregate means because users
without held-out positives are not evaluable by top-k recall-like metrics.

**Fix**

- Check `test_interactions.getnnz(axis=1)` to see which rows have positives.
- Use `preserve_rows=True` only when you need user-axis alignment.
- Keep a `row_has_test` mask and aggregate only over true held-out-positive rows.
- If a split left too many users without test positives, use a user-aware split
  instead of entry-level random splitting.

## Zero rows and undefined recall

**Symptom**

User-preserving recall contains non-finite values or gives misleading means.

**Cause**

Recall divides by the number of test positives for each user. Users with zero
test positives have no valid recall denominator. The default row filtering avoids
this; `preserve_rows=True` exposes those rows so you can align arrays by user id.

**Fix**

```python
row_has_test = test_interactions.getnnz(axis=1) > 0
recall_by_user = recall_at_k(..., preserve_rows=True)
recall_mean = recall_by_user[row_has_test].mean()
```

If an application needs a filled user-aligned array, fill zero-test rows only
after computing the masked aggregate and clearly document the fill policy.

## Non-sparse or wrong sparse input

**Symptom**

`random_train_test_split` raises `ValueError: Interactions must be a scipy.sparse
matrix`, or metric calls fail with shape/attribute errors.

**Cause**

LightFM evaluation expects SciPy sparse interaction matrices. Dense arrays are
not valid input for splitting and are inefficient or invalid for ranking.

**Fix**

Convert tabular `(user, item, value)` records into a SciPy sparse matrix through
[data-features](../../data-features/SKILL.md). Use CSR for repeated row access
and COO when constructing matrices:

```python
interactions = interactions.tocoo()
interactions.sum_duplicates()
train, test = random_train_test_split(interactions, random_state=42)
train = train.tocsr()
test = test.tocsr()
```

## Feature or shape mismatch

**Symptom**

`predict_rank` or a metric reports incorrect feature counts, mismatched shapes,
or an uninitialized/not-fitted model error.

**Cause**

The model, interaction matrices, and optional feature matrices do not describe
the same dimensions. If the model was trained with custom feature matrices,
evaluation must use compatible matrices; identity-feature inference only works
when dimensions match the trained model.

**Fix**

- Confirm `train_interactions.shape == test_interactions.shape`.
- Confirm feature matrix row counts match `n_users` and `n_items` for the
  evaluation interactions.
- Confirm feature matrix column counts match the feature space used during fit.
- Route feature construction or mapping alignment issues to
  [data-features](../../data-features/SKILL.md).
- Route not-fitted model or training-state issues to
  [model-training](../../model-training/SKILL.md).

## `num_threads` errors or disappointing parallel speed

**Symptom**

A call raises `ValueError: Number of threads must be 1 or larger`, or increasing
`num_threads` does not speed up evaluation.

**Cause**

`num_threads` must be a positive integer. LightFM is a CPU package; GPU settings
will not accelerate metrics. Parallel speedups depend on the installed compiled
extension and workload size.

**Fix**

Use `num_threads=1` for deterministic small fixtures and increase only for large
matrices on a CPU build that benefits from multithreading. Do not exceed the
number of physical cores.

## Pessimistic ties and all-zero scores

**Symptom**

`predict_rank` assigns very poor ranks to positives, or `precision_at_k` is zero
even though the test matrix has positives.

**Cause**

LightFM ranks ties pessimistically. If all items have equal scores, every tied
item can receive the worst rank, so no item falls into the top `k`.

**Fix**

Check whether the model is trained and whether embeddings/biases are all zero or
nearly identical. If training quality is the issue, route to
[model-training](../../model-training/SKILL.md). For evaluation interpretation,
remember that a hit requires `rank < k`.

## AUC near `0.5`

**Symptom**

AUC is close to random even when precision seems non-zero, or user-preserving
AUC contains uninformative rows.

**Cause**

AUC measures whether positives score above unobserved candidate items. A random
or weak model scores around `0.5`. Users without test positives are not useful
for aggregate AUC and should be masked when preserving rows.

**Fix**

Compare train and test AUC using the same filtering setup. If train AUC is also
near `0.5`, debug model training. If train AUC is high and test AUC is random,
check split policy, cold-start users/items, feature availability, and
overfitting.

## Random split creates cold-start rows or items

**Symptom**

Some test users/items have no training interactions, causing unexpectedly low
or unstable metrics.

**Cause**

`random_train_test_split` makes no effort to keep every user or item represented
in train. It randomly assigns non-zero entries to train/test.

**Fix**

For warm-start evaluation, build a custom split that enforces at least one train
positive per evaluated user/item. For deliberate cold-start or hybrid evaluation,
ensure informative features are supplied and route feature design to
[data-features](../../data-features/SKILL.md).

## Slow or memory-heavy ranking

**Symptom**

`predict_rank` is slow or memory-heavy when trying to rank every item for every
user.

**Cause**

`predict_rank` computes ranks for non-zero entries in `test_interactions`. It is
best when only a small held-out set of positives per user needs ranks. Dense
all-item rank requests are expensive.

**Fix**

For user recommendation lists or all-item score vectors, call `LightFM.predict`
for the target user and candidate items through
[model-training](../../model-training/SKILL.md). Reserve `predict_rank` for
metric computation on sparse held-out positives.
