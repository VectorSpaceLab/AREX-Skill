# Search API reference

All public retrieval APIs are async. Examples assume data has already been added and memorized by the appropriate workflow.

## Imports

```python
import m_flow
from m_flow.search.types import RecallMode
from m_flow.api.v1.search import SearchConfig, QueryResult
```

The package exports `search`, `query`, `QueryResult`, `SearchConfig`, and `RecallMode` from the search API package.

## RecallMode values

```python
RecallMode.CHUNKS_LEXICAL
RecallMode.TRIPLET_COMPLETION
RecallMode.CYPHER
RecallMode.EPISODIC
RecallMode.PROCEDURAL
```

Mode-string mapping for the simplified query helper:

| `query(mode=...)` | RecallMode |
|---|---|
| `"episodic"` | `RecallMode.EPISODIC` |
| `"triplet"` | `RecallMode.TRIPLET_COMPLETION` |
| `"chunks"` | `RecallMode.CHUNKS_LEXICAL` |
| `"procedural"` | `RecallMode.PROCEDURAL` |
| `"cypher"` | `RecallMode.CYPHER` |

Unknown mode strings fall back to `episodic` with a warning.

## Simplified `query()`

```python
result = await m_flow.query(
    question="What decisions were made about database migration?",
    datasets="team-memory",
    mode="episodic",
    top_k=5,
)

print(result.answer)     # populated mainly for triplet mode
print(result.context)    # list for episodic/chunks/procedural; dict for triplet
print(result.datasets)   # dataset names that contributed results
```

Signature:

```python
query(question: str, datasets=None, mode: str = "episodic", top_k: int = 10) -> QueryResult
```

Use `query()` for simple user-facing Q&A. Use `search()` when you need recall-mode enums, graph/detail output, scoring knobs, collection selection, or custom prompts.

## Advanced `search()`

Important public parameters:

```python
results = await m_flow.search(
    query_text="Which migration missed the P99 target?",
    query_type=RecallMode.EPISODIC,
    datasets=["team-memory"],        # names
    # dataset_ids=[...],              # UUIDs, alternative to datasets
    top_k=5,
    node_name=None,                   # MemorySpace/node filter; often leave unset
    only_context=False,
    use_combined_context=False,
    session_id="debug-session",
    wide_search_top_k=150,
    triplet_distance_penalty=3.5,
    verbose=True,
    enable_hybrid_search=True,
    enable_time_bonus=True,
    edge_miss_cost=0.9,
    hop_cost=0.05,
    full_number_match_bonus=0.12,
    enable_adaptive_weights=True,
    display_mode="detail",
    max_facets_per_episode=4,
    max_points_per_facet=8,
    collections=[
        "Episode_summary",
        "Facet_search_text",
        "Facet_anchor_text",
        "FacetPoint_search_text",
        "Entity_name",
        "RelationType_relationship_name",
    ],
)
```

Return shape:

- default `TRIPLET_COMPLETION` can return a `CombinedSearchResult` when combined context is enabled, otherwise a list of `SearchResult` wrappers;
- `EPISODIC`, `CHUNKS_LEXICAL`, and `PROCEDURAL` normally return a list of `SearchResult` wrappers;
- `SearchResult.search_result` holds the actual text, edge list, or retriever-specific object;
- `dataset_id` and `dataset_name` are set when access-controlled dataset metadata is available.

Direct parameters override a supplied `SearchConfig` when both are present.

## `SearchConfig`

`SearchConfig` bundles less-common graph/LLM parameters:

```python
config = SearchConfig(
    system_prompt="Answer only from retrieved context.",
    system_prompt_path="direct_answer.txt",
    save_interaction=False,
    use_combined_context=False,
    wide_search_top_k=100,
    triplet_distance_penalty=3.5,
    verbose=True,
)

results = await m_flow.search(
    query_text="Summarize recent Neo4j decisions",
    query_type=RecallMode.TRIPLET_COMPLETION,
    top_k=10,
    config=config,
)
```

Use `SearchConfig` when you repeatedly call `search()` with the same advanced defaults. Keep per-call direct arguments for one-off overrides.

## Episodic tuning knobs

| Parameter | Default evidence | Effect | First-use advice |
|---|---:|---|---|
| `top_k` | 10 | number of Episodes/results after scoring | lower to 3-5 when broad queries are noisy |
| `wide_search_top_k` | 100 | candidates per vector collection before graph projection | raise when relevant facts are missing |
| `triplet_distance_penalty` | 3.5 | graph projection distance penalty | keep default unless graph paths look over-expanded |
| `edge_miss_cost` | 0.9 | cost when an edge lacks vector-hit evidence | increase to punish weak structural paths; lower when edge embeddings are sparse |
| `hop_cost` | 0.05 | per-hop traversal cost | increase to prefer direct/local paths |
| `full_number_match_bonus` | 0.12 | score reduction for exact numeric matches | useful for metric/date/version questions |
| `enable_hybrid_search` | true | keyword+vector fallback for short/numeric/mixed-language queries | keep enabled for terse user queries |
| `enable_time_bonus` | true | query-time parsing and temporal bonus | keep enabled for "when", dates, ranges, or recency questions |
| `enable_adaptive_weights` | true | query-specific node/edge confidence weighting | disable only for A/B debugging |
| `display_mode` | `summary` | output assembler mode | use `highly_related_summary` or `detail` for noisy broad summaries |
| `max_facets_per_episode` | 4 | detail-mode facets per Episode | lower for concise graph evidence |
| `max_points_per_facet` | 8 | detail point cap where applicable | useful if detail output becomes too large |
| `collections` | mode-specific defaults | vector collections to search | include precise collections for fact-heavy queries |

