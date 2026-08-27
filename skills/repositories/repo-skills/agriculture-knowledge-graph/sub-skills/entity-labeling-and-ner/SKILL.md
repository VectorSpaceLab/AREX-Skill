---
name: entity-labeling-and-ner
description: "Use THULAC, the agricultural label taxonomy, and the legacy
  KNN/fastText label workflow for entity recognition and category prediction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Entity Labeling and NER

Use this sub-skill for agricultural entity labeling, THULAC-based NER, and the legacy KNN label-prediction workflow.

## Read when

- You need to validate or interpret `term label` files with labels `0-16`.
- You need the entity-recognition flow that combines THULAC tags, predicted labels, and Neo4j entity presence checks.
- You need to inspect the KNN classifier interface or its fastText prerequisites.
- You need to work with manual seed labels or predicted label files.

## Do

- Start with [label taxonomy](references/label-taxonomy.md) for the accepted label ids and file formats.
- Use [NER and labeling workflow](references/entity-labeling-and-ner.md) for the recognition flow, seed-label generation, and label file lifecycle.
- Use [KNN classifier API](references/knn-classifier-api.md) when a task depends on the legacy classifier interface or its prerequisites.
- Run [label file check](scripts/label_file_check.py) before trusting a label file.
- Run [KNN feature probe](scripts/knn_feature_probe.py) to inspect the non-model prerequisites without downloading the fastText model.

## Do not

- Do not treat this sub-skill as the Django UI route owner.
- Do not treat this sub-skill as the Neo4j import/query owner.
- Do not treat this sub-skill as the relation-sentence labeling owner.
- Do not claim live KNN prediction is verified unless the fastText model file and backing graph data are actually present.

## Outputs this sub-skill owns

- Numeric agricultural label taxonomy `0-16`.
- THULAC + predicted-label NER behavior.
- Label-file validation.
- KNN feature prerequisites and legacy classifier interface notes.
- Manual and seed label workflows.

## Quick checks

- `python scripts/label_file_check.py --demo`
- `python scripts/knn_feature_probe.py --demo`
