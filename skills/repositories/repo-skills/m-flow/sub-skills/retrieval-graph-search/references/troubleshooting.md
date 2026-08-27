# Retrieval troubleshooting

Use this page after you know the task is retrieval/search over already-memorized data. If data has not been ingested or memorized, route to the core or ingestion sub-skill instead of debugging search.

## Fast triage sequence

1. **Separate retrieval from LLM.** Run the same query with `only_context=True` or `query_type=RecallMode.EPISODIC` before debugging `TRIPLET_COMPLETION` answers.
2. **Check the graph is not empty.** Search logs may warn `knowledge graph has no data`, `Searching an empty knowledge graph`, or `Graph is empty, returning no results`.
3. **Use detail output.** Set `display_mode="detail"`, `top_k=3`, and `verbose=True` to inspect supporting facets/entities.
4. **Probe config/imports.** Run `python scripts/backend_config_probe.py --json` before assuming a remote service is broken.
5. **Only then tune scoring.** Change one parameter at a time: `top_k`, `wide_search_top_k`, `display_mode`, `collections`, then costs/bonuses.

## Empty results

| Symptom | Likely cause | Action |
|---|---|---|
| warning: graph has no data / graph is empty | no memorized graph in selected backend | route to core/ingestion workflow; or verify you are pointing at the same graph backend used during memorize. |
| empty list but graph is populated | vector collections missing in selected vector backend | check collection names, provider switch, and whether data was memorized into this vector store. |
| empty for one dataset only | bad dataset name or permission filtering | try no dataset filter; confirm authenticated user can read dataset. |
| empty in `EPISODIC`, non-empty in `CHUNKS_LEXICAL` | episodic graph nodes/collections missing or wrong `MemorySpace` filter | remove custom `node_name`; include episodic collections; rememorize with episodic memory enabled. |
| `CollectionNotFoundError` swallowed as empty | collection was not created for this backend/data | add collection explicitly only if it exists; otherwise rememorize or use available collections. |
| `ValueError: query string` | blank or non-string query | validate user input before calling `search()`. |
| `top_k must be greater than zero` | invalid limit | set `top_k >= 1`. |

Minimal isolation check:

```python
from m_flow.search.types import RecallMode

ctx = await m_flow.search(
    query_text="database migration",
    query_type=RecallMode.EPISODIC,
    top_k=3,
    only_context=True,
    display_mode="detail",
)
print(ctx)
```

If this is empty, do not spend time on LLM prompts yet.

## Noisy or over-broad results

Broad Episode summaries can match many topic-adjacent queries. Bundle Search intentionally adds a direct Episode penalty, but a broad direct path may still win when precise collections are missing or a query is underspecified.

### First knobs

```python
results = await m_flow.search(
    query_text="Which database migration decision affected P99 latency?",
    query_type=RecallMode.EPISODIC,
    top_k=3,
    display_mode="highly_related_summary",
    max_facets_per_episode=2,
    wide_search_top_k=150,
    collections=[
        "FacetPoint_search_text",
        "Facet_search_text",
        "Facet_anchor_text",
        "Entity_name",
        "RelationType_relationship_name",
    ],
)
```

If still noisy:

- switch to `display_mode="detail"` to see whether matched Facets/Entities are relevant;
- reduce `top_k` to 1-3 for user-facing answers;
- keep `enable_hybrid_search=True` for short/numeric/mixed-language queries;
- keep `full_number_match_bonus` at or above default for metric/version/date queries;
- increase `edge_miss_cost` if results seem connected by weak or irrelevant edges;
- increase `hop_cost` if long paths outrank obvious local evidence;
- avoid disabling `direct_episode_penalty` logic; it is the main guard against generic summaries dominating.

## Missing precise fact despite broad related results

Use this pattern when a result mentions the right topic but misses a specific fact:

1. Include `FacetPoint_search_text` and `RelationType_relationship_name` in `collections`.
2. Raise `wide_search_top_k` to 150-300 to let precise hits enter graph projection.
3. Ensure `display_mode` is not hiding support: use `detail` for inspection.
4. If the query contains a number, leave `enable_hybrid_search=True` and `full_number_match_bonus` enabled.
5. If the query contains a date/range, leave `enable_time_bonus=True` and inspect time fields.

```python
results = await m_flow.search(
    query_text="P99 under 500ms on May 7",
    query_type=RecallMode.EPISODIC,
    top_k=3,
    display_mode="detail",
    wide_search_top_k=250,
    enable_hybrid_search=True,
    enable_time_bonus=True,
)
```

## Temporal recall looks wrong

M-flow distinguishes semantic event time from ingestion time:

