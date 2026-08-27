---
name: evaluation-splitting
description: "Evaluate fitted LightFM recommenders and create leakage-safe
  train/test splits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightFM evaluation and splitting

Use this sub-skill when a task is about offline ranking metrics, train/test
splits, or debugging leakage in a fitted LightFM recommender.

## Read when

- Compute `precision_at_k`, `recall_at_k`, `auc_score`, `reciprocal_rank`, or
  `LightFM.predict_rank` for a fitted model.
- Split an interactions matrix with `random_train_test_split` and validate that
  train and test interactions do not overlap.
- Explain `train_interactions`, `check_intersections`, `preserve_rows`, metric
  output shapes, top-k behavior, rank values, or tie handling.
- Diagnose intersection `ValueError`, suspiciously high test metrics, empty
  metric arrays, zero-row users, sparse matrix input problems, or
  `num_threads` errors.

## Route elsewhere

- Training, tuning, resuming, serializing, direct `predict` scoring, or loss
  selection: read [model-training](../model-training/SKILL.md).
- Dataset mappings, feature matrix construction, built-in dataset fetchers,
  cold-start feature design, or interaction schemas: read
  [data-features](../data-features/SKILL.md).
- Repository build, editable install, compiled extension maintenance, native
  tests, or CI commands: read [repo-development](../repo-development/SKILL.md).

## Fast workflow

1. Start from a fitted `lightfm.LightFM` model and SciPy sparse train/test
   matrices with identical `(n_users, n_items)` shape. If the model was fit
   with user or item features, pass compatible feature matrices into the metric
   call as well.
2. Treat non-zero entries in `test_interactions` as positives to rank. Remove
   or zero-out negative feedback before ranking metrics; LightFM evaluation
   treats any non-zero entry as an interaction.
3. Pass `train_interactions=train` for test metrics so known training positives
   are excluded from the candidate ranking. Keep `check_intersections=True`
   unless performing an intentional diagnostic.
4. Choose `preserve_rows=False` for aggregate means over users with test
   positives, or `preserve_rows=True` when the output must stay aligned to the
   original user axis.
5. Inspect [API details](references/api-reference.md) for signatures, return
   shapes, sparse matrix expectations, intersection checks, and tie semantics.
6. Use [workflows](references/workflows.md) for leakage-safe split/evaluate
   recipes, user-preserving metrics, and `predict_rank` interpretation.
7. Use [troubleshooting](references/troubleshooting.md) when metrics error,
   look optimistic, contain zero/empty rows, or disagree with expected top-k
   behavior.

A deterministic, no-network fixture is bundled at
[scripts/evaluate_lightfm_fixture.py](scripts/evaluate_lightfm_fixture.py). It
trains a tiny CPU model, computes all ranking metrics, validates a random split,
and can intentionally demonstrate intersection handling.

## Non-negotiables for leakage-safe evaluation

- Do not average test metrics without checking that train/test matrices are
  disjoint at non-zero coordinates.
- Do not silence intersection checks just to get a score; fix the split unless
  the task is explicitly evaluating training-set ranking behavior.
- Do not compare metrics across runs unless `k`, split policy, feature matrices,
  `preserve_rows`, and train-interaction filtering are the same.
- Do not interpret random splits as temporal validation. Use a chronological or
  user-aware holdout when production evaluation requires it, then still validate
  intersections before scoring.
