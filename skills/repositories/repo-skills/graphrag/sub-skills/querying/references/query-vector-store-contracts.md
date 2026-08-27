# Query Vector-Store Contracts

GraphRAG query methods create vector-store clients from `settings.yaml`. The default store is LanceDB, but the config model supports LanceDB, Azure AI Search, and Cosmos DB. This sub-skill only validates config shape and local table prerequisites; actual vector connectivity can require credentials and should be tested deliberately.

## Embedding Names by Method

- `global`: no vector store is used by the standard global search path; dynamic community selection uses the chat model to rate reports.
- `local`: uses `entity_description` vectors for semantic entity extraction.
- `drift`: uses `entity_description` vectors and `community_full_content` vectors; report vectors are looked up by `community_reports.id`.
- `basic`: uses `text_unit_text` vectors for baseline chunk retrieval.
- question generation: uses local-search style `entity_description` vectors.

Supported vector-store schema keys are exactly `text_unit_text`, `entity_description`, and `community_full_content`. The config validator fills missing schema entries with defaults, but an external vector backend may still be missing the physical index.

## Config Shape

A typical local LanceDB config is:

```yaml
vector_store:
  type: lancedb
  db_uri: output/lancedb
  index_schema:
    text_unit_text:
      index_name: text_unit_text
      id_field: id
      vector_field: vector
      vector_size: 3072
    entity_description:
      index_name: entity_description
      id_field: id
      vector_field: vector
      vector_size: 3072
    community_full_content:
      index_name: community_full_content
      id_field: id
      vector_field: vector
      vector_size: 3072
```

If `index_name`, `id_field`, `vector_field`, or `vector_size` are customized, make sure the indexer and query runtime use the same names.

## ID-Key Pitfall

The local search factory uses `EntityVectorStoreKey.ID` and passes `embedding_vectorstore_key=EntityVectorStoreKey.ID`. Basic search uses `embedding_vectorstore_key="id"`. Therefore, the vector record ID must match `entities.id` for `entity_description` and `text_units.id` for `text_unit_text`. If a custom or BYOG vector store uses entity titles as vector IDs, the default factory will retrieve poorly or fail unless the factory/context-builder code is intentionally customized to use `EntityVectorStoreKey.TITLE`.

DRIFT additionally calls `search_by_id(report.id)` on the `community_full_content` vector store and assigns the vector to `CommunityReport.full_content_embedding`. If no vector is found, GraphRAG leaves that embedding as `None`; later DRIFT quality or execution may suffer depending on context and search path.

## Dimension Compatibility

Embedding vector dimensions must match the configured vector index schema and the embedding model used at query time. A common failure mode is reusing an index built with one embedding model while `local_search.embedding_model_id`, `drift_search.embedding_model_id`, or `basic_search.embedding_model_id` points at another model with a different dimensionality.

## Practical Checks

- Confirm `settings.yaml` has or defaults the needed schema keys for the method.
- For LanceDB, confirm the vector database directory exists after indexing and contains tables named by `index_schema.*.index_name`.
- For external stores, confirm credentials and network access only when intentionally running a query.
- For BYOG vectors, sample vector IDs and compare them to `entities.id`, `text_units.id`, or `community_reports.id`, not display titles.
- Rebuild or re-embed when vector dimensions, embedding model IDs, or index names changed after indexing.
