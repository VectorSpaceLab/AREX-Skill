# RAG Query Troubleshooting

This reference covers query-time problems. Provider setup, credentials, ingestion, CLI behavior, and benchmark metrics are routed to sibling sub-skills unless the issue appears only during RAG agent execution.

## Quick diagnosis table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `No relevant information found for query ...` from `DeepSearch.query` | No chunks retrieved or all chunks rejected by rerank. | Run retrieval-only; compare with `NaiveRAG`; inspect collection routing and ingestion. |
| Empty `refs` from `retrieve` | No matching collection/chunks, embedding/vector DB mismatch, or route selected no collections. | Check `vector_db.list_collections(dim=embedding_model.dimension)` and collection descriptions. |
| `ValueError: Invalid JSON/List format...` | LLM did not return a parseable Python/JSON list for sub-queries, reflection, collection routing, or support-doc indices. | Use a stronger instruction-following/reasoning model; simplify prompt/query; lower router complexity. |
| Router picks wrong RAG agent | Descriptions overlap or model output parsed incorrectly. | Provide explicit mutually exclusive descriptions or instantiate the desired agent directly. |
| High token use | Too many iterations, collections, chunks, rerank calls, or support-doc selection calls. | Use `NaiveRAG`, lower `max_iter`, lower `top_k`, enable `early_stopping`, or narrow collections. |
| Notebook event-loop error | `DeepSearch.retrieve` uses `asyncio.run`. | In notebooks use `nest_asyncio.apply()` or call `async_retrieve` from an owned async context. |
| `naive_retrieve(..., top_k=...)` ignores `top_k` | Wrapper accepts but does not pass `top_k`/`collection` to `configuration.naive_rag`. | Instantiate `NaiveRAG(top_k=...)` manually. |
| Local Milvus Lite lock or stale data | Default URI is cwd-relative `./milvus.db`; concurrent processes can contend. | Use one process per local DB path or configure distinct URIs in provider setup. |

## No relevant information after data is loaded

Use a staged check instead of immediately increasing `max_iter`.

1. **Check raw retrieval with simple terms**

   ```python
   from deepsearcher.online_query import retrieve
   refs, _, tokens = retrieve("exact phrase expected in the loaded document", max_iter=1)
   print(len(refs), tokens)
   ```

2. **Compare with NaiveRAG**

   `DeepSearch` reranks each retrieved chunk and can reject useful chunks if the LLM returns an ambiguous rerank answer. If `NaiveRAG` returns chunks but `DeepSearch` does not, focus on rerank/model behavior.

3. **Inspect collection routing**

   Collection routing can return an empty list when no collections exist, include only the default collection, or include collections with empty descriptions. Make collection descriptions specific and ensure the router uses `embedding_model.dimension`.

4. **Check ingestion ownership**

   If no agent returns chunks, route to `data-ingestion` to check collection creation, chunk size/overlap, loader behavior, and whether data was loaded into the expected vector DB.

5. **Check provider/vector DB setup**

   If collection listing or search errors mention dimensions, connection state, or DB files, route to `provider-configuration`.

## Output parsing failures

DeepSearcher relies on `BaseLLM.literal_eval` and simple string parsing in several places:

- `DeepSearch._generate_sub_queries`: Python `list[str]`.
- `DeepSearch._generate_gap_queries`: Python `list[str]`.
- `CollectionRouter.invoke`: Python `list[str]` of collection names.
- `ChainOfRAG._get_supported_docs`: Python list of document indices.
- `RAGRouter._route`: one integer index, with fallback to the last digit in the model response.

FAQ guidance from project evidence: smaller language models often struggle to follow these output-format prompts. Prefer large reasoning or strong instruction-following models, such as OpenAI o-series, DeepSeek-R1-scale, or Claude Sonnet-class models, when parse stability matters.

Mitigations:

- Lower the complexity of the user query and run with `max_iter=1` while debugging.
- Use direct `NaiveRAG` for evidence checks; it has fewer parse-sensitive steps.
- Provide explicit `agent_descriptions` to `RAGRouter` and keep them short.
- Avoid asking the router to choose among many near-identical agents.
- If using a model that emits `<think>...</think>`, DeepSearcher removes one leading think block via `remove_think`, but extra prose outside expected literals can still fail.

