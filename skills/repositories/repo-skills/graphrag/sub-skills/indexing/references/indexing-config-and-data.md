# Indexing Config and Data

## Config Files

GraphRAG default configuration mode reads `settings.yml`, `settings.yaml`, or JSON settings under the project root and loads `.env` token substitutions such as `${GRAPHRAG_API_KEY}`. Do not commit secrets; keep provider keys in environment variables or external secret stores.

Use `../configuration-data/` for full schema coverage. For indexing, check these sections first:

- `input` and `input_storage`: document format and source location.
- `chunking`: text unit size, overlap, encoding model, and metadata prepending.
- `output_storage` and `table_provider`: where output tables are written.
- `update_output_storage`: where incremental update snapshots and deltas are written.
- `cache`: LLM response cache; can be disabled from CLI with `--no-cache`.
- `reporting`: report/log sink.
- `vector_store`: where embeddings are stored and what vector dimensions are expected.
- `workflows`: optional explicit workflow list that overrides built-in method pipelines.
- `embed_text`, `extract_graph`, `extract_graph_nlp`, `prune_graph`, `cluster_graph`, `extract_claims`, and `community_reports`: workflow-specific tuning.

## Input Documents

Built-in ingestion supports text, CSV, and JSON files. All loaders produce a `documents` table with shared columns: `id`, `text`, `title`, `creation_date`, and optional `metadata`.

API callers can supply `input_documents` directly to `build_index`. The DataFrame must already match the document schema. This is useful for unsupported data stores or preprocessing pipelines; GraphRAG still performs chunking and downstream workflows.

## Standard vs Fast Data Needs

`standard` uses LLM extraction and summarization. Its important knobs include graph extraction prompts/entity types, claim extraction enablement, description summarization limits, community report prompts, and embedding settings.

`fast` uses NLP extraction (`extract_graph_nlp`) and graph pruning. The default noun-phrase extraction is regex-oriented for English; SpaCy-backed extractors require an installed model compatible with `model_name`. FastGraphRAG commonly benefits from smaller text chunks.

## BYOG Data

For bring-your-own graph, pre-populate output tables, then set `workflows` to run only downstream workflows.

Minimum global-search tables:

- `entities`: needs at least `id`, `title`, `description`, and `text_unit_ids` for graph summarization.
- `relationships`: needs at least `id`, `source`, `target`, `description`, `weight`, and `text_unit_ids`; `weight` affects Leiden community detection.

Optional tables for richer query:

- `text_units`: needed by local, DRIFT, basic, and FastGraphRAG-style text report paths.
- Embedding outputs: needed for local, DRIFT, and basic search depending on query method and config.

Example BYOG workflows:

```yaml
workflows: [create_communities, create_community_reports]
```

```yaml
workflows: [create_communities, create_community_reports, generate_text_embeddings]
```

```yaml
workflows: [create_communities, create_community_reports_text, generate_text_embeddings]
```

## Storage and Paths

File storage paths are resolved by GraphRAG relative to the project/config context. For file-backed output, expect parquet tables by table name. For blob/cosmos/vector backends, validate provider credentials and namespaces before the first costly run.

Update runs use `update_output_storage` to create timestamped folders/namespaces containing a `previous` copy of the old index and a `delta` index for new work. A missing or incomplete previous output is an update blocker.

## Embeddings and Vector Store

GraphRAG supports embedding names including `text_unit_text`, `entity_description`, and `community_full_content`. The vector store schema controls index names, ID field, vector field, and vector size. A dimension mismatch usually means the embedding model changed without updating vector store schema or clearing/rebuilding incompatible vectors.

## Validation Guidance

- Use `inspect_index_config.py` to summarize effective indexing-related config without printing secret-looking keys.
- Use `validate_index_outputs.py` after runs or before BYOG workflows to catch missing source/output tables.
- Treat `--skip-validation` as a scoped escape hatch, not a general fix. It can let custom workflows proceed, but it can also defer model/config mistakes until a workflow fails mid-run.
