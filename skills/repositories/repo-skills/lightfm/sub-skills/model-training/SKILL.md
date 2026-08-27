---
name: model-training
description: "Train, resume, tune, inspect, serialize, score, and troubleshoot
  LightFM recommendation models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightFM model training sub-skill

Use this sub-skill when the task is to train or operate a `lightfm.LightFM` model: choose a loss, fit or resume training, score items, inspect embeddings, serialize the model, tune regularization or schedules, use sample weights, or export representations for nearest-neighbour retrieval.

## Route map

- **Use this sub-skill for:** `LightFM(...)`, `fit`, `fit_partial`, `predict`, `predict_rank` usage notes, `get_user_representations`, `get_item_representations`, sample weights, `random_state`, `num_threads`, pickling, sklearn-style parameters, and optional ANN indexing from trained embeddings.
- **Route dataset mappings and feature matrices to:** [`../data-features/SKILL.md`](../data-features/SKILL.md). This includes `Dataset`, raw user/item ids, identity features, metadata features, and feature-shape preparation.
- **Route metrics and splits to:** [`../evaluation-splitting/SKILL.md`](../evaluation-splitting/SKILL.md). This includes `precision_at_k`, `auc_score`, train/test split construction, and evaluation leakage checks. This sub-skill only notes when model APIs feed evaluation.
- **Route build, Cython, OpenMP, and packaging maintenance to:** [`../repo-development/SKILL.md`](../repo-development/SKILL.md).

## Fast workflow

1. Prepare `interactions` as a SciPy sparse user-item matrix. Use [`../data-features/SKILL.md`](../data-features/SKILL.md) if raw ids or feature matrices are involved.
2. Pick a loss:
   - `warp` for implicit top-k ranking, often a strong default.
   - `bpr` for implicit ranking/AUC-style objectives and usually faster epochs than WARP.
   - `logistic` when interactions include both positive `1` and negative `-1` labels.
   - `warp-kos` for k-order statistic WARP experiments; do not combine it with `sample_weight`.
3. Train with `model.fit(...)` for a fresh model or `model.fit_partial(...)` to resume from current weights.
4. Score candidate pairs with `model.predict(user_ids, item_ids, ...)`; pass repeated user ids when ranking many items for one user.
5. Inspect/export representations with `get_item_representations(...)` and `get_user_representations(...)`; preserve the same feature schema used at training time.
6. Use [`references/workflows.md`](references/workflows.md) for concrete snippets and [`scripts/tiny_lightfm_smoke.py`](scripts/tiny_lightfm_smoke.py) for a no-network smoke run.

## Decision points

- **Fresh versus resumed training:** `fit` resets existing learned state; `fit_partial` keeps state and advances training. Use `fit_partial` for epoch-by-epoch validation, checkpointing, and warm starts.
- **Feature shape continuity:** when resuming or predicting with side features, the feature matrices must have compatible rows and the same feature-column meaning as training.
- **Regularization:** if train quality is high but validation quality degrades, try lower `no_components`, early stopping, or small `item_alpha`/`user_alpha`. If learned weights collapse toward zero, regularization may be too strong.
- **Threads:** LightFM is CPU-only. `num_threads` must be at least `1`; keep it no larger than physical cores and use `1` when reproducibility/debugging matters.
- **ANN retrieval:** approximate nearest-neighbour libraries are optional operational add-ons. Build indexes only after extracting trained item/user embeddings; keep exact `predict` as the correctness fallback.

## References

- [`references/api-reference.md`](references/api-reference.md): signatures, parameter tables, returns, and gotchas.
- [`references/workflows.md`](references/workflows.md): minimal in-memory, implicit, explicit, tuning, resume, representation, ANN, sample-weight, pickling, and sklearn snippets.
- [`references/troubleshooting.md`](references/troubleshooting.md): common exceptions, shape mismatches, NaNs/divergence, WARP speed, popularity collapse, threads, CPU-only, and optional ANN imports.
- [`scripts/tiny_lightfm_smoke.py`](scripts/tiny_lightfm_smoke.py): deterministic local smoke script with no downloads.
