# Cross-Cutting Troubleshooting

## Purpose

Read this for GraphRAG failures that span configuration, indexing, querying, prompt tuning, and extension work. Workflow-specific troubleshooting lives in each sub-skill.

## Install and Import

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: graphrag` | GraphRAG is not installed in the active Python. | Install `graphrag` in the target environment and rerun `python -c "import graphrag"`. |
| `graphrag: command not found` | Console script is not on `PATH` or the wrong environment is active. | Use `python -m graphrag --help` or activate/install into the intended environment. |
| Import failure from `pyarrow`, `spacy`, `graspologic_native`, `lancedb`, `markitdown`, or Azure packages | Optional or compiled dependency mismatch. | Check the owning sub-skill; prefer Python versions supported by GraphRAG package metadata and reinstall the missing dependency in the target environment. |
| LiteLLM warnings for uninstalled cloud SDKs | Optional provider backends are not installed. | Ignore if not using that provider; install the provider SDK only when the selected model backend needs it. |

## Credentials and Services

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Model validation fails before indexing/querying | Missing API key, invalid deployment, invalid endpoint, or network/auth issue. | Validate model config in `sub-skills/configuration-data/`; use `--skip-validation` only when intentionally deferring live validation. |
| Azure managed identity fails while `api_key` is present | Managed identity and API-key auth are mixed. | Remove `api_key` for managed identity and confirm the host has Azure identity access. |
| Azure AI Search, Cosmos DB, Blob Storage, or LanceDB errors | Service endpoint, credentials, collection/index name, URI, or schema mismatch. | Use config/vector/storage references before running indexing or query commands. |
| Costs or long runtimes are unexpected | Indexing, prompt tuning, and querying call hosted models or vector services. | Start with tiny fixtures, offline validators, and explicit user approval for live model/service runs. |

## Data and Tables

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Indexing finds no input documents | Input directory, file pattern, input type, or storage base path is wrong. | Use `sub-skills/configuration-data/scripts/smoke_input_readers.py` or inspect the input config. |
| Query command fails with missing table errors | Chosen query method needs tables not present in the completed index. | Run `sub-skills/querying/scripts/validate_query_prereqs.py` for the method. |
| DRIFT/basic/local query fails around vectors | Required vector-store index/table is missing or keyed differently than expected. | Read `sub-skills/querying/references/query-vector-store-contracts.md`. |
| Incremental update skips or removes unexpected rows | Document IDs/titles changed, previous output is missing, or deleted/orphan logic applied. | Read `sub-skills/indexing/references/indexing-workflows-and-outputs.md`. |

## Docs Drift

When docs and package behavior differ, prefer current installed package facts and source-backed references in this skill. Known drift surfaces include current code support for JSONL/parquet/MarkItDown inputs in places where docs are shorter, and prompt-tuning output filenames around `community_report_graph.txt`.
