---
name: querying
description: "Run and diagnose GraphRAG global, local, DRIFT, basic, streaming,
  and question-generation queries over completed indexes or BYOG tables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Querying

Use this sub-skill when the task is about `graphrag query`, global/local/DRIFT/basic search, streaming query output, query DataFrame inputs, vector-store embedding IDs, community levels, dynamic community selection, or follow-up question generation over an existing GraphRAG index. Do not use it to create indexes, update indexes, tune prompts, or design input data; route indexing to `../indexing/` and config/data setup to `../configuration-data/`.

## Route by Query Task

- **Use CLI for completed indexes**: run `graphrag query` with `--root`, optional `--data`, `--method`, `--community-level`, `--dynamic-community-selection`, `--response-type`, and `--streaming`; see [API and CLI](references/query-api-cli.md).
- **Call Python APIs**: load `GraphRagConfig` with `load_config`, read the required parquet tables into pandas DataFrames, then call `global_search`, `local_search`, `drift_search`, `basic_search`, or the matching streaming variant; see [API and CLI](references/query-api-cli.md).
- **Validate table prerequisites**: map each method to its required `*.parquet` tables and columns before querying; see [input contracts](references/query-input-contracts.md).
- **Diagnose vector retrieval**: verify the configured vector-store schema includes `entity_description`, `community_full_content`, and/or `text_unit_text` as required by the selected method; see [vector-store contracts](references/query-vector-store-contracts.md).
- **Debug failures**: handle missing reports, level mismatches, bad vector IDs, local context proportions, DRIFT report embeddings, JSON parse warnings, and token truncation; see [troubleshooting](references/troubleshooting.md).

## Method Selection

- **Global search** answers dataset-wide or thematic questions from community reports; it needs `entities`, `communities`, and `community_reports`, and can use dynamic community selection.
- **Local search** answers entity-specific questions using entities, relationships, text units, community reports, optional covariates, and `entity_description` vectors.
- **DRIFT search** expands local search with community-report priming and follow-up exploration; it needs local-search tables plus `entity_description` and `community_full_content` vectors.
- **Basic search** is baseline vector RAG over text units; it needs `text_units` plus `text_unit_text` vectors.
- **Question generation** uses the same local-context data shape as local search and produces candidate follow-up questions rather than final answers.

## Bundled Helper

- `scripts/validate_query_prereqs.py` checks table file presence, required columns, community-level availability, query-shape risks, local proportion settings, and configured vector-store embedding names for one method without network access or credentials.

## Quick Commands

```bash
python skills/graphrag/sub-skills/querying/scripts/validate_query_prereqs.py --root . --method local --data output
python skills/graphrag/sub-skills/querying/scripts/validate_query_prereqs.py --root . --method drift --community-level 2 --query "What changed?"
graphrag query "What are the major themes?" --root . --method global --community-level 2 --response-type "List of 5 Points"
graphrag query "What does entity X do?" --root . --method local --streaming
```

## Query Mental Model

GraphRAG query APIs do not build indexes. They adapt completed index tables into query data models, create model/vector-store clients from `settings.yaml`, build a bounded context window, and then call the configured completion model. Most query failures are caused by stale or incomplete output tables, wrong community level, missing vector indexes, vector IDs keyed by titles instead of IDs, or token budgets that prune needed context.
