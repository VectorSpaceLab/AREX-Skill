# Query Troubleshooting

## Missing Table or Column

Symptoms include `FileNotFoundError`, table-provider errors, or `Column [...] not found in data`. Match the method to its required tables in [input contracts](query-input-contracts.md). If only local search fails, remember `covariates` is optional but `relationships`, `entities`, `text_units`, `communities`, and `community_reports` are not.

## Missing Community Reports

`read_indexer_communities` warns about communities without reports and filters those communities out. Rebuild reports when `communities.community` values do not appear in `community_reports.community`, or lower/raise `--community-level` to a level where reports exist.

## Community-Level Mismatch

GraphRAG filters rows with `level <= community_level`. If the requested level yields no communities or no reports, choose an available level from the tables. Higher levels are smaller communities; lower levels are broader summaries. Dynamic global selection still respects the maximum level cap.

## Local Context Proportions

Local search raises an error when `local_search.community_prop + local_search.text_unit_prop > 1`. Reduce one or both settings in config. DRIFT has separate local-search proportions under `drift_search.local_search_community_prop` and `drift_search.local_search_text_unit_prop`; check both when DRIFT local follow-up context fails.

## Wrong Vector IDs or Index Names

Local search expects `entity_description` vector IDs keyed by `entities.id`, not entity title. Basic search expects `text_unit_text` vector IDs keyed by `text_units.id`. DRIFT expects `community_full_content` vector IDs keyed by `community_reports.id`. If a custom vector store uses titles or human-readable IDs, either rebuild vectors with canonical IDs or intentionally adapt the factory/context-builder.

## DRIFT Missing Report Content or Embeddings

DRIFT needs community reports with `full_content` and a `community_full_content` vector store. If `full_content` is missing, BYOG reports are incomplete. If report vectors are missing, GraphRAG sets `full_content_embedding` to `None` after failed lookup; rebuild `community_full_content` vectors or check `index_schema.community_full_content.index_name` and vector IDs.

## Incompatible Embedding Dimensions

Dimension errors usually mean the vector index was built with a different embedding model or vector size than the query config. Compare `vector_store.index_schema.*.vector_size` with the embedding model dimensions for `local_search`, `drift_search`, and `basic_search`, then rebuild affected vector indexes.

## Empty DRIFT Query

DRIFT and local search ultimately embed or expand the user query. Empty or whitespace-only queries can skip entity extraction or produce invalid follow-up actions. Ask the user for a concrete question before running DRIFT.

## JSON Map Parsing Warnings

Global map-reduce and DRIFT action parsing can warn when the LLM returns malformed JSON-like content. Tighten `response_type`, lower temperature where configurable, reduce prompt customizations, or inspect whether token truncation cut off structured output.

## Token Budget Truncation

If answers omit expected context, inspect `global_search.max_context_tokens`, `global_search.data_max_tokens`, `local_search.max_context_tokens`, `basic_search.max_context_tokens`, and DRIFT local/data token settings. Large community levels, high `top_k_entities`, or high text-unit/community proportions can crowd out relevant records.

## Native Verification Candidates

Useful safe evidence checks include unit tests around entity extraction, dynamic community selection, and input retrieval. Notebook-style local/global/DRIFT examples are evidence for behavior, but do not make a runtime skill depend on original notebook paths or example datasets.
