---
name: model-selection
description: "Rank pretrained models with TLLib transferability metrics
  including H-score, regularized H-score, LEEP, NCE, LogME, and TransRate."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Selection Skill

Use this sub-skill when a user wants to **choose or rank pretrained models before fine-tuning** with TLLib transferability metrics.

## Route here for

- Computing H-score or regularized H-score from extracted feature matrices and target labels.
- Computing LogME or TransRate from extracted feature matrices and target labels.
- Computing LEEP from source-class probability predictions and target labels.
- Computing NCE from source-class predicted labels and target labels.
- Deciding which metric is possible from the arrays a user already has: features, target labels, source-head probabilities, logits, or source predicted classes.
- Building a safe CPU smoke check for ranking APIs without downloading datasets or running full feature extraction.

## Route elsewhere

- Dataset classes, image-list formats, model factories, transforms, and feature-extraction data/model setup: [vision-data-models](../vision-data-models/SKILL.md).
- Fine-tuning or adapting the selected pretrained model after ranking: [task-generalization](../task-generalization/SKILL.md).
- Domain adaptation, self-training, or image translation methods beyond model ranking: use the corresponding sibling sub-skill.

## Operating sequence

1. Confirm the user has a labeled target ranking subset. TLLib ranking metrics need arrays aligned by sample; they are not unsupervised dataset-selection scores.
2. Choose the metric by available inputs:
   - `features` + `target labels`: H-score, regularized H-score, LogME, TransRate.
   - `source-class probabilities` + `target labels`: LEEP.
   - `source predicted class ids` + `target labels`: NCE.
   - `regression features` + continuous targets: LogME with `regression=True`.
3. Validate array shapes and label encoding with [ranking API reference](references/ranking-api-reference.md) before computing scores.
4. If features or predictions must be extracted, use [vision-data-models](../vision-data-models/SKILL.md) for datasets/models and follow the cache/metadata guidance in [model selection workflows](references/model-selection-workflows.md).
5. Interpret scores only within the same target dataset, split, preprocessing, feature layer, and candidate-model set. After selecting a model, route fine-tuning to [task-generalization](../task-generalization/SKILL.md).
6. For an installed-package sanity check, run `scripts/tllib_ranking_smoke.py` from any directory.

## Bundled references

- [Ranking API reference](references/ranking-api-reference.md)
- [Model-selection workflows](references/model-selection-workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled script

- `scripts/tllib_ranking_smoke.py`: CPU-only synthetic smoke that imports installed `tllib`, computes all supported ranking metrics on small NumPy arrays, and asserts finite scalar outputs. It does not read datasets, download models, or rely on source checkout files.

## Verification status

This sub-skill claims API-level CPU verification for ranking metrics using synthetic arrays. Full dataset feature extraction, pretrained model downloads, and benchmark ranking runs remain user workflow steps and are not bundled as required verification.
