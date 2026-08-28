# Per-Source Configuration

## Default object

```json
{
  "kind": "classic",
  "chunking": {
    "strategy": "classic_chunk",
    "max_tokens": 1250,
    "min_tokens": 150,
    "duplicate_headers": false
  },
  "retrieval": {
    "retriever": "classic",
    "exposure": "prefetch",
    "chunks": 2,
    "score_threshold": null,
    "rephrase_query": true,
    "reranker": null,
    "prescreen": null
  },
  "graph": {
    "extraction_model": null,
    "max_chunks": null,
    "gleanings": 0
  }
}
```

Writes are strict: extra keys or invalid values should be rejected. Reads are lenient for historical data and may fall back to defaults, so a bad stored object can look like classic behavior rather than crash.

## Chunking strategies

| Strategy | Use |
|---|---|
| `classic_chunk` | stable token-window default |
| `recursive` | break on natural character/token boundaries |
| `markdown` | preserve heading/section structure |
| `parent_child` | embed small children while returning larger parent context |
| `semantic` | use embedding distance to split topical changes; extra ingest cost and recursive fallback |

Chunking is bake-time. Re-ingest existing data after changing it.

## Retrieval fields

- `retriever`: `classic`, `hybrid`, or `graphrag`; instance allow-list still applies.
- `exposure`: `prefetch` or `agentic_tool`.
- `chunks`: integer 1–500 in stored config. A configured source value outranks a request-level top-k; request-level `0` can still mean skip retrieval for a turn.
- `score_threshold`: supported meaningfully by pgvector and MongoDB Atlas; other stores may ignore it and return warnings.
- `rephrase_query`: enables a query-rephrasing LLM side call.
- `prescreen`: optional LLM relevance filter.

Pre-screen example:

```json
{
  "candidate_k": 40,
  "batch_size": 10,
  "max_keep": 8,
  "model": null
}
```

All positive fields are bounded to 500. `max_keep <= candidate_k` and `candidate_k >= retrieval.chunks`.

## Updating

```bash
curl -X PATCH "$DOCSGPT_URL/api/sources/$SOURCE_ID/config" \
  -H "Authorization: Bearer $DOCSGPT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"retrieval":{"retriever":"classic","chunks":4}}'
```

The response includes the effective config and whether re-ingestion is required. Editing requires owner or team-editor permission.

Do not change `kind` through this endpoint. Wiki and GraphRAG use dedicated transitions with their own preconditions and jobs.
