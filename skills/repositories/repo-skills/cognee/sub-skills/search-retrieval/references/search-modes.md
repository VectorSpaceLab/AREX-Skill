# Search and Recall Modes

Read this when you need to map a user query to the right Cognee retrieval mode.

## Public mode set

Verified `SearchType` values in the installed package:

- `SUMMARIES`
- `CHUNKS`
- `RAG_COMPLETION`
- `HYBRID_COMPLETION`
- `TRIPLET_COMPLETION`
- `GRAPH_COMPLETION`
- `GRAPH_COMPLETION_DECOMPOSITION`
- `GRAPH_SUMMARY_COMPLETION`
- `CYPHER`
- `NATURAL_LANGUAGE`
- `GRAPH_COMPLETION_COT`
- `GRAPH_COMPLETION_CONTEXT_EXTENSION`
- `FEELING_LUCKY`
- `TEMPORAL`
- `CODING_RULES`
- `CHUNKS_LEXICAL`
- `AGENTIC_COMPLETION`
- `CODE`

## How to choose

| Intent | Good default | Why |
| --- | --- | --- |
| General question about stored knowledge | `GRAPH_COMPLETION` | Balanced graph-backed answer path. |
| Need the raw supporting passages | `CHUNKS` | Returns chunk-level matches. |
| Need a quick summary | `SUMMARIES` | Uses precomputed summaries when available. |
| Want a graph answer but no session scope | `search(...)` | Lower-level query control. |
| Want session-aware recall | `recall(...)` | Session-first routing and graph fallback. |
| Need exact code graph traversal | `CODE` | Deterministic code-graph search. |
| Need time-aware answers | `TEMPORAL` | Time-sensitive retrieval. |
| Want the system to pick for you | `FEELING_LUCKY` | Uses query routing heuristics. |
| Want agentic tool use | `AGENTIC_COMPLETION` | Allows `skills`, `tools`, and `max_iter`. |

## Query knobs that matter

- `datasets` / `dataset_ids` narrow the search scope.
- `top_k` controls result count.
- `node_name` and `node_name_filter_operator` scope graph results by entity name.
- `only_context=True` returns context-heavy output instead of a full answer.
- `include_references=True` asks for evidence references when supported.
- `scope` on `recall` controls whether the search consults session, graph, trace, or both.
- `feedback_influence` changes ranking behavior when feedback is available.

## Constraint matrix

| Combination | Result |
| --- | --- |
| `code_query` with anything other than `CODE` | Invalid. |
| `skills` or `tools` with anything other than `AGENTIC_COMPLETION` | Invalid. |
| `scope="graph_context"` | Deprecated alias; use `graph`. |
| `neighborhood_depth` / `neighborhood_seed_top_k` less than 1 | Invalid. |

## Recommended routing

- If the user says “recall what I just said,” use `recall`.
- If the user says “search my graph,” use `search` with `GRAPH_COMPLETION` or `CHUNKS`.
- If the user says “find the exact code path / impact path,” use `CODE`.
- If the user says “what changed over time,” use `TEMPORAL`.
- If the user says “let the model choose,” use `FEELING_LUCKY`.
