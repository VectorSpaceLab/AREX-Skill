---
name: relation-extraction-pipeline
description: "Prepare relation extraction datasets and inspect the TensorFlow
  PCNN training workflow for Agriculture_KnowledgeGraph."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Relation Extraction Pipeline

Use this sub-skill when the task is to create, validate, split, or troubleshoot the remote-supervised relation-extraction dataset, or to understand the TensorFlow PCNN training stack in this agriculture knowledge-graph repository.

## Route here for

- Turning aligned Wikidata/Wikipedia sentence rows into `rel2id.json`, `entity2id.json`, `dataset.json`, `word2vec.json`, `train_dataset.json`, and `test_dataset.json`.
- Validating six-column training TSV rows and the JSON schemas expected by the PCNN data loader.
- Diagnosing Fire command names, working-directory-sensitive paths, stale `_processed_data`, bad entity positions, relation-label filters, or NA-sample split failures.
- Reviewing the PCNN model configuration, TensorFlow 1.x assumptions, GPU settings, and large word-vector limits before any expensive training run.

## Route elsewhere

- General Wikidata crawling, Wikidata JSON-to-CSV conversion, Neo4j import CSV creation, Hudong/weather crawlers, and network collection pipelines belong to the crawler/Wikidata workflow, not this sub-skill.
- Django relation-label annotation UI, Mongo-backed tagging pages, and web-service startup belong to the web-app workflow, not this sub-skill.
- Neo4j graph querying or Cypher import plans belong to graph query/data management.

## Operating map

1. For the end-to-end data build sequence, required source artifacts, Fire commands, and safe replacement commands, read [dataset preparation](references/dataset-preparation.md).
2. For exact row and JSON schemas, path-sensitive generated files, and validator usage, read [data formats](references/data-formats.md).
3. Before training or editing `config.py`/`train.py`, read [PCNN training](references/pcnn-training.md).
4. For known failure modes and recovery actions, read [troubleshooting](references/troubleshooting.md).

## Bundled scripts

- [scripts/relation_dataset_schema_check.py](scripts/relation_dataset_schema_check.py) validates tiny training TSV, `rel2id`, `entity2id`, dataset JSON, and optional word-vector JSON files without importing TensorFlow.
- [scripts/deduplicate_training_rows.sh](scripts/deduplicate_training_rows.sh) deduplicates training rows with explicit input and output paths and a safe `--help` path.

## Safe default

Do not launch PCNN training, live Neo4j alignment, Mongo annotation, network crawling, or large word-vector conversion as a first check. First run the schema checker or a tiny deduplication fixture, then escalate only after data files, working directory, and TensorFlow 1.x/GPU constraints are explicit.
