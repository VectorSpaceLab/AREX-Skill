---
name: lightfm
description: "Operate LightFM recommendation models, data/feature matrices,
  evaluation metrics, and repository maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightFM repo skill

Use this skill when a task involves the `lightfm` Python package: building hybrid recommendation inputs, training or scoring `LightFM` models, evaluating ranking metrics, or maintaining the LightFM source checkout.

LightFM is a CPU-only recommender-system package. It implements hybrid matrix-factorization models for implicit and explicit feedback, including `logistic`, `bpr`, `warp`, and `warp-kos` losses. It can combine user/item identity features with side metadata so models can handle cold-start or metadata-aware recommendations when the feature schema is planned correctly.

## Start here

1. Install the package in an isolated Python environment:

   ```bash
   python -m pip install lightfm
   # or, for conda users
   conda install -c conda-forge lightfm
   ```

   For source checkout maintenance, use the [`repo-development`](sub-skills/repo-development/SKILL.md) route instead of the end-user install path.

2. Run a minimal import and CPU smoke check:

   ```bash
   python scripts/check_lightfm_environment.py --tiny-run
   ```

3. Choose the route below based on the user's task. Read the nearest sub-skill before giving detailed commands or API advice.

## Route map

| User task or signal | Read this |
| --- | --- |
| Train a `LightFM` model, choose `warp`/`bpr`/`logistic`, resume with `fit_partial`, predict recommendations, inspect embeddings, handle sample weights, tune regularization, serialize a model, or use optional ANN indexes from representations. | [`sub-skills/model-training/SKILL.md`](sub-skills/model-training/SKILL.md) |
| Convert raw user/item ids, interactions, weights, metadata, or built-in MovieLens/StackExchange data into LightFM sparse matrices and feature mappings; design cold-start user/item features. | [`sub-skills/data-features/SKILL.md`](sub-skills/data-features/SKILL.md) |
| Split interactions, compute `precision_at_k`, `recall_at_k`, `auc_score`, `reciprocal_rank`, use `predict_rank`, preserve user rows, or debug train/test intersection leakage. | [`sub-skills/evaluation-splitting/SKILL.md`](sub-skills/evaluation-splitting/SKILL.md) |
| Work on the LightFM repository itself: editable install, compiled extension/OpenMP/no-OpenMP behavior, Cython regeneration, focused tests, docs, lint, CI, or build failures. | [`sub-skills/repo-development/SKILL.md`](sub-skills/repo-development/SKILL.md) |

## Common package workflow

1. Build or load a SciPy sparse interactions matrix. If raw ids or metadata are involved, use [`data-features`](sub-skills/data-features/SKILL.md) to create stable mappings and feature matrices.
2. Instantiate `LightFM(...)`. Use `loss="warp"` for many implicit top-k tasks, `loss="bpr"` for implicit pairwise ranking/AUC-style objectives, and `loss="logistic"` when explicit positive and negative labels are represented in `interactions.data`.
3. Fit with `model.fit(...)` for a fresh model or `model.fit_partial(...)` for resumed/epoch-by-epoch training. Pass `user_features` and/or `item_features` consistently whenever the model was trained with side features.
4. Score items with `model.predict(user_ids, item_ids, ...)` or rank sparse held-out interactions with `predict_rank`/evaluation utilities.
5. Evaluate with a disjoint train/test split and `train_interactions=train` so known positives are excluded from test rankings.

## Important constraints

- There is no GPU implementation. OpenMP is only CPU multithreading; do not install CUDA packages or promise GPU acceleration for LightFM.
- Feature column schemas are model state. Adding new user/item feature names after training changes the embedding dimensions and normally requires retraining or a deliberate model-resize workflow.
- `Dataset.build_interactions` returns both an interactions matrix and a weights matrix. If using `sample_weight`, the weight COO entries must have the same shape and entry order as the interactions COO matrix.
- Evaluation treats non-zero test entries as positives. Remove negative labels before ranking metrics unless you intentionally evaluate on the training labels.
- Built-in dataset fetchers may download public data. For offline or deterministic checks, use the bundled tiny scripts instead of MovieLens/StackExchange downloads.

## Bundled references and scripts

- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting install/import, CPU/OpenMP, dataset download, feature schema, and evaluation leakage guidance.
- [`references/repo-provenance.md`](references/repo-provenance.md): source snapshot and refresh baseline for this generated skill.
- [`scripts/check_lightfm_environment.py`](scripts/check_lightfm_environment.py): package import/version/compiled-extension/tiny-fit diagnostic.

## When not to use this skill

- The task is about a different recommender package such as implicit, Surprise, LensKit, RecBole, Cornac, or a deep-learning recommender framework without LightFM APIs.
- The task is pure database/product ranking design with no `lightfm` package usage.
- The user asks to export this generated repo skill into another agent tool; use the managed repo-skill import/export workflow instead.
