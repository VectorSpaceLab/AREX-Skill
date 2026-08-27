# Evaluation and splitting workflows

Use these workflows after a `lightfm.LightFM` model has already been fit. For
training decisions, read [model-training](../../model-training/SKILL.md). For
building mappings, interaction matrices, or feature matrices, read
[data-features](../../data-features/SKILL.md).

## 1. Leakage-safe offline evaluation

Use this pattern for ordinary held-out test evaluation.

```python
import numpy as np
from lightfm.evaluation import auc_score, precision_at_k, recall_at_k, reciprocal_rank

# train_interactions and test_interactions are SciPy sparse matrices with the
# same (n_users, n_items) shape. The model was fit on train_interactions.
assert train_interactions.shape == test_interactions.shape
assert train_interactions.multiply(test_interactions).nnz == 0

metrics = {
    "precision@10": precision_at_k(
        model,
        test_interactions,
        train_interactions=train_interactions,
        k=10,
        num_threads=1,
        check_intersections=True,
    ),
    "recall@10": recall_at_k(
        model,
        test_interactions,
        train_interactions=train_interactions,
        k=10,
        num_threads=1,
        check_intersections=True,
    ),
    "auc": auc_score(
        model,
        test_interactions,
        train_interactions=train_interactions,
        num_threads=1,
        check_intersections=True,
    ),
    "reciprocal_rank": reciprocal_rank(
        model,
        test_interactions,
        train_interactions=train_interactions,
        num_threads=1,
        check_intersections=True,
    ),
}

summary = {name: float(values.mean()) for name, values in metrics.items()}
```

Why this is safe:

- `train_interactions` excludes known training positives from the ranking
  candidates.
- `check_intersections=True` catches leaked coordinates before returning a
  metric.
- Default `preserve_rows=False` averages only over users with held-out positives.

If the model was trained with features, pass the same compatible feature
matrices to every metric call:

```python
precision = precision_at_k(
    model,
    test_interactions,
    train_interactions=train_interactions,
    item_features=item_features,
    user_features=user_features,
    k=10,
)
```

## 2. Random split with validation

`random_train_test_split` is useful for fast experiments when temporal leakage is
not the main concern.

```python
from lightfm.cross_validation import random_train_test_split

interactions = interactions.tocoo()
interactions.sum_duplicates()  # avoid duplicate coordinates being split apart

train, test = random_train_test_split(
    interactions,
    test_percentage=0.2,
    random_state=42,
)

train = train.tocsr()
test = test.tocsr()

if train.multiply(test).nnz:
    raise ValueError("train/test split contains overlapping non-zero entries")

model.fit(train, epochs=10, num_threads=1)
test_precision = precision_at_k(
    model,
    test,
    train_interactions=train,
    k=10,
    check_intersections=True,
).mean()
```

Cautions:

- The splitter does not guarantee that every held-out user or item appears in
  train. For recommender validation that must avoid cold-start artifacts, build
  a user-aware or time-aware split yourself and then apply the same intersection
  check.
- The splitter works at the non-zero entry level. If the input contains
  duplicate coordinates, aggregate them first.
- For tiny matrices, the realized fraction can differ from `test_percentage`
  because the cutoff is integer-rounded.

## 3. Splitting sample weights consistently

LightFM training can use `sample_weight`; evaluation metrics do not use weights.
If training weights must be split the same way as interactions, use the same
seed and matching non-zero structure.

```python
seed = 123
train_interactions, test_interactions = random_train_test_split(
    interactions,
    test_percentage=0.2,
    random_state=seed,
)
train_weights, test_weights = random_train_test_split(
    sample_weight_matrix,
    test_percentage=0.2,
    random_state=seed,
)

# The weight matrix must have the same non-zero coordinates/order as the
# interaction matrix before splitting.
assert (train_interactions.row == train_weights.row).all()
assert (train_interactions.col == train_weights.col).all()

model.fit(train_interactions, sample_weight=train_weights, epochs=10)
```

Use a fresh integer seed (or a fresh `RandomState` initialized with the same
seed) for each split. Reusing the same mutable `RandomState` object after it has
already been consumed advances its state and will not reproduce the same split.

## 4. User-preserving metrics

Set `preserve_rows=True` when the output array must remain indexed by user id.
Always keep a mask for users with at least one held-out positive before
aggregating.

```python
row_has_test = test_interactions.getnnz(axis=1) > 0

precision_by_user = precision_at_k(
    model,
    test_interactions,
    train_interactions=train_interactions,
    k=5,
    preserve_rows=True,
)
recall_by_user = recall_at_k(
    model,
    test_interactions,
    train_interactions=train_interactions,
    k=5,
    preserve_rows=True,
)

precision_mean = precision_by_user[row_has_test].mean()
recall_mean = recall_by_user[row_has_test].mean()
```

Do not average unmasked user-preserving recall when some users have no test
positives; those rows have no recall denominator.

## 5. Interpreting `predict_rank`

`predict_rank` returns ranks only for the entries you ask it to evaluate.

```python
ranks = model.predict_rank(
    test_interactions,
    train_interactions=train_interactions,
    check_intersections=True,
)

# For each stored value, 0 is best; a hit at k has rank < k.
hit_mask = ranks.data < 10
```

Important interpretation rules:

- The returned matrix has the same shape and non-zero coordinates as
  `test_interactions`.
- `rank == 0` means the item is the top recommendation after filtering training
  positives.
- Top-k metrics count ranks `< k`.
- Ties are pessimistic. Equal item scores receive worst-case ranks, so a model
  with all-zero embeddings/biases can score poorly even if positives exist.
- If you need scores for every item for one user, use `LightFM.predict` rather
  than constructing a dense `test_interactions` matrix just to call
  `predict_rank`.

## 6. Choosing a split policy

| Validation goal | Split policy | Metric setup |
| --- | --- | --- |
| Quick smoke test | `random_train_test_split` with fixed seed | Pass `train_interactions`, keep `check_intersections=True`, compare finite means. |
| Offline benchmark without time order | Random split, preferably stratified/user-aware outside LightFM if each user must remain represented | Validate disjointness and mask zero-test rows. |
| Production-like next-item or future-period evaluation | Chronological holdout built by the caller | Do not use random split; still keep shape/mapping aligned and pass training positives to metrics. |
| Cold-start or hybrid feature evaluation | Hold out selected cold users/items and supply feature matrices | Confirm the model has informative features; route feature construction to [data-features](../../data-features/SKILL.md). |

## 7. Running the bundled fixture

The bundled fixture script trains a tiny model, computes all metrics, validates
an entry-level random split, and can show the expected intersection error.

From this sub-skill directory:

```bash
python scripts/evaluate_lightfm_fixture.py --help
python scripts/evaluate_lightfm_fixture.py
python scripts/evaluate_lightfm_fixture.py --demonstrate-intersection
```

See [API details](api-reference.md) for exact return semantics and
[troubleshooting](troubleshooting.md) when the fixture exposes an error that
matches a user problem.