## DeepSearch-specific issues

### Sub-query list parse fails

The first DeepSearch call must produce a Python list of strings. If it returns bullets or explanations, `literal_eval` raises. Use a stronger model or start with `NaiveRAG`/`ChainOfRAG` depending on the task.

### Rerank rejects everything

Rerank acceptance requires response content with `YES` and not `NO`. Responses such as `YES, but not enough` contain both and are rejected. Try a stronger model, shorter chunks, or `NaiveRAG` to bypass rerank.

### Token explosion

DeepSearch can make calls for:

- sub-query generation,
- collection routing per query,
- per-chunk reranking,
- reflection per iteration,
- final summarization.

Reduce `max_iter`, narrow collections, verify `top_k` behavior in the vector DB, or switch to `NaiveRAG`.

## ChainOfRAG-specific issues

### Weak intermediate answers

If the follow-up query is vague, the retrieved documents and intermediate answer will drift. Inspect `metadata["intermediate_context"]` from `retrieve` to see each step.

### Support-doc index parse fails

Support-doc selection must parse as a Python list. Failures usually mean the LLM added prose. Use a stronger model or reduce the number/length of retrieved documents.

### Early stopping never stops

`early_stopping=True` only helps if the reflection answer is exactly `Yes` after `remove_think(...).strip().lower()`. If the model returns explanatory text, the check may not stop. Use fewer `max_iter` or a stricter model.

## NaiveRAG wrapper caveats

The public wrappers declare:

```python
naive_retrieve(query, collection=None, top_k=10)
naive_rag_query(query, collection=None, top_k=10)
```

Current implementation calls `configuration.naive_rag.retrieve(query)` and `configuration.naive_rag.query(query)` without passing `collection` or `top_k`. Treat wrapper `collection` and `top_k` as accepted but ineffective in this checkout. Use manual construction for reliable control:

```python
from deepsearcher.agent import NaiveRAG
rag = NaiveRAG(llm, embedding_model, vector_db, top_k=4, route_collection=True)
answer, refs, tokens = rag.query("...")
```

Also note that the current no-routing branch reads `self.collection_router.all_collections` although `collection_router` is only initialized when routing is enabled. If you need fixed-collection search, prefer configuring descriptions/default collection or wrap the vector DB with the desired collection behavior.

## Collection routing problems

- **No collections**: returns `[]` and zero tokens; query agents then retrieve no chunks.
- **Single collection**: no LLM call; always searches the only collection.
- **Multiple collections**: requires a parseable list of names.
- **Empty descriptions**: always included.
- **Default collection**: always included when present.
- **Dimension mismatch**: routers list collections with `dim=embedding_model.dimension`; if loaded embeddings used a different dimension, collection listing/search can be empty or fail.

## Compatibility warnings relevant to query workflows

These are package-level facts that often surface while trying to query:

- This checkout imports FireCrawl `ScrapeOptions`; `firecrawl-py` 4.x may fail while `2.16.5` worked in inspection. Web loading belongs to `data-ingestion`, but a broken import can prevent setup before query.
- Local Milvus Lite passed with `pymilvus 2.5.8` and `milvus-lite 2.5.1`; `pymilvus` 3.x or `milvus-lite` 3.x produced local DB smoke failures.
- The default Milvus URI is cwd-relative `./milvus.db`; concurrent processes can lock or share the wrong local DB if run from the same directory.
- CLI help initializes providers before argparse, so help can fail without credentials or vector DB readiness. Route CLI help issues to `cli-and-service`.

## When to switch agents under hard cases

### No relevant information after loading data

- If `DeepSearch` returns no info but `NaiveRAG` finds refs: use `NaiveRAG` or change the LLM used for rerank/reflection.
- If all agents return no refs: inspect ingestion and vector DB configuration; do not increase `max_iter` blindly.
- If refs exist but answer is unsupported: use retrieval-only and cite/inspect refs manually.

### Choosing under token constraints

- Use `NaiveRAG` for a first pass and for tight budgets.
- Use `DeepSearch(max_iter=1)` for a broad but bounded report.
- Use `ChainOfRAG(max_iter=2, early_stopping=True)` for multi-hop fact finding.
- Avoid `RAGRouter` when the task already tells you the best agent.
