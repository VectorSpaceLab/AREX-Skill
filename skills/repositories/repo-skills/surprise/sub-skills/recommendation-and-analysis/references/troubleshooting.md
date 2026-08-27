# Troubleshooting

## Anti-testset size or fill looks wrong

**Symptom:** the anti-testset is smaller or larger than expected, or the fill value is surprising.

**Cause:** `build_anti_testset` only enumerates known users and items from the trainset. `fill=None` uses `trainset.global_mean`.

**Fix:**
- check `trainset.n_users`, `trainset.n_items`, and `trainset.n_ratings`
- expect `len(anti) == n_users * n_items - n_ratings`
- if you want a specific placeholder score, pass `fill=<float>`
- if a user or item is missing from the trainset, rebuild the trainset before ranking

## Top-N order or missing-user output looks odd

**Symptom:** tied items appear in an unexpected order, or some users are absent from the result.

**Cause:** the top-N helper sorts only on `est`, and Python keeps the input order for ties. Users with no candidates have no predictions to group.

**Fix:**
- rely on stable sort for deterministic tie handling
- if you need a key for every user, seed the output dict before grouping
- use raw ids from the `Prediction` objects, not inner ids

## precision@k / recall@k divide by zero

**Symptom:** one of the metrics is 0 or the helper would divide by zero.

**Cause:** a user had no recommended items in the top `k`, or no relevant items above the threshold.

**Fix:**
- return 0 when `n_rec_k == 0`
- return 0 when `n_rel == 0`
- when averaging, guard against an empty `precisions` or `recalls` dict
- keep the relevance threshold explicit in both the script and the report

## dump/load roundtrip is unsafe or leaves files behind

**Symptom:** a serialized model cannot be reloaded, or temp files accumulate.

**Cause:** `dump` and `load` use `pickle`, and the example wrote to a fixed path instead of a managed temp file.

**Fix:**
- only load files you trust
- use `TemporaryDirectory()` or `NamedTemporaryFile(delete=False)` with `finally` cleanup
- confirm the loaded algorithm reproduces the original predictions on the same testset
- remember that `dump.load` returns `(predictions, algo)`

## Raw vs inner id confusion

**Symptom:** `ValueError` from `to_inner_uid` / `to_inner_iid`, or recommendation output uses ids you cannot map back.

**Cause:** recommendation workflows operate on raw ids, while the trainset stores inner ids internally.

**Fix:**
- pass raw ids to `predict`, `test`, and the top-N output formatter
- use `Trainset.to_inner_uid/iid` only when you already know the id belongs to the trainset
- use `Trainset.to_raw_uid/iid` when converting inner ids for display
- check `Prediction.uid` and `Prediction.iid`; they are raw ids

## Smoke commands

```bash
python scripts/top_n_smoke.py
python scripts/precision_recall_smoke.py
python scripts/serialize_smoke.py
```
