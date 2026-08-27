---
name: graphrag
description: "Use Microsoft GraphRAG from CLI or Python: configure
  data/model/storage/vector settings, build or update indexes, query completed
  indexes, tune indexing prompts, and extend package factories safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GraphRAG

Use this skill when a task mentions Microsoft GraphRAG, graph-based RAG, `graphrag init`, `graphrag index`, `graphrag query`, `graphrag prompt-tune`, GraphRAG settings, completed index tables, or custom GraphRAG providers.

GraphRAG is a Python package and CLI for extracting structured knowledge graphs from unstructured text, writing index tables/vector stores, and querying those completed indexes with global, local, DRIFT, or basic search.

## First Steps

1. Confirm GraphRAG is installed in the target environment:

   ```bash
   python - <<'PY'
   import graphrag
   print("graphrag import ok")
   PY
   graphrag --help
   ```

2. Identify the user’s workflow:
   - New workspace or settings/data/auth issue → `sub-skills/configuration-data/`
   - Build, update, validate, or inspect an index → `sub-skills/indexing/`
   - Query an existing index → `sub-skills/querying/`
   - Generate or repair indexing prompts → `sub-skills/prompt-tuning/`
   - Implement custom providers/factories or graph helpers → `sub-skills/package-extensions/`

3. Keep live-service calls guarded. Indexing, querying, and prompt tuning often need OpenAI/Azure credentials, model deployments, vector stores, or storage services. Prefer bundled validators and offline contract checks before running cost-incurring commands.

## Common Routes

- **Configuration and data readiness**: Use `sub-skills/configuration-data/` for `settings.yaml`, `.env` interpolation, model/auth config, input formats (`text`, `csv`, `json`, `jsonl`, `markitdown`, `parquet`), file/blob/Cosmos storage, JSON/memory/no-op cache, LanceDB/Azure AI Search/Cosmos vector stores, and safe config/input diagnostics.
- **Indexing**: Use `sub-skills/indexing/` for `graphrag init`, `graphrag index`, `graphrag update`, Python `build_index(...)`, standard vs fast indexing, custom workflow lists, BYOG tables, output table validation, embeddings, and incremental update failure recovery.
- **Querying**: Use `sub-skills/querying/` for `graphrag query`, global/local/DRIFT/basic search, streaming APIs, completed-index table contracts, vector-store names and ID keys, community levels, dynamic community selection, and query prerequisite checks.
- **Prompt tuning**: Use `sub-skills/prompt-tuning/` for `graphrag prompt-tune`, Python `generate_indexing_prompts(...)`, selection methods, output prompt files, multilingual/domain/entity-type tuning, and prompt output validation.
- **Package extensions**: Use `sub-skills/package-extensions/` for custom cache/storage/table/input/chunker/vector/LLM providers, factory `register_*` and `create_*` patterns, graph helper checks, workflow factory registration, and optional dependency diagnostics.

## Typical Workflows

### Configure → Index → Query

1. Read `sub-skills/configuration-data/` to initialize or validate `settings.yaml`, `.env`, input layout, storage, cache, and vector-store settings.
2. Read `sub-skills/indexing/` to run `graphrag init`, `graphrag index`, or `graphrag update`, and validate output tables.
3. Read `sub-skills/querying/` to choose global/local/DRIFT/basic search and check completed-index prerequisites before running model-backed queries.

### Tune Prompts Before Indexing

1. Read `sub-skills/configuration-data/` for model credentials and input readiness.
2. Read `sub-skills/prompt-tuning/` to generate `extract_graph.txt`, `summarize_descriptions.txt`, and `community_report_graph.txt`.
3. Return to `sub-skills/indexing/` to run an index with the updated prompts.

### Add a Custom Provider

1. Read `sub-skills/package-extensions/` to pick the correct factory and offline mock pattern.
2. Read `sub-skills/configuration-data/` only when the custom provider must be wired through GraphRAG YAML.
3. Use the bundled extension scripts as templates for isolated tests before touching live storage, vector stores, or LLM providers.

## Repo-Level References

- `references/cli-command-map.md` summarizes the verified public CLI commands and when to route to each sub-skill.
- `references/capability-routing.md` maps natural user requests to the owning sub-skill and notes key exclusions.
- `references/troubleshooting.md` covers cross-cutting install/import, credentials, optional dependencies, service, and cost-safety failures.
- `references/repo-provenance.md` records the source snapshot used to generate this skill. Read it before deciding whether this skill is stale for a different checkout.

## Safety Notes

- Do not run indexing, prompt tuning, or query commands that call hosted models until credentials, model deployments, cost expectations, and data scope are explicit.
- Do not assume docs and code are identical. Current package inspection verified GraphRAG `3.1.0`; the sub-skills call out known docs drift where it affects JSONL/parquet/MarkItDown support or prompt output filenames.
- Treat original notebooks/tests/docs as evidence only. Runtime scripts and references in this skill are self-contained and do not require the original repository checkout.
