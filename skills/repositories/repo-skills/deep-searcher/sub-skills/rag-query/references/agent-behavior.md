# RAG Agent Behavior

This reference distills the query-time behavior of DeepSearcher's RAG agents and routers.

## Shared RAGAgent contract

Every RAG agent implements:

- `retrieve(query, **kwargs) -> (retrieved_results, consumed_tokens, metadata)`
- `query(query, **kwargs) -> (answer, retrieved_results, consumed_tokens)`

`consumed_tokens` counts LLM calls made by the agent. Embedding and vector DB calls are not token-counted. Returned results are deduplicated by exact `RetrievalResult.text`.

## `RetrievalResult` and `wider_text`

A `RetrievalResult` has `embedding`, `text`, `reference`, `metadata`, and `score` fields. Query agents use the chunk content as follows:

- If `text_window_splitter=True` and `result.metadata` contains `"wider_text"`, summarization/final-answer prompts use `metadata["wider_text"]`.
- Otherwise, prompts use `result.text`.

Use `wider_text` when source chunks were split with surrounding context and you want the LLM to see a broader passage than the precise vector hit. Disable `text_window_splitter` when wider windows are too large, duplicate unrelated context, or hide the exact matching sentence.

## DeepSearch loop

Constructor:

```python
DeepSearch(llm, embedding_model, vector_db, max_iter=3, route_collection=True, text_window_splitter=True)
```

Best for broad reports, surveys, and open-ended synthesis.

### Retrieve sequence

1. **Sub-query generation**: prompts the LLM to break the original query into up to four Python-list string sub-queries. Simple questions may return a one-item list containing the original query.
2. **Search per sub-query**: each current gap query is embedded via `embedding_model.embed_query(query)` and searched in selected collections.
3. **Collection routing**: if `route_collection=True`, `CollectionRouter.invoke(query, dim=embedding_model.dimension)` selects collections. If false, the implementation still reads `self.collection_router.all_collections`.
4. **Rerank per chunk**: for each retrieved chunk, the LLM must answer only `YES` or `NO` to whether it helps answer any query question. Chunks are accepted only when the response contains `YES` and not `NO`.
5. **Deduplicate and accumulate**: accepted chunks are deduplicated by text and added to all search results.
6. **Reflection**: unless this is the final iteration, the LLM receives the original query, all sub-queries, and all chunks, then returns a Python list of up to three gap queries. Empty list stops the loop.
7. **Metadata**: `retrieve` returns metadata `{"all_sub_queries": all_sub_queries}`.

### Query sequence

`query` calls `retrieve`. If no results remain after rerank/reflection, it returns:

```python
(f"No relevant information found for query '{query}'.", [], n_token_retrieval)
```

Otherwise it summarizes all retrieved chunks using the original query and all sub-queries, then returns the final answer, retrieved refs, and total tokens.

### Failure-sensitive steps

- Sub-query generation and reflection require parseable Python lists.
- Rerank requires clean `YES`/`NO`. Ambiguous responses can incorrectly drop useful chunks.
- Token use grows with number of sub-queries, collections, retrieved chunks, and iterations.

## ChainOfRAG loop

Constructor:

```python
ChainOfRAG(llm, embedding_model, vector_db, max_iter=4, early_stopping=False, route_collection=True, text_window_splitter=True)
```

Best for concrete factual questions and multi-hop questions.

### Retrieve sequence

For each iteration up to `max_iter`:

1. **Follow-up query**: prompts the LLM to generate one simple follow-up question from previous intermediate Q/A and the main query.
2. **Collection-routed retrieval**: embeds the follow-up query and searches selected collections.
3. **Intermediate answer**: prompts the LLM to answer the follow-up using only retrieved documents, or respond `No relevant information found` when documents are not useful.
4. **Support-doc selection**: if the intermediate answer is not `No relevant information found`, prompts the LLM to return a Python list of indices of documents that support that Q/A pair.
5. **Intermediate context update**: appends `Intermediate queryN` and `Intermediate answerN` to metadata context.
6. **Optional early stopping**: if `early_stopping=True`, prompts the LLM to answer `Yes`/`No` for whether enough information exists to answer the main query. `Yes` stops the loop.

