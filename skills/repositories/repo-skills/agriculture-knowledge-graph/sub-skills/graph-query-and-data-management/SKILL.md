---
name: graph-query-and-data-management
description: "Operate the Agriculture KnowledgeGraph Neo4j graph import/query,
  CSV schemas, hierarchy tree, and vector utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Graph Query and Data Management

Use this sub-skill when the task is about the Agriculture KnowledgeGraph data
model rather than the web UI or model-training pipelines.

## Use this for

- Planning or debugging Neo4j imports for Hudong, Wikidata, attribute, weather,
  and city-climate CSV artifacts.
- Understanding graph labels, relationship types, and relation-search semantics.
- Translating or modernizing the repo's `Neo4j` wrapper query methods safely.
- Inspecting CSV field meanings, delimiter quirks, and hierarchy/vector utility
  input formats.
- Running a tiny non-repo smoke check of the hierarchy tree behavior.

## Route elsewhere

- Django service startup, URL/view behavior, form fields, and preload side
  effects: use `../web-app-service/`.
- THULAC entity recognition, predicted labels, KNN, or fastText files: use
  `../entity-labeling-and-ner/`.
- Scrapy crawlers, Wikidata conversion scripts, and weather data acquisition:
  use `../crawlers-and-wikidata-pipelines/`.
- PCNN relation extraction datasets, Mongo annotation data, or TensorFlow
  training: use `../relation-extraction-pipeline/`.

## Read first

- [Neo4j import and query guide](references/neo4j-import-and-query.md)
- [Data format guide](references/data-formats.md)
- [Tree and vector API guide](references/tree-and-vector-apis.md)
- [Workflow troubleshooting](references/troubleshooting.md)

## Bundled helpers

- [Tree API smoke check](scripts/tree_api_smoke.py) creates temporary edge/leaf
  fixtures and asserts source-compatible hierarchy behavior without importing
  the original checkout.
- [Cypher import templates](scripts/cypher_import_templates.cypher) provides
  adaptable `LOAD CSV` templates that use Neo4j import-directory file URLs, not
  machine-local absolute paths.

## Operating cautions

- Treat live Neo4j, MongoDB, the Django service, large word-vector files, and
  network crawls as external prerequisites unless a task explicitly provisions
  them.
- The historical source concatenates Cypher strings. When writing new code,
  prefer parameterized queries and preserve exact label/relationship semantics.
- The source is old and un-packaged; use these references as operating guidance
  and keep runtime work self-contained.