- `mentioned_time_start_ms` / `mentioned_time_end_ms` / `mentioned_time_text`: time found in the content;
- `created_at`: record/ingestion time fallback.

Triage:

1. Query with an explicit date/range and `display_mode="detail"`.
2. Check whether returned nodes include `mentioned_time_*` values.
3. Keep `enable_time_bonus=True`; for debug logs, set `EPISODIC_TIME_DEBUG=true`.
4. If only `created_at` is present, remember it may be ingestion time, not event time.
5. Treat timestamp migration utilities as reference-only and dry-run-only unless the user explicitly asks for a migration.

## Backend provider errors

Run:

```bash
python scripts/backend_config_probe.py --provider neo4j
python scripts/backend_config_probe.py --kind vector --provider pgvector --json
```

Common signals:

| Signal | Meaning | Fix |
|---|---|---|
| `Unknown graph provider` / `Unknown vector provider` | provider name not in built-in registry | use names from the probe: `kuzu`, `neo4j`, `pgvector`, `lancedb`, etc. |
| `Missing required configuration: Neo4j URL` | graph provider selected without URL | set `GRAPH_DATABASE_URL` or config field `graph_database_url`. |
| `Missing PGVector credentials` | pgvector selected but relational Postgres settings incomplete | set all `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`. |
| `ChromaDB not installed` | optional extra missing | install ChromaDB extra/dependency in the active environment. |
| `langchain_aws is required` | Neptune extra missing | install Neptune/AWS dependency and configure AWS access. |
| connection refused / DNS / auth failed | import/config ok but service unreachable | start service, fix URI/credentials/network, or switch back to local default. |
| old data vanished after provider switch | graph/vector provider points at a different physical store | rememorize into new backend or migrate intentionally. |

## Cypher mode safety

`RecallMode.CYPHER` executes the query against the configured graph provider. It is for users who intentionally provide Cypher/openCypher. Do not pass arbitrary natural language to Cypher mode.

- If `ALLOW_CYPHER_QUERY=false`, M-flow raises an unsupported-mode error for Cypher.
- If the graph is empty, Cypher returns no results and logs a warning.
- If the query fails, errors are wrapped as `CypherSearchError`.

Safe smoke query:

```python
rows = await m_flow.search(
    query_text="MATCH (n) RETURN n LIMIT 5",
    query_type=RecallMode.CYPHER,
    top_k=5,
)
```

## TRIPLET_COMPLETION answer failures

`TRIPLET_COMPLETION` uses retrieval plus LLM completion. If `EPISODIC`/context retrieval works but `TRIPLET_COMPLETION` fails:

| Signal | Likely cause | Fix |
|---|---|---|
| model not found | provider/model name not recognized by LiteLLM | prefix model with `openai/` for OpenAI-compatible endpoints. |
| JSON/structured output parse failures | provider ignores JSON mode | set `MFLOW_LLM_INSTRUCTOR_MODE=markdown_json_mode`. |
| endpoint 404 or double `/v1` | base URL format mismatch | use provider base URL expected by LiteLLM; avoid duplicate `/v1` unless provider requires it. |
| rate limit / timeout | provider quota or concurrency limit | enable rate limits or reduce request concurrency. |
| content-policy fallback expected but not used | fallback not configured | set fallback model, endpoint, and key. |

LLM smoke idea:

```bash
python - <<'PY'
import asyncio
from pydantic import BaseModel
from m_flow.llm.backends.litellm_instructor.llm.get_llm_client import create_llm_backend

class TestResponse(BaseModel):
    greeting: str

async def main():
    backend = create_llm_backend()
    result = await backend.extract_structured(
        text_input='Say hello',
        system_prompt='Respond with a JSON greeting.',
        response_model=TestResponse,
    )
    print('success', result.greeting)

asyncio.run(main())
PY
```

## Embedding issues

Vector search requires an embedding engine. Relevant variables:

```bash
export EMBEDDING_PROVIDER=openai
export EMBEDDING_MODEL=openai/text-embedding-3-large
export EMBEDDING_DIMENSIONS=3072
export EMBEDDING_ENDPOINT=''
export EMBEDDING_API_KEY='...'   # may fall back to LLM_API_KEY in some setups
```

For local or alternative embeddings, verify the provider's own extra/dependency and dimensionality compatibility with existing vector collections. Changing embedding dimensions without rebuilding collections can produce search failures or invalid distances.

## When to rememorize instead of tuning

Rememorize or route to ingestion when:

- selected backend has no corresponding vector collections;
- graph has no `Episode`, `Facet`, `FacetPoint`, or `Entity` topology for episodic search;
- old data was memorized before the current episodic/procedural schema existed;
- embedding model/dimensions changed after collections were written;
- provider switch intentionally points at a fresh empty graph/vector store.
