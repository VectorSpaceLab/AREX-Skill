---
name: indexing
description: "Initialize GraphRAG workspaces and run, update, inspect, or
  troubleshoot indexing pipelines, including standard vs fast methods, workflow
  selection, output tables, BYOG indexes, embeddings, cache/reporting/storage,
  and incremental update failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GraphRAG Indexing

Use this sub-skill when a task mentions `graphrag init`, `graphrag index`, `graphrag update`, `build_index`, indexing methods, workflows, output parquet tables, BYOG tables, embeddings generated during indexing, or update failures.

## Route First

- For config schema details, input providers, model/env setup, and storage provider configuration, use `../configuration-data/`.
- For querying a completed index with global, local, DRIFT, or basic search, use `../querying/`.
- For generating or editing extraction/community report prompts, use `../prompt-tuning/`.
- For implementing custom factories/providers beyond workflow selection, use `../package-extensions/`.

## Common Tasks

### Initialize a Workspace

```bash
graphrag init --root <project-root>
```

This creates a default config and prompt layout. After initialization, add input documents under the configured input location, set model credentials outside committed config when needed, and dry-run the indexer before a costly run.

### Dry-Run and Build an Index

```bash
graphrag index --root <project-root> --dry-run
graphrag index --root <project-root> --method standard
```

`standard` is the default. Use `--method fast` for FastGraphRAG when lower cost matters more than rich LLM-derived entity and relationship descriptions. Add `--verbose` while debugging and `--no-cache` only when cached LLM responses must be ignored.

### Incrementally Update an Index

```bash
graphrag update --root <project-root> --method standard
```

`update` calls the same indexing API with `is_update_run=True`, copies previous output tables into update storage, builds a delta index, then runs update merge workflows. Confirm previous outputs exist before updating, and verify that changed, deleted, duplicate, and unchanged document titles behave as expected for the project.

### Call the Python API

```python
import asyncio
from graphrag.api import build_index
from graphrag.config.load_config import load_config

config = load_config(root_dir="<project-root>")
results = asyncio.run(build_index(config, method="standard", verbose=True))
if any(result.error for result in results):
    raise RuntimeError([result.workflow for result in results if result.error])
```

The verified signature is `build_index(config, method='standard', is_update_run=False, callbacks=None, additional_context=None, verbose=False, input_documents=None)`. `input_documents` may be a pandas `DataFrame` with GraphRAG document columns to bypass file loading.

## Method Choice

- `standard`: LLM graph extraction, relationship extraction, description summarization, optional claims, community reports, and embeddings. Prefer for high-fidelity graph outputs.
- `fast`: NLP noun phrase extraction and co-occurrence relationships, LLM community reporting, and embeddings. Prefer for lower cost or large exploratory runs; check SpaCy/NLP model requirements when using non-default extractors.
- `standard-update` / `fast-update`: internal pipeline names selected when `build_index(..., is_update_run=True)` or `graphrag update` is used with the base method.
- Custom `workflows`: a config `workflows` list overrides built-in method pipelines; use it for BYOG or partial reruns after confirming source tables exist.

## Outputs to Expect

Default file table output is parquet. Core tables are `documents`, `text_units`, `entities`, `relationships`, `communities`, and `community_reports`; `covariates` appears when claim extraction is enabled. Embeddings are written to the configured vector store for enabled embedding names such as `text_unit_text`, `entity_description`, and `community_full_content`.

Use bundled helpers:

```bash
python sub-skills/indexing/scripts/inspect_index_config.py --root <project-root>
python sub-skills/indexing/scripts/validate_index_outputs.py --output <project-root>/output --use global
python sub-skills/indexing/scripts/run_mock_index_workflow.py
```

## BYOG Pattern

For bring-your-own graph, place `entities.parquet` and `relationships.parquet` in the configured output table location before running only the downstream workflows. Add `text_units.parquet` and `generate_text_embeddings` when local, DRIFT, or basic search will need chunks or vectors.

Minimal global-search BYOG workflow:

```yaml
workflows: [create_communities, create_community_reports]
```

Expanded BYOG workflow for non-global search:

```yaml
workflows: [create_communities, create_community_reports, generate_text_embeddings]
```

FastGraphRAG-style BYOG reporting can use `create_community_reports_text` when entities and relationships lack descriptions but have valid `text_unit_ids` links.

## References

- See `references/indexing-api-cli.md` for CLI/API entry points and lifecycle details.
- See `references/indexing-config-and-data.md` for config, storage, input, BYOG, cache, and vector considerations.
- See `references/indexing-workflows-and-outputs.md` for built-in workflow order and output table expectations.
- See `references/troubleshooting.md` for common failures and targeted fixes.
