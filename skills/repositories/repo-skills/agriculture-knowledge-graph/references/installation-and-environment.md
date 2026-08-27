# Installation and Environment Notes

## Purpose

Read this before installing dependencies, running preflight checks, or deciding whether a failure is an environment issue versus a data/service issue.

## Repository packaging status

Agriculture_KnowledgeGraph is not a packaged Python distribution. There is no `pyproject.toml`, `setup.py`, or console-script entry point. Treat it as a source checkout containing a Django app, Scrapy projects, data-processing scripts, and model code. Use explicit working directories and `PYTHONPATH`/module paths when importing legacy modules.

## Python and dependency guidance

The code was written for an older Python 3/Django 1.11-era stack. A conservative starting point for legacy execution is Python 3.7 with these dependency families:

- Django 1.11.x for the demo app.
- THULAC for segmentation/NER preloading.
- py2neo plus the Neo4j Python driver for graph access.
- pymongo for relation/tagging collections.
- pyfasttext and a separately downloaded Chinese fastText model for live KNN label prediction.
- Scrapy for crawler projects.
- numpy, pandas, scikit-learn, fire, tqdm, requests, beautifulsoup4, jieba, and pinyin for processing and utility scripts.
- TensorFlow 1.x-era APIs for the PCNN relation-extraction model if training is explicitly required.

Do not install every optional stack just to inspect the project. Choose dependencies by the workflow route:

| Workflow | Minimum to inspect | Extra to execute fully |
| --- | --- | --- |
| Graph schemas/import plans | Python, CSV tools, bundled validators | Neo4j server and import directory access |
| Django demo | Django, THULAC, py2neo, pymongo, data files | Running Neo4j and MongoDB services with populated graph/collections |
| NER/KNN labels | THULAC, pyfasttext, label files | fastText `wiki.zh.bin` model, Neo4j graph data, predicted labels |
| Crawlers/Wikidata | Scrapy, requests/parsers | Network access, target site availability, large generated JSON/CSV storage |
| Relation extraction | numpy, fire, schema checker | TensorFlow 1.x stack, word-vector JSON, dataset splits, optional GPU |

## Safe root preflight

Use the bundled root helper for a non-destructive check:

```bash
python scripts/check_agri_kg_environment.py --help
python scripts/check_agri_kg_environment.py --repo-root /path/to/Agriculture_KnowledgeGraph
python scripts/check_agri_kg_environment.py --repo-root /path/to/Agriculture_KnowledgeGraph --check-services --json
```

The helper imports optional packages, checks expected files when a checkout path is supplied, and can probe localhost Neo4j/MongoDB sockets. It does not start servers, crawl the network, download models, connect with credentials, import large vectors, or train models.

## Service prerequisites

- Neo4j is required for graph imports, relation/entity lookup, QA graph traversal, and many demo routes.
- MongoDB is required for relation-tagging pages that read/write `train_data` and `test_data` collections.
- The source code contains hard-coded connection defaults in old wrappers. Treat them as local-demo defaults, not production credentials. Prefer editing local settings or wrappers in a checkout rather than publishing credentials.
- The Django app imports a preload module from many views. That module initializes THULAC, Neo4j, MongoDB, predicted labels, word vectors, and taxonomy tree state at import time, so startup can fail before a request is handled.

## Large assets and downloads

- The fastText Chinese model is intentionally not bundled in this skill and may not be present in a checkout.
- Large crawled CSV/JSON/corpus/vector artifacts should be validated by headers and sample rows before any expensive regeneration.
- TensorFlow PCNN training depends on generated dataset files and large word-vector JSON. Treat it as an explicit training task, not an environment smoke check.
