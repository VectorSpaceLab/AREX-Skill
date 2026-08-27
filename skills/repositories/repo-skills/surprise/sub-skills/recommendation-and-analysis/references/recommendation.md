# Recommendation and analysis

This route starts after a model has been fitted, or when you already have a `Prediction` list.

## 1. Build candidate recommendations

`Trainset.build_anti_testset(fill=None)` returns all known `(raw_uid, raw_iid, fill)` pairs that are not in the trainset.

- `fill=None` uses `trainset.global_mean`.
- `fill` is converted to `float`.
- The returned ids are raw ids, not inner ids.
- For a trainset with `n_users`, `n_items`, and `n_ratings`, the anti-testset length is `n_users * n_items - n_ratings`.

A quick check:

```python
anti = trainset.build_anti_testset()
assert len(anti) == trainset.n_users * trainset.n_items - trainset.n_ratings
assert all(r == trainset.global_mean for _, _, r in anti)
```

If a user has rated every known item, that user contributes no candidate pairs and will not appear later in grouped recommendation output unless you pre-seed the result mapping.

## 2. Rank top-N items

The canonical pattern is:

```python
from collections import defaultdict


def get_top_n(predictions, n=10):
    top_n = defaultdict(list)
    for uid, iid, _, est, _ in predictions:
        top_n[uid].append((iid, est))

    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]
    return top_n
```

Notes:
- Group by raw `uid`.
- Sort on the estimated score only.
- Python's sort is stable, so tied scores keep their original order.
- If the candidate set is empty for a user, that user is absent from the mapping.

## 3. Interpret Prediction outputs

`algo.predict(...)` and `algo.test(...)` return `Prediction` objects:
`Prediction(uid, iid, r_ui, est, details)`.

- `uid` and `iid` are raw ids.
- `r_ui` is the known true rating when available, otherwise `None`.
- `est` is the score used for ranking.
- `details` is a dict, usually including `was_impossible` and sometimes `reason`.

Use `Prediction` objects directly when you want ranking, analysis, or serialization.
If you only need item order, read `uid`, `iid`, and `est`.

## 4. Compute precision@k and recall@k

The standard per-user pattern mirrors the docs example:

- relevant if `true_r >= threshold`
- recommended if `est >= threshold`
- take the top `k` predictions after sorting by `est` descending

Zero-division convention:

- precision is `0` when a user has no recommended items in the top `k`
- recall is `0` when a user has no relevant items

When averaging, guard the empty-dictionary case before dividing.

## 5. Serialize predictions or algorithms

`dump.dump(path, predictions=..., algo=...)` stores a pickle file containing a dictionary with those two keys.
`dump.load(path)` returns `(predictions, algo)`.

Recommended roundtrip pattern:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from surprise import dump

with TemporaryDirectory() as tmpdir:
    path = Path(tmpdir) / "surprise_dump.pkl"
    dump.dump(str(path), predictions=predictions, algo=algo)
    loaded_predictions, loaded_algo = dump.load(str(path))
    assert predictions == loaded_predictions
```

Best practices:
- use a temporary directory or a `try/finally` cleanup
- do not load untrusted pickle files
- verify the loaded algorithm against the same testset if you need to confirm equivalence

## 6. Native validation anchors

- `tests/test_dataset.py`: anti-testset fill defaults, expected sizes, and raw-id roundtrips.
- `tests/test_dump.py`: prediction and algorithm dump/load roundtrips plus `None` defaults.

## 7. Cross-links

If you still need to build a trainset, see the data-loading route.
If you still need to fit or configure the algorithm, see the prediction-algorithms route.
