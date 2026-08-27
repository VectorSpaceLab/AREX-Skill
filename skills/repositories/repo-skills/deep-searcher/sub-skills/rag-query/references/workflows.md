# RAG Query Workflows

Use these workflows after provider setup and data ingestion are complete.

## Choose the RAG path

| Need | Use | Why | Main tradeoff |
| --- | --- | --- | --- |
| Lowest-cost answer over loaded data | `NaiveRAG` or `naive_rag_query` | One retrieval pass plus one summarization call. | No sub-query expansion, reranking, reflection, or support-doc filtering. |
| Broad report, survey, or open-ended synthesis | `DeepSearch` | Decomposes the original query, searches sub-queries, reranks chunks, reflects for gap queries, then summarizes. | More LLM calls and stricter output parsing. |
| Concrete factual or multi-hop answer | `ChainOfRAG` | Builds follow-up queries from intermediate answers, retrieves/answers each step, filters support docs, then writes a final answer. | Iterative and token-heavy; may need `early_stopping=True` to control cost. |
| Unsure which agent fits per query | `RAGRouter` | Uses descriptions to pick exactly one RAG agent. | Adds a routing LLM call and can misroute if descriptions are vague or model output parsing fails. |

## Standard query workflow

```python
from deepsearcher.configuration import Configuration, init_config
from deepsearcher.online_query import query

config = Configuration()
# Configure providers in provider-configuration before init_config if defaults are not desired.
init_config(config=config)

# Load data in data-ingestion before querying.
answer, refs, consumed_tokens = query("What are the documented renewal risks?", max_iter=2)

print(answer)
for ref in refs:
    print(ref.reference, ref.score, ref.text[:200])
print("tokens:", consumed_tokens)
```

Use `max_iter=1` for a quick answer or while debugging. Increase `max_iter` only when the question needs additional sub-queries or follow-up reasoning and token budget allows it.

## Retrieval-only workflow

Use retrieval-only when the downstream task wants evidence inspection, citations, or a custom answer generator.

```python
from deepsearcher.online_query import retrieve

refs, _, consumed_tokens = retrieve("Which paragraph defines the warranty period?", max_iter=1)
if not refs:
    print("No chunks found. Check collection selection, ingestion, and query wording.")
else:
    for i, result in enumerate(refs):
        text_for_display = result.metadata.get("wider_text", result.text)
        print(f"[{i}] {result.reference} score={result.score}\n{text_for_display[:500]}\n")
```

`retrieve` returns an empty list as the second tuple item. Do not treat that placeholder as references or metadata.

## Manual low-token NaiveRAG workflow

Use manual construction when the wrapper's accepted `collection` and `top_k` parameters are misleading for the current implementation.

```python
from deepsearcher.agent import NaiveRAG

rag = NaiveRAG(
    llm=llm,
    embedding_model=embedding_model,
    vector_db=vector_db,
    top_k=4,
    route_collection=False,  # search all known collections from router cache only if router exists
    text_window_splitter=True,
)
answer, refs, tokens = rag.query("Summarize the escalation steps.")
```

If using `route_collection=False`, note that `NaiveRAG.retrieve` expects `self.collection_router.all_collections` in the current implementation even though `collection_router` is only created when `route_collection=True`. For a robust no-routing workflow, instantiate with `route_collection=True` and use collection descriptions that reliably include the desired collections, or patch/set `rag.collection_router` to an object exposing `all_collections` before disabling routing.

## DeepSearch workflow for reports

`DeepSearch` is useful for broad reports over loaded knowledge.

```python
from deepsearcher.agent import DeepSearch

agent = DeepSearch(llm, embedding_model, vector_db, max_iter=2, route_collection=True)
answer, refs, tokens = agent.query("Write a concise report on customer renewal risks.")
```

Operational notes:

- `max_iter` caps reflection rounds. Each round can search multiple sub-queries.
- The first LLM call must return a Python list of sub-queries. If it returns prose, parsing can fail.
- Reranking calls ask the LLM for `YES` or `NO` per retrieved chunk; weak instruction-following models can make this noisy.
- If no retrieved chunks survive, `query` returns `"No relevant information found for query '...'."`, an empty refs list, and retrieval token usage.

## ChainOfRAG workflow for multi-hop questions

```python
from deepsearcher.agent import ChainOfRAG

agent = ChainOfRAG(
    llm=llm,
    embedding_model=embedding_model,
    vector_db=vector_db,
    max_iter=3,
    early_stopping=True,
)
answer, refs, tokens = agent.query("Which approval clause determines the final renewal date?")
```

Operational notes:

- Each iteration asks for one simple follow-up query based on previous intermediate Q/A.
- It retrieves chunks for that follow-up query, writes an intermediate answer, then asks the LLM to select supporting document indices.
- With `early_stopping=True`, an additional yes/no reflection can stop once enough information is available.
- `retrieve` metadata includes `intermediate_context`, which is useful for debugging why the final answer took a path.

## RAGRouter workflow

The global `query` and `retrieve` functions route between `DeepSearch` and `ChainOfRAG`. You can build your own router with `NaiveRAG` included for cost control.

```python
from deepsearcher.agent import DeepSearch, ChainOfRAG, NaiveRAG
from deepsearcher.agent.rag_router import RAGRouter

agents = [
    NaiveRAG(llm, embedding_model, vector_db, top_k=6),
    DeepSearch(llm, embedding_model, vector_db, max_iter=2),
    ChainOfRAG(llm, embedding_model, vector_db, max_iter=3, early_stopping=True),
]
router = RAGRouter(
    llm=llm,
    rag_agents=agents,
    agent_descriptions=[
        "Simple direct Q&A when one retrieval pass is enough and cost matters.",
        "Broad report or survey requiring multiple sub-queries and reflection.",
        "Concrete multi-hop factual question requiring stepwise follow-up evidence.",
    ],
)
answer, refs, tokens = router.query("Compare renewal risk themes across all notes.")
```

Make descriptions mutually exclusive. If two descriptions sound similar, the router can pick the wrong agent even when the underlying agents work.

## Handling no relevant information after loading data

When data is loaded but the answer says no relevant information or refs are empty:

1. Run a retrieval-only call with `max_iter=1` to isolate retrieval from summarization.
2. Inspect vector DB collections and descriptions; CollectionRouter may return no collection or only the default collection.
3. Try a simpler literal query containing exact terms expected in the document.
4. If `DeepSearch` rejects all chunks during reranking, try `NaiveRAG` to see whether raw retrieval was available before reranking.
5. If `NaiveRAG` finds chunks but `DeepSearch` does not, the rerank prompt/model output is the likely issue.
6. If no agent finds chunks, route to `data-ingestion` for collection/chunking checks and to `provider-configuration` for embedding/vector DB dimension checks.

## Token and latency controls

- Lower `max_iter` first. `DeepSearch` and `ChainOfRAG` multiply LLM calls by iterations and retrieved chunks.
- Prefer `NaiveRAG(top_k=3..6)` for exploratory checks.
- Disable or narrow collection routing only when you have verified the manual path; current no-routing behavior has implementation caveats.
- Use `retrieve` before `query` to inspect refs without final answer generation.
- Use `ChainOfRAG(early_stopping=True)` for multi-hop questions where enough evidence may be found before `max_iter`.
- Keep collection descriptions precise to reduce unnecessary searches.

## Notebook async caveat

`DeepSearch.retrieve` wraps `async_retrieve` with `asyncio.run`. In notebooks or existing event loops, this can fail. Apply `nest_asyncio` in notebooks, or call `async_retrieve` from an async context when you own the event loop.
