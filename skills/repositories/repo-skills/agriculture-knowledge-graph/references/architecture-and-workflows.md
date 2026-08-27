# Architecture and Workflow Map

## Purpose

Read this when a task asks what Agriculture_KnowledgeGraph contains, how its major workflows connect, or which sub-skill owns a capability. The repository is an old research/demo application rather than an installable package, so operating safely starts with choosing the right workflow boundary.

## High-level components

| Component | Role | Main outputs or runtime assets | Skill route |
| --- | --- | --- | --- |
| Graph data resources | Crawled Hudong entities, Wikidata relation CSVs, attributes, weather/city relations, labels, and hierarchy/vector text files | `HudongItem`, `NewNode`, `Weather`, `RELATION`, `Weather2Plant`, `CityWeather`, label and tree files | `graph-query-and-data-management` |
| Django demo | Search pages, relation search, overview tree, QA, decision page, and tagging interfaces | HTTP routes, templates, Neo4j/Mongo-backed views, eager preload state | `web-app-service` |
| Entity recognition and labels | THULAC segmentation, predicted label lookup, hand labels, and KNN label prediction | label ids `0-16`, `predict_labels` maps, optional fastText model | `entity-labeling-and-ner` |
| Crawlers and acquisition scripts | Scrapy crawlers and processing scripts for Hudong pages, Wikidata properties/entities/relations, tree lists, weather, and attributes | JSON/CSV artifacts later imported into Neo4j or used for model data | `crawlers-and-wikidata-pipelines` |
| Relation extraction | Remote-supervised sentence alignment, relation dataset JSON generation, and TensorFlow PCNN training | six-column TSV rows, `rel2id`, `entity2id`, `dataset`, train/test splits, checkpoints | `relation-extraction-pipeline` |

## Typical workflow order

1. **Use existing artifacts when possible.** The checkout already contains large crawled CSV/JSON/model-like artifacts. Prefer validation and schema checks over recrawling.
2. **Validate or regenerate acquisition outputs.** Use the crawler/Wikidata route for Hudong/Wikidata/weather artifacts. Do not start broad network crawls as a first diagnostic.
3. **Plan Neo4j import.** Use the graph/data route for CSV headers, labels, constraints, and Cypher templates. Import order matters: base entity nodes first, then new nodes/weather nodes, then relationships.
4. **Run or debug the Django demo.** Use the web-app route after Neo4j, MongoDB, THULAC, vector/tree files, and label files are known to be available.
5. **Handle entity labels.** Use the NER/KNN route for label taxonomy, predicted labels, manual labels, and fastText prerequisites.
6. **Build relation extraction data only when needed.** Use the relation-extraction route for aligned sentence TSVs, JSON schema checks, deduplication, splits, and PCNN training caveats.

## Safety model

- **Safe by default:** bundled validators, source compilation, label-file checks, schema checks, tiny hierarchy fixtures, import/package checks.
- **Requires explicit service setup:** Neo4j graph queries/import, Django startup, Mongo-backed tagging, THULAC+Neo4j entity recognition.
- **Requires explicit network approval:** Scrapy crawls, Wikidata/weather page retrieval, external model downloads.
- **Requires explicit compute/runtime approval:** TensorFlow PCNN training, large word-vector conversion, large fastText model inference.

## Evidence used to build this skill

The skill was distilled from the project README, declared requirements, Django source, graph/data helpers, KNN/NER code, crawler modules, Wikidata/weather processing scripts, relation-extraction preprocessing/training code, and representative headers/samples from the bundled data artifacts. Large generated data files and vendored UI assets were not copied into the skill.
