# LightFM model-training workflows

All snippets are self-contained and avoid network downloads. Replace tiny matrices with the user’s prepared sparse matrices. If raw ids or metadata features are involved, prepare them through [`../../data-features/SKILL.md`](../../data-features/SKILL.md); if metrics or data splits are the main task, use [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md).

## 1. Tiny in-memory smoke workflow

Run the bundled smoke script from the `model-training` sub-skill directory, or pass the same script path from any directory where `lightfm`, `numpy`, and `scipy` are installed:

```bash
python scripts/tiny_lightfm_smoke.py --loss warp --epochs 3 --threads 1
```

It trains on a deterministic in-memory matrix, checks finite predictions/embeddings, and prints a small precision summary. For manual equivalent code:

```python
import numpy as np
import scipy.sparse as sp
from lightfm import LightFM

shape = (4, 6)
train = sp.coo_matrix(
    (
        np.ones(8, dtype=np.float32),
        ([0, 0, 1, 1, 2, 2, 3, 3], [0, 1, 1, 2, 3, 4, 4, 5]),
    ),
    shape=shape,
)

model = LightFM(loss="warp", no_components=8, random_state=42)
model.fit(train, epochs=5, num_threads=1)

scores = model.predict(0, np.arange(shape[1], dtype=np.int32))
known = train.tocsr()[0].indices
scores[known] = -np.inf
print(np.argsort(-scores)[:3])
```

## 2. Implicit feedback ranking

Use `warp` or `bpr` when non-zero entries mean observed positive feedback, such as clicks, purchases, plays, or ratings above a threshold.

```python
from lightfm import LightFM

model = LightFM(
    loss="warp",
    no_components=32,
    learning_schedule="adagrad",
    learning_rate=0.05,
    item_alpha=1e-6,
    user_alpha=1e-6,
    max_sampled=20,
    random_state=2024,
)
model.fit(interactions, epochs=20, num_threads=4)
```

Operational notes:

- `warp` often performs well for top-k recommendations but each epoch can get slower as the model improves because it must sample more negatives to find rank violations.
- `bpr` is usually simpler and often faster per epoch; try it when WARP is too slow or AUC-style ranking is the target.
- For validation loops, call `fit_partial(..., epochs=1)` and measure after each epoch through [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md).
- Do not pass unbounded counts as if they were explicit ratings. If counts express confidence, use `sample_weight` or normalized features.

## 3. Explicit positive/negative logistic training

Use `loss="logistic"` when the interaction matrix contains both positives and negatives, commonly `1.0` and `-1.0`.

```python
import numpy as np
import scipy.sparse as sp
from lightfm import LightFM

rows = np.array([0, 0, 1, 1, 2, 2], dtype=np.int32)
cols = np.array([0, 4, 1, 5, 2, 3], dtype=np.int32)
labels = np.array([1, -1, 1, -1, 1, -1], dtype=np.float32)
explicit = sp.coo_matrix((labels, (rows, cols)), shape=(3, 6))

model = LightFM(loss="logistic", random_state=7)
model.fit(explicit, epochs=10, num_threads=1)
```

Keep negative labels deliberate: an unobserved interaction is not automatically a negative label unless the problem definition says it is.

## 4. Loss and schedule tuning loop

Use `fit_partial` to train one epoch at a time and keep validation outside the training matrix. Metric details are routed to [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md), but this pattern shows the model side of the loop:

```python
from lightfm import LightFM
from lightfm.evaluation import auc_score

candidates = [
    {"loss": "warp", "learning_schedule": "adagrad", "max_sampled": 10},
    {"loss": "warp", "learning_schedule": "adadelta", "rho": 0.95, "epsilon": 1e-6},
    {"loss": "bpr", "learning_schedule": "adagrad"},
]

for params in candidates:
    model = LightFM(no_components=32, random_state=13, **params)
    history = []
    for epoch in range(20):
        model.fit_partial(train, epochs=1, num_threads=4)
        score = auc_score(model, validation, train_interactions=train, num_threads=4).mean()
        history.append(float(score))
    print(params, max(history), history.index(max(history)) + 1)
```

Tuning heuristics:

- If validation peaks early and then drops, stop earlier or increase `item_alpha`/`user_alpha` slightly.
- If WARP epochs become very slow, reduce `max_sampled` and compare validation quality.
- If `adadelta` learns faster initially but stalls, compare against `adagrad` for the final selected epoch budget.
- If all scores become non-finite, lower `learning_rate` and normalize features/weights.

## 5. Resuming training with `fit_partial`

`fit` resets state. `fit_partial` keeps the current embeddings, optimizer accumulators, and random-state progression.

```python
from lightfm import LightFM

model = LightFM(loss="warp", random_state=42)
for epoch in range(10):
    model.fit_partial(train, epochs=1, num_threads=1)
    # evaluate/checkpoint here

# Continue later with the same interaction shape and feature schema.
model.fit_partial(train, epochs=5, num_threads=1)
```

When using side features, persist and reuse the exact mapping/feature-column schema. Changing the number or meaning of feature columns between resume calls invalidates the model state.

## 6. Top-item prediction and serving cache

`predict` scores pairs, not all combinations. For one user and all items:

```python
import numpy as np

n_items = interactions.shape[1]
user_id = 0
scores = model.predict(user_id, np.arange(n_items), num_threads=1)

# Optional: remove items already known to the user.
known_items = interactions.tocsr()[user_id].indices
scores[known_items] = -np.inf

top_k = np.argsort(-scores)[:10]
```

