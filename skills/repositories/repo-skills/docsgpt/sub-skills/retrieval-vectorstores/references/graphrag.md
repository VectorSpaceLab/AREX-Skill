# GraphRAG

GraphRAG extracts entities and relationships from source chunks during ingestion and uses Personalized PageRank-style graph traversal at query time.

## Hard requirements

```env
VECTOR_STORE=pgvector
GRAPHRAG_ENABLED=true
```

Also require:

- pgvector extension/schema ready;
- a configured extraction LLM;
- embedding dimension consistent with graph/vector tables;
- Celery workers for extraction;
- a cost/time budget.

Use the upload-time GraphRAG selector or:

```bash
curl -X POST "$DOCSGPT_URL/api/sources/$SOURCE_ID/graphrag/enable" \
  -H "Authorization: Bearer $DOCSGPT_TOKEN"
```

This returns a task id. Poll it; re-enabling rebuilds rather than no-ops. The generic source config patch cannot convert `kind` to GraphRAG.

## Controls

- `GRAPHRAG_EXTRACTION_MODEL`: instance extraction-model override; unset reuses the default model.
- `GRAPHRAG_MAX_CHUNKS_FOR_EXTRACTION`: global cost cap, default 2000.
- per-source `graph.extraction_model` and `graph.max_chunks`: overrides.
- `graph.gleanings`: extra extraction passes per chunk; default 0 and adds LLM cost.

## Operational behavior

- Extraction is checkpointed/resumable but a rebuild starts from source chunks again.
- Token usage is attributable to graph extraction.
- Query graph endpoints expose a bounded overview and node-neighbor view.
- If no graph exists yet or extraction failed, retrieval falls back to classic vectors so answers continue without graph context.

## Validation

1. validate prerequisites with `validate_retrieval_plan.py`;
2. ingest a tiny relationship-rich source;
3. poll extraction to terminal state;
4. inspect graph nodes/edges through bounded graph endpoints;
5. ask one direct and one multi-hop question;
6. compare classic and graph-retrieved citations;
7. confirm cost and chunk cap;
8. verify fallback by querying while graph is unavailable.

## Rebuild triggers

Rebuild/re-ingest after source content, chunking, embeddings/dimension, extraction model, or extraction cap/gleanings materially changes. Back up or retain the prior source state until expected multi-hop retrieval passes.
