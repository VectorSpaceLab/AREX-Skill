# Indexing Troubleshooting

## Model Validation Failures

Symptoms: `graphrag index --dry-run` or `graphrag index` fails before workflows execute, often around model IDs, missing model references, or workflow config names.

Fixes:

- Check completion and embedding model keys referenced by `extract_graph`, `community_reports`, `embed_text`, and query configs.
- Confirm required environment variables are set for `${...}` substitutions.
- Use `--skip-validation` only for intentional no-LLM/custom-workflow cases. It skips preflight validation but does not make invalid workflow settings safe.

## Missing Input Documents

Symptoms: load workflow finds no documents, downstream tables are empty, or update reports no new data.

Fixes:

- Confirm `input_storage.base_dir`, input type, file pattern, and file extensions.
- For CSV/JSON, confirm `text_column`, `title_column`, and optional metadata columns exist.
- For API use, validate `input_documents` has `id`, `text`, `title`, `creation_date`, and optional `metadata` columns.

## Invalid Storage or Output Directories

Symptoms: cannot create/read output, reports, cache, update output, or vector store paths.

Fixes:

- Verify file-backed base directories are writable and not accidentally pointed at input data.
- Confirm blob/cosmos credentials and namespaces outside committed config.
- For update, check both `output_storage` and `update_output_storage`.

## Missing Previous Output for Update

Symptoms: `graphrag update` fails while copying previous tables or merge workflows cannot find prior entities/relationships/text units.

Fixes:

- Run `validate_index_outputs.py --output <output-dir> --use <global|local|drift|basic>` before updating.
- Ensure previous output belongs to the same GraphRAG config family and table provider.
- Rebuild a full index if previous outputs are incomplete or incompatible.

## No New Documents in Update

Symptoms: update completes quickly, delta tables are empty, or merged output does not change.

Fixes:

- Check input file discovery and document IDs/titles.
- Confirm the update set contains genuinely new or changed text, not only copied files.
- Inspect update logs and `stats.json` for workflows that ran with zero rows.

## Skipped Embeddings from Missing Tables

Symptoms: `generate_text_embeddings` or `update_text_embeddings` skips embedding targets or emits missing-source-table messages.

Fixes:

- Confirm source tables exist for configured embedding names: `text_units` for `text_unit_text`, `entities` for `entity_description`, and `community_reports` for `community_full_content`.
- For BYOG, include `text_units` before requesting local/DRIFT/basic-ready embeddings.
- Disable unused embedding names rather than letting a partial BYOG table set fail late.

## Vector Dimension Mismatch

Symptoms: vector store insert/query errors mention vector length, schema, or incompatible index dimensions.

Fixes:

- Align `vector_store.index_schema.*.vector_size` with the configured embedding model.
- Clear or rebuild old vector indexes after changing embedding models or dimensions.
- Keep query-time embedding config consistent with index-time embedding config.

## FastGraphRAG NLP/SpaCy Issues

Symptoms: `fast` method fails in `extract_graph_nlp`, attempts to download a SpaCy model, or returns poor/non-language-appropriate noun phrases.

Fixes:

- Use default regex extraction for quick English trials.
- Install the configured SpaCy model ahead of time when using `syntactic_parser` or `cfg`.
- Tune chunk size smaller than typical standard GraphRAG settings for co-occurrence quality.
- Consider `standard` when entity descriptions and high-fidelity relationships matter.

## BYOG Source Table Problems

Symptoms: custom `workflows` fail because `entities`, `relationships`, or `text_units` are absent or have missing columns.

Fixes:

- Use `validate_index_outputs.py --use byog --byog-workflows ...` before running.
- Ensure relationship endpoints match entity titles.
- Keep `relationship.weight` numeric; Leiden clustering uses it.
- Use `create_community_reports_text` only when `text_unit_ids` links are valid.

## Incremental Relationship Orphans

Symptoms: update merge produces relationships whose source or target no longer exists, or later graph workflows fail on endpoints.

Fixes:

- Verify merged entities before merged relationships.
- Filter orphan relationships after combining old and delta relationships.
- Add a focused update regression case with duplicate, deleted, and new titles plus hallucinated delta endpoints.

## Cost and Resource Warnings

Symptoms: high token cost, rate-limit failures, slow runs, large memory use, or excessive vector writes.

Fixes:

- Start with a small input subset and `--dry-run`.
- Use cache for iterative prompt/config work.
- Consider `fast` for exploratory indexing.
- Tune chunk size, concurrency/rate limits, and embedding targets.
- Avoid enabling claim extraction or all embedding targets unless they are required.