For many users, batch ids explicitly:

```python
users = np.asarray([10, 20, 30], dtype=np.int32)
items = np.arange(n_items, dtype=np.int32)
all_scores = model.predict(
    np.repeat(users, len(items)),
    np.tile(items, len(users)),
    num_threads=4,
).reshape(len(users), len(items))
```

If the model was trained with `user_features` or `item_features`, pass matching feature matrices at prediction time.

## 7. Representation export and manual score check

Use representations for diagnostics and retrieval. With identity features, representation rows correspond to internal user/item ids.

```python
item_biases, item_embeddings = model.get_item_representations(item_features)
user_biases, user_embeddings = model.get_user_representations(user_features)

u = 0
i = 3
manual = (user_embeddings[u] * item_embeddings[i]).sum()
manual += user_biases[u] + item_biases[i]
api_score = model.predict(u, [i])[0]
assert abs(float(manual - api_score)) < 1e-5
```

If `item_features`/`user_features` are metadata matrices, the returned rows are feature-weighted item/user representations, not raw feature embedding rows.

## 8. Optional ANN workflow from embeddings

Approximate nearest-neighbour libraries are optional and are not required by LightFM. Keep imports lazy and keep `predict` or exact vector search as a fallback.

Annoy-style item-to-item index sketch:

```python
import numpy as np

_, item_embeddings = model.get_item_representations(item_features)

try:
    from annoy import AnnoyIndex
except ImportError:
    AnnoyIndex = None

if AnnoyIndex is not None:
    index = AnnoyIndex(item_embeddings.shape[1], "angular")
    for item_id, vector in enumerate(item_embeddings):
        index.add_item(int(item_id), vector.astype("float32"))
    index.build(10)
    similar_item_ids = index.get_nns_by_item(0, 10)
else:
    # Exact fallback for small/medium item sets.
    scores = item_embeddings @ item_embeddings[0]
    similar_item_ids = np.argsort(-scores)[:10]
```

NMSLIB-style sketch:

```python
_, item_embeddings = model.get_item_representations(item_features)

try:
    import nmslib
except ImportError:
    nmslib = None

if nmslib is not None:
    index = nmslib.init(method="hnsw", space="cosinesimil")
    index.addDataPointBatch(item_embeddings)
    index.createIndex(print_progress=False)
    similar_item_ids, distances = index.knnQuery(item_embeddings[0], k=10)
```

For user-to-item ANN recommendation, an exact `predict` call remains the easiest correctness baseline. If transforming vectors to support maximum-inner-product search, document and test the transformation against exact `predict` rankings.

## 9. Sample weights

`sample_weight` must be a COO matrix with exactly the same `.row` and `.col` arrays as `interactions.tocoo()`.

```python
import numpy as np
import scipy.sparse as sp

train_coo = interactions.tocoo()
weights = np.ones(train_coo.nnz, dtype=np.float32)
weights[high_confidence_mask] = 3.0

sample_weight = sp.coo_matrix(
    (weights, (train_coo.row, train_coo.col)),
    shape=train_coo.shape,
)

model = LightFM(loss="warp", random_state=42)
model.fit_partial(train_coo, sample_weight=sample_weight, epochs=10)
```

Do not use `sample_weight` with `loss="warp-kos"`; it raises `NotImplementedError`.

## 10. Pickling and deployment bundle

Pickle the fitted model, and separately persist everything needed to rebuild candidate ids/features.

```python
import pickle

with open("lightfm_model.pkl", "wb") as f:
    pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("lightfm_model.pkl", "rb") as f:
    restored = pickle.load(f)
```

Bundle checklist:

- fitted `LightFM` object;
- internal user/item id mappings;
- feature vocabulary and feature matrix recipe;
- training-time `loss`, `no_components`, `learning_schedule`, regularization, and seed;
- candidate-filter policy for already-seen items;
- optional ANN index build parameters and exact-predict fallback.

Mappings and feature recipes are handled by [`../../data-features/SKILL.md`](../../data-features/SKILL.md).

## 11. Sklearn-style parameter search

`LightFM` exposes `get_params` and `set_params`, so sklearn search wrappers can work when scoring and cross-validation preserve sparse matrix shape.

```python
import numpy as np
from scipy import stats
from sklearn.model_selection import KFold, RandomizedSearchCV
from lightfm import LightFM
from lightfm.evaluation import precision_at_k

model = LightFM(loss="warp", random_state=42)
param_distributions = {
    "no_components": stats.randint(low=8, high=65),
    "learning_rate": stats.gamma(a=1.2, loc=0, scale=0.13),
}

def scorer(estimator, x, y=None):
    return float(precision_at_k(estimator, x, k=10).mean())

class ShapePreservingCV(KFold):
    def split(self, X, y=None, groups=None):
        idx = np.arange(X.shape[0])
        for _ in range(self.n_splits):
            yield idx, idx

search = RandomizedSearchCV(
    estimator=model,
    param_distributions=param_distributions,
    n_iter=8,
    scoring=scorer,
    cv=ShapePreservingCV(n_splits=3, shuffle=True, random_state=42),
    random_state=42,
)
search.fit(train)
```

For realistic evaluation, prefer explicit train/test matrices and leakage checks from [`../../evaluation-splitting/SKILL.md`](../../evaluation-splitting/SKILL.md).
