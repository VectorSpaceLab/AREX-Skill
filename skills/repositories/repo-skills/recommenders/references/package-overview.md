# Package Overview

## Purpose

Read this for a compact map of Microsoft Recommenders modules, optional extras, and which sub-skill owns each workflow. The package provides utilities and examples for recommendation-system prototyping, evaluation, tuning, and operationalization.

## Installation variants

| Variant | Use when | Notes |
|---|---|---|
| Base `recommenders` | CPU data prep, Python metrics, SAR, TF-IDF, Cornac helpers, LightGBM helpers, notebook utilities | Verified for this skill's CPU inspection scope. |
| `recommenders[spark]` | Spark splitters, Spark metrics, Spark ALS, Spark LightGBM workflows | Requires Java/JDK and Spark/PySpark. |
| `recommenders[gpu]` | TensorFlow/PyTorch DeepRec, NewsRec, NCF, Wide&Deep, RBM, VAE, GPU utility checks | Requires compatible framework wheels and GPU runtime; CPU import is not GPU proof. |
| `recommenders[experimental]` | Surprise, LightFM, Vowpal Wabbit, xLearn, NNI, pymanopt and incubating models | May require native binaries, compilers, or extra system packages. |
| `recommenders[dev]` | Repo development and tests | Not needed for ordinary package use. |

## Module ownership

| Package area | Main responsibility | Skill owner |
|---|---|---|
| `recommenders.datasets` | Dataset loaders, download helpers, pandas/Spark splitters, sparse matrices, LibFFM conversion, negative sampling | `data-preparation` |
| `recommenders.evaluation` | Python and Spark rating/ranking/beyond-accuracy metrics | `evaluation` |
| `recommenders.models.sar`, `tfidf`, `cornac`, `lightgbm` | Lightweight CPU model and helper workflows | `modeling` |
| `recommenders.models.deeprec`, `newsrec`, `ncf`, `wide_deep`, `vae`, `rbm`, `sasrec` | Optional TensorFlow/PyTorch deep-learning, news, and sequential workflows | `modeling` with optional backend notes |
| `recommenders.tuning` | Parameter grids, NNI helpers, tuning utilities | `operations-and-tuning` |
| `recommenders.utils` | Timers, Python math helpers, notebook execution, Spark/GPU/K8s/TensorFlow utilities | Root or nearest sub-skill depending on task |

## Common task routing

- "Split my ratings by user and timestamp" -> `data-preparation`.
- "Train a SAR recommender and recommend top-k items" -> `modeling`, then `evaluation` for metrics.
- "Compute MAP@10 and nDCG@10" -> `evaluation`.
- "Which algorithm should I use for item text only?" -> `modeling` TF-IDF path.
- "Run Spark ALS" -> `modeling` plus optional Spark readiness in `operations-and-tuning`.
- "Tune NCF with NNI or AzureML" -> `operations-and-tuning` for execution plan, `modeling` for model/data assumptions.
- "Deploy recommendations through Databricks/Cosmos/AKS" -> `operations-and-tuning`.

## Verification baseline for this generated skill

The generated skill was verified against a CPU/base environment. It includes bundled no-network smoke helpers for:

- Interaction CSV schema validation.
- Python metric calculation.
- SAR fit/predict/recommend.
- TF-IDF content recommendation.
- Environment readiness reporting.

Optional Spark/GPU/cloud/experimental workflows are preserved as operating guidance and must be verified in a suitable future environment before execution claims.
