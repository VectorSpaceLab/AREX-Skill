# Cross-Cutting Troubleshooting

## Purpose

Read this when a failure spans multiple Agriculture_KnowledgeGraph workflows or you need to decide which focused sub-skill owns the fix.

## First triage

1. Identify the task family: graph import/query, Django service, entity labeling/NER, crawlers/Wikidata/weather, or relation extraction.
2. Run only non-destructive checks first: root environment preflight, label/schema validators, or tiny fixture scripts.
3. Confirm whether the failure needs an external service, network crawl, large model, or training runtime before trying to reproduce it.
4. Route to the focused troubleshooting page named below.

## Common failure surfaces

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError` for `django`, `thulac`, `py2neo`, `pymongo`, `scrapy`, `pyfasttext`, or `tensorflow` | Workflow-specific dependencies are not installed; the repo is not packaged and has only a legacy requirements file | Read [installation-and-environment.md](installation-and-environment.md), then run `scripts/check_agri_kg_environment.py` |
| Django startup fails before serving a page | View imports load `toolkit/pre_load.py`, which initializes THULAC, Neo4j, MongoDB, label files, vectors, and tree files at import time | Use `sub-skills/web-app-service/references/troubleshooting.md` and the web preflight script |
| Neo4j relation/entity search returns empty results | Nodes/relations were not imported, label-specific match is wrong, relation `type` value differs, or the old wrappers treat empty lists inconsistently | Use `sub-skills/graph-query-and-data-management/references/troubleshooting.md` |
| Label files parse incorrectly | Files are whitespace-delimited `term label`; terms must map to integer labels `0-16`; duplicate terms may need review | Use `sub-skills/entity-labeling-and-ner/scripts/label_file_check.py` |
| KNN prediction cannot start | Missing large fastText model, missing `pyfasttext`, missing Neo4j-labeled training items, or mismatched current working directory | Use `sub-skills/entity-labeling-and-ner/references/troubleshooting.md` |
| Scrapy says no active project or cannot find settings | Command was run from the wrong nested project directory or a settings module is required | Use `sub-skills/crawlers-and-wikidata-pipelines/references/troubleshooting.md` |
| Generated relation/weather CSVs have bad headers or duplicate/suspicious rows | Conversion script output is incomplete, hand-edited, or sourced from stale generated artifacts | Use `sub-skills/crawlers-and-wikidata-pipelines/scripts/validate_relation_csvs.py` |
| Relation dataset JSON generation fails | Six-column TSV rows are malformed, entity/relation ids are incomplete, NA sample file is absent, or source working directory is wrong | Use `sub-skills/relation-extraction-pipeline/scripts/relation_dataset_schema_check.py` |
| PCNN training looks for `data/nyt` despite agriculture files | Source `train.py` initializes `dataset = "nyt"` and does not use the intended CLI variable consistently | Use `sub-skills/relation-extraction-pipeline/references/pcnn-training.md` before patching or training |

## External prerequisites are not proof of skill gaps

This skill documents how to operate the project, but several workflows depend on resources that may not exist in a fresh checkout:

- Neo4j with imported `HudongItem`, `NewNode`, and `Weather` data.
- MongoDB collections for tagging/annotation flows.
- Large fastText Chinese vectors and generated word-vector files.
- Network access and target site availability for crawlers.
- TensorFlow 1.x-compatible training environment and large relation datasets.

If those resources are missing, report the missing prerequisite explicitly and use the nearest bundled validator/reference to narrow the problem. Do not claim a live graph, crawl, model, or training run passed unless it actually ran in the active environment.
