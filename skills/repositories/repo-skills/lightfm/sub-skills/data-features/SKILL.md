---
name: data-features
description: "Build LightFM Dataset mappings, sparse interactions, weights,
  user/item feature matrices, built-in data loads, and cold-start feature
  inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightFM data-features

Use this sub-skill when the task is to turn external user/item ids, interaction records, sample weights, or user/item metadata into LightFM-ready sparse matrices and mappings.

## Route map

| Need | Go to |
| --- | --- |
| Build `Dataset` mappings, interactions, weights, user/item feature matrices, or cold-start feature rows | This sub-skill; start with [API reference](references/api-reference.md) and [data formats](references/data-formats.md). |
| Convert tiny local JSONL records without network access | [build_lightfm_dataset.py](scripts/build_lightfm_dataset.py). |
| Choose loss, learning schedule, regularization, epochs, or `LightFM.fit` strategy | [model-training](../model-training/SKILL.md). |
| Create train/test splits, compute precision/AUC, or reason about `check_intersections` | [evaluation-splitting](../evaluation-splitting/SKILL.md). |
| Build, install, Cythonize, or maintain the repository itself | [repo-development](../repo-development/SKILL.md). |

## Short matrix-building workflow

1. Collect the complete user id set, item id set, and stable user/item feature vocabulary needed for the current model run. Namespace metadata labels such as `genre:comedy` or `country:gb` so they cannot collide with raw ids.
2. Choose `Dataset(user_identity_features=..., item_identity_features=...)`. Defaults add one identity feature per known user and item; disable the relevant identity flag for true cold-start generalization from metadata only.
3. Call `fit(users, items, user_features=None, item_features=None)` once to create fresh mappings, or `fit_partial(...)` only when intentionally extending mappings before model training.
4. Call `build_interactions(records)` to get `(interactions, weights)` as aligned COO matrices. Call `build_user_features(records)` and/or `build_item_features(records)` when passing explicit feature matrices to LightFM.
5. Check `interactions_shape()`, `user_features_shape()`, `item_features_shape()`, `model_dimensions()`, and `mapping()` before handing matrices to training, prediction, or evaluation.
6. Pass the same feature matrices, with the same number and order of feature columns, to every model operation that needs them.

## Read next

- [API reference](references/api-reference.md) for exact methods, return keys, shapes, dtypes, and mapping semantics.
- [Data formats](references/data-formats.md) for accepted interaction/feature records, built-in dataset dictionaries, custom conversion, and cold-start workflows.
- [Troubleshooting](references/troubleshooting.md) for unknown ids/features, normalization failures, feature dimension mismatches, download/cache errors, and identity-feature tradeoffs.