`retrieve` returns deduplicated support documents and metadata `{"intermediate_context": intermediate_contexts}`.

### Query sequence

`query` calls `retrieve`, then prompts the LLM to generate a final answer from:

- formatted retrieved support documents,
- intermediate queries and answers,
- the main query.

Unlike `DeepSearch.query`, there is no explicit hard-coded no-results answer; if no support docs are selected, the final answer depends on the LLM prompt and intermediate context.

### Failure-sensitive steps

- Follow-up query quality strongly affects retrieval quality.
- Support-doc selection must be a parseable Python list of indices.
- `early_stopping=True` saves tokens only if the LLM reliably returns exactly `Yes` or `No`.

## NaiveRAG behavior

Constructor:

```python
NaiveRAG(llm, embedding_model, vector_db, top_k=10, route_collection=True, text_window_splitter=True)
```

Best for cheap direct retrieval and summarization.

### Retrieve sequence

1. If routing is enabled, `CollectionRouter` selects collections.
2. For each selected collection, the query is embedded and `vector_db.search_data` is called with `top_k=max(self.top_k // len(selected_collections), 1)`.
3. Results are deduplicated by text.
4. `retrieve` returns `(all_retrieved_results, route_tokens, {})`.

### Query sequence

`query` formats each retrieved chunk, preferring `wider_text` when enabled, then asks the LLM to summarize a detailed answer based on the original query and related chunks.

Unlike `DeepSearch`, `NaiveRAG` does not explicitly stop with a no-results message. If no chunks are returned, it still calls the LLM with an empty related-chunks section; the answer may be generic unless the model follows the prompt conservatively.

## RAGRouter behavior

Constructor:

```python
RAGRouter(llm, rag_agents, agent_descriptions=None)
```

Behavior:

1. Builds a numbered list of agent descriptions.
2. Prompts the LLM to select one agent index only.
3. Parses the index. If direct integer parsing fails, it tries to find the last digit in the response as a fallback.
4. Calls only that selected agent's `retrieve` or `query`.
5. Adds routing token count to the selected agent's token count.

If `agent_descriptions` is omitted, it tries to read `__description__` from each agent class. `DeepSearch` and `ChainOfRAG` have descriptions from decorators. Provide explicit descriptions when using custom agents or when you want cost-sensitive routing that includes `NaiveRAG`.

## CollectionRouter behavior

Constructor:

```python
CollectionRouter(llm, vector_db, dim)
```

Behavior:

- On construction, captures `all_collections` from `vector_db.list_collections(dim=dim)`.
- On `invoke(query, dim)`, re-lists collections for the provided dimension.
- If no collections exist, returns empty selection and zero tokens.
- If one collection exists, returns it without asking the LLM.
- If multiple collections exist, asks the LLM to return a Python `list[str]` of collection names based on collection names/descriptions.
- Adds collections whose description is empty, because the router cannot rule them out.
- Adds the vector DB default collection, if present, even when the LLM did not select it.

Collection descriptions matter. Use concise domain labels such as `"Quarterly customer renewal notes"` rather than generic text such as `"documents"`.

## Agent choice under token constraints

- Start with `NaiveRAG(top_k=3..6)` to confirm evidence exists.
- Use `DeepSearch(max_iter=1)` when the user asks for a broad answer but cost is tight.
- Use `DeepSearch(max_iter=2..3)` only when reflection is likely to add value.
- Use `ChainOfRAG(max_iter=2..3, early_stopping=True)` for multi-hop factual questions.
- Avoid a router for one-off known workloads; instantiate the intended agent directly to skip routing tokens and avoid misrouting.