Environment equivalents for episodic defaults include `MFLOW_EPISODIC_TOP_K`, `MFLOW_EPISODIC_WIDE_SEARCH_TOP_K`, `MFLOW_EPISODIC_EDGE_MISS_COST`, `MFLOW_EPISODIC_HOP_COST`, `MFLOW_EPISODIC_MAX_FACETS_PER_EPISODE`, `MFLOW_EPISODIC_MAX_POINTS_PER_FACET`, and `MFLOW_EPISODIC_DISPLAY_MODE`.

## Collection names

Common episodic collections:

- `Episode_summary`
- `Facet_search_text`
- `Facet_anchor_text`
- `FacetPoint_search_text`
- `Entity_name`
- `Concept_name` for older data compatibility
- `RelationType_relationship_name` for edge semantics / `edge_text`

Default triplet search uses `Episode_summary`, `Entity_name`, legacy `Concept_name`, and auto-includes `RelationType_relationship_name` unless the caller supplies different collections.

## Display-mode recipes

### Concise event recall

```python
results = await m_flow.search(
    query_text="What happened with the database migration?",
    query_type=RecallMode.EPISODIC,
    top_k=5,
    display_mode="summary",
)
```

### Explain why a result matched

```python
results = await m_flow.search(
    query_text="Was P99 under 500ms?",
    query_type=RecallMode.EPISODIC,
    top_k=3,
    display_mode="detail",
    verbose=True,
)
```

Detail mode exposes Episode→Facet and Episode→Entity edges so you can reason about graph support instead of only reading Episode summaries.

### Reduce broad-summary noise

```python
results = await m_flow.search(
    query_text="Which migration decisions affected latency?",
    query_type=RecallMode.EPISODIC,
    top_k=3,
    display_mode="highly_related_summary",
    max_facets_per_episode=2,
)
```

This keeps only summary sections tied to matched Facets when the Episode summary contains unrelated sections.

## TRIPLET_COMPLETION and LLM dependency

`TRIPLET_COMPLETION` retrieves graph context and asks an LLM to answer. If vector/graph retrieval succeeds but answers fail or return malformed text, inspect LLM configuration:

```bash
export MFLOW_LLM_PROVIDER=custom
export MFLOW_LLM_MODEL=deepseek-chat
export MFLOW_LLM_ENDPOINT=https://api.deepseek.com
export MFLOW_LLM_API_KEY='...'
export MFLOW_LLM_INSTRUCTOR_MODE=json_mode
```

Common fixes:

- prefix unknown model names with `openai/` to force OpenAI-compatible LiteLLM routing;
- omit a trailing `/v1` from endpoints when the provider expects a base URL;
- switch to `MFLOW_LLM_INSTRUCTOR_MODE=markdown_json_mode` if structured output is raw Markdown/text;
- configure `MFLOW_LLM_RATE_LIMIT_ENABLED`, `MFLOW_LLM_RATE_LIMIT_REQUESTS`, and `MFLOW_LLM_RATE_LIMIT_INTERVAL` for rate-limited providers.

## REST API shape

Search endpoint payload sketch:

```json
POST /api/v1/search
{
  "recall_mode": "EPISODIC",
  "datasets": ["team-memory"],
  "query": "Which migration missed the P99 target?",
  "top_k": 3,
  "verbose": true,
  "display_mode": "detail",
  "wide_search_top_k": 150,
  "enable_hybrid_search": true,
  "enable_time_bonus": true,
  "collections": ["FacetPoint_search_text", "Facet_search_text", "Entity_name", "RelationType_relationship_name"]
}
```

Simplified endpoint payload sketch:

```json
POST /api/v1/search/query
{
  "question": "What were the database migration decisions?",
  "datasets": ["team-memory"],
  "mode": "episodic",
  "top_k": 5
}
```

The remote `/query` endpoint binds the authenticated user so dataset visibility matches the regular `/search` endpoint.

## CLI

The `mflow search` command is useful for quick smoke tests after data already exists:

```bash
mflow search "database migration" --query-type EPISODIC --top-k 5
mflow search "MATCH (n) RETURN n LIMIT 5" --query-type CYPHER --output-format json
mflow search "Summarize Neo4j capabilities" --query-type TRIPLET_COMPLETION --datasets team-memory
```

CLI mode names are the enum names: `TRIPLET_COMPLETION`, `EPISODIC`, `PROCEDURAL`, `CYPHER`, and `CHUNKS_LEXICAL`.

## Safety notes

- Do not use `CYPHER` for arbitrary untrusted text. It is raw graph query execution and may be disabled by `ALLOW_CYPHER_QUERY=false`.
- `only_context=True` skips LLM completion and is useful to isolate retrieval from LLM issues.
- `use_combined_context=True` merges contexts across datasets before answer generation; use it intentionally when cross-dataset synthesis is desired.
- Dataset-name filters are resolved to authorized dataset IDs for authenticated users; permission-denied REST paths may return empty lists or 403/409 responses depending on endpoint.
