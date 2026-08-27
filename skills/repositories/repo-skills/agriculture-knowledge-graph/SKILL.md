---
name: agriculture-knowledge-graph
description: "Operate the Agriculture_KnowledgeGraph agricultural Neo4j graph,
  Django demo, entity labeling, crawler, and relation-extraction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Agriculture_KnowledgeGraph

Use this repo skill when a task involves the Agriculture_KnowledgeGraph / AgriKG research demo: agricultural entity data, Neo4j graph imports and queries, the Django web demo, THULAC/KNN labels, Hudong/Wikidata/weather crawlers, or remote-supervised relation extraction.

## Start by routing the task

- **Graph data, Neo4j import/query, CSV schemas, hierarchy tree, or vector utilities:** use [graph-query-and-data-management](sub-skills/graph-query-and-data-management/SKILL.md).
- **Django demo startup, routes, forms, QA, relation search pages, tagging pages, or preload side effects:** use [web-app-service](sub-skills/web-app-service/SKILL.md).
- **THULAC entity recognition, label ids `0-16`, predicted label files, manual labels, fastText/KNN classifier prerequisites:** use [entity-labeling-and-ner](sub-skills/entity-labeling-and-ner/SKILL.md).
- **Hudong/Baike crawlers, DFS tree crawling, Wikidata property/entity/relation crawlers, weather/attribute pipelines, or generated relation CSV validation:** use [crawlers-and-wikidata-pipelines](sub-skills/crawlers-and-wikidata-pipelines/SKILL.md).
- **Wikidata/Wikipedia sentence alignment, relation dataset TSV/JSON creation, deduplication, Fire preprocessing commands, or TensorFlow PCNN training:** use [relation-extraction-pipeline](sub-skills/relation-extraction-pipeline/SKILL.md).

## Read shared references when needed

- [architecture-and-workflows.md](references/architecture-and-workflows.md) maps the repository components and task order.
- [installation-and-environment.md](references/installation-and-environment.md) explains the un-packaged source layout, old Python/Django stack, optional services, large assets, and dependency choices.
- [troubleshooting.md](references/troubleshooting.md) gives cross-cutting triage and routes symptoms to the right sub-skill.
- [repo-provenance.md](references/repo-provenance.md) records the source snapshot and evidence paths used to create this skill; read it before deciding whether a checkout needs refresh.

## Safe root preflight

Run the bundled checker before broad debugging:

```bash
python scripts/check_agri_kg_environment.py --help
python scripts/check_agri_kg_environment.py --repo-root /path/to/Agriculture_KnowledgeGraph
```

The checker is non-destructive. It imports optional packages, checks expected files when a checkout path is supplied, and can optionally probe local Neo4j/MongoDB sockets. It does not start services, crawl the network, download fastText vectors, connect with credentials, load large models, or train TensorFlow models.

## Repository operating assumptions

- The repo is a legacy source checkout, not a packaged Python distribution. Use workflow-specific dependencies and working directories rather than expecting `pip install -e .`.
- Python 3.7 with Django 1.11-era dependencies is the safest legacy starting point; modern Python may require compatibility patches.
- Neo4j, MongoDB, network crawls, large fastText/vector files, and TensorFlow PCNN training are external prerequisites. Treat them as explicit user-approved steps, not first-line smoke checks.
- Many source modules are path-sensitive or eager at import time. Prefer bundled validators and references before importing modules that start service connections or load large files.
- Do not claim a live graph import, web app, crawl, KNN prediction, or PCNN training run passed unless that exact workflow ran in the active environment.

## Quick task examples

- “Import the AgriKG CSVs into Neo4j” → graph-query-and-data-management, then its Cypher templates.
- “Django route fails before the first page loads” → web-app-service, especially preload troubleshooting.
- “Validate `predict_labels.txt` or explain label 6” → entity-labeling-and-ner.
- “Regenerate or validate `wikidata_relation2.csv`” → crawlers-and-wikidata-pipelines.
- “Convert aligned relation sentences into train/test JSON” → relation-extraction-pipeline.
