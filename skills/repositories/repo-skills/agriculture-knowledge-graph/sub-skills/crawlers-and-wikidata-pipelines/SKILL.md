---
name: crawlers-and-wikidata-pipelines
description: "Operate Agriculture_KnowledgeGraph crawler and Wikidata/weather
  data-acquisition pipelines safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Crawlers and Wikidata Pipelines

Use this sub-skill when the task is to inspect, run, repair, or validate the repository's crawler-driven data acquisition and intermediate CSV generation workflows for Hudong/Baike pages, Wikidata entity/relation alignment, weather relations, attributes, and tree source lists.

## Load this when

- The user asks how to run a Scrapy spider, choose the correct working directory, or understand crawler outputs.
- The task involves `hudong_pedia`, `entityRelation`, `wikidata_relation`, `new_node`, `weather_plant`, `city_weather`, `attributes`, `staticResult`, or tree-list artifacts before Neo4j import.
- A pipeline failed because expected JSON/CSV files are missing, a Scrapy project cannot find settings, or CSV rows are malformed.
- You need a no-network validation check for relation/weather CSV headers and row invariants.

## Route elsewhere when

- The next action is final Neo4j `LOAD CSV`, Cypher import order, graph constraints, graph query semantics, or tree/vector query APIs; route to the graph-query-and-data-management sub-skill.
- The task is PCNN relation-extraction dataset generation, deduplication, or TensorFlow training; route to the relation-extraction-pipeline sub-skill.
- The task is Django route operation, Mongo-backed tagging UI, THULAC NER behavior, or KNN/fastText entity labeling; use the corresponding sibling sub-skill.

## Operating references

1. Start with [crawler-workflows.md](references/crawler-workflows.md) for Scrapy projects, DFS tree crawlers, legacy data-processing scripts, working directories, output names, and network constraints.
2. Use [wikidata-processing.md](references/wikidata-processing.md) for Wikidata relation conversion, `new_node.csv`, `wikidata_relation*.csv`, relation distribution analysis, and safe CSV validation.
3. Use [weather-and-attribute-pipelines.md](references/weather-and-attribute-pipelines.md) for city/weather, weather-to-plant, climate-list, and attribute-extraction artifacts.
4. Use [troubleshooting.md](references/troubleshooting.md) for crawler-specific recovery steps, path-sensitive failures, service prerequisites, and malformed CSV symptoms.

## Bundled safe script

- [validate_relation_csvs.py](scripts/validate_relation_csvs.py) checks required CSV headers, non-empty fields, duplicate/suspicious rows, and cross-file consistency for `wikidata_relation.csv`, `wikidata_relation2.csv`, `new_node.csv`, `weather_plant.csv`, and `city_weather.csv`. It performs no network or database calls.

Example safe checks:

```bash
python scripts/validate_relation_csvs.py --help
python scripts/validate_relation_csvs.py --self-test
python scripts/validate_relation_csvs.py --root path/to/csv-export-directory
```

## Safety defaults

- Treat all live crawls as network-expensive and site-policy-sensitive. Do not start a broad crawl, disable robots compliance, or raise concurrency without explicit user approval.
- Prefer inspecting existing generated artifacts and running the bundled CSV validator before any live crawl or service-backed conversion.
- Run path-sensitive source scripts from their documented project directories. Many scripts write outputs relative to the current working directory and some execute work at module import time.
- Do not claim Wikidata/weather conversion is verified unless the required local files and, where applicable, Neo4j/THULAC dependencies were actually checked in the active environment.
