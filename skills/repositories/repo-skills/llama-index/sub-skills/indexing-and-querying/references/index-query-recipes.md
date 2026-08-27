# Index and Query Recipes

These recipes assume documents or nodes already exist. Loading files, chunking text, and ingestion pipelines are owned by `ingestion-and-loading`.

## Build a Vector Index

Use `VectorStoreIndex` when queries should retrieve semantically similar chunks.

```python
from llama_index.core import Settings, VectorStoreIndex

# Set Settings.embed_model explicitly, or pass embed_model=... below.
index = VectorStoreIndex.from_documents(
    documents,
    show_progress=True,
    insert_batch_size=512,
)
query_engine = index.as_query_engine(similarity_top_k=3)
response = query_engine.query("Summarize the refund policy.")
```

Important details:

- `VectorStoreIndex(...)` accepts nodes; use `VectorStoreIndex.from_documents(...)` for `Document` objects.
- `insert_batch_size` controls embedding/vector-store insert batches.
- `store_nodes_override=True` forces node storage in the docstore/index store even when the vector store claims it stores text.
- `use_async=True` enables async embedding/insertion paths during index construction.

## Build a Summary Index

Use `SummaryIndex` when the corpus is small, ordered, or every node should be considered.

```python
from llama_index.core import SummaryIndex

index = SummaryIndex.from_documents(documents)
query_engine = index.as_query_engine(response_mode="tree_summarize")
response = query_engine.query("Give a high-level summary.")
```

Retriever modes:

- Default mode iterates through stored nodes.
- `retriever_mode="embedding"` uses an embedding model for selection.
- `retriever_mode="llm"` asks an LLM to choose relevant nodes.

## Persist and Reload an Index

```python
from llama_index.core import StorageContext, load_index_from_storage

index = VectorStoreIndex.from_documents(documents)
index.set_index_id("policies-vector")
index.storage_context.persist(persist_dir="./storage/policies")

storage_context = StorageContext.from_defaults(persist_dir="./storage/policies")
reloaded = load_index_from_storage(
    storage_context,
    index_id="policies-vector",
)
```

Rules of thumb:

- Use the same `persist_dir` for reload that was used for `persist`.
- If one storage directory contains multiple indexes, pass `index_id`; otherwise `load_index_from_storage` raises because it cannot choose.
- If loading with an external vector store that persists outside the local storage directory, recreate the same vector store client first, then pass it to `StorageContext.from_defaults(persist_dir=..., vector_store=...)`.
- If the vector store does not store text, keep docstore/index-store persistence alongside the vector store; otherwise retrieval may return ids without reconstructable nodes.

## Separate Retriever and Query Engine

Use this when you need explicit retrieval, node postprocessors, or a custom response synthesizer.

```python
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer

retriever = index.as_retriever(similarity_top_k=5)
synthesizer = get_response_synthesizer(response_mode="compact")
query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=synthesizer,
)
response = query_engine.query("Which documents mention renewals?")
```

Use `response_mode="no_text"` to inspect retrieved source nodes without an LLM-generated answer, or `response_mode="context_only"` to return concatenated retrieved context.

## Use VectorIndexRetriever Directly

```python
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters

filters = MetadataFilters(filters=[
    MetadataFilter(key="category", value="billing"),
])
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=4,
    filters=filters,
    vector_store_query_mode="default",
)
nodes = retriever.retrieve("refund SLA")
```

Common knobs:

- `similarity_top_k`: final number of returned nodes before synthesis.
- `filters`: vector-store metadata filters; key names and operators must match the active vector store.
- `doc_ids` and `node_ids`: constrain search to known ids.
- `vector_store_query_mode`, `alpha`, `sparse_top_k`, and `hybrid_top_k`: use only when the vector store supports the requested mode.
- `vector_store_kwargs`: pass integration-specific query options through to the vector store.

## Fuse Multiple Retrievers

Use `QueryFusionRetriever` when different retrievers should contribute to one ranked set.

```python
from llama_index.core.retrievers import QueryFusionRetriever

fusion = QueryFusionRetriever(
    retrievers=[title_retriever, body_retriever],
    mode="reciprocal_rerank",
    similarity_top_k=6,
    num_queries=1,  # set >1 only when an LLM should generate extra queries
    retriever_weights=[0.35, 0.65],
    use_async=False,
)
query_engine = RetrieverQueryEngine.from_args(
    retriever=fusion,
    response_mode="compact",
)
```

For no-network or deterministic systems, keep `num_queries=1` and pass an explicit local/mock `llm` if query generation is needed. Fusion de-duplicates by node hash, so duplicate content across retrievers collapses into one candidate.

## Route Between Retrievers

Use `RouterRetriever` when the query should select one or more retrievers based on tool metadata.

```python
from llama_index.core.retrievers import RouterRetriever
from llama_index.core.tools import RetrieverTool

retriever_tools = [
    RetrieverTool.from_defaults(
        retriever=policy_retriever,
        name="policy_search",
        description="Search HR and compliance policy chunks.",
    ),
    RetrieverTool.from_defaults(
        retriever=invoice_retriever,
        name="invoice_search",
        description="Search invoice and billing support chunks.",
    ),
]
router = RouterRetriever.from_defaults(
    retriever_tools=retriever_tools,
    select_multi=True,
)
```

Metadata matters. Tool names should be unique, lowercase-ish identifiers; descriptions should state domain, data type, and when not to use the retriever.

## Route Between Query Engines

Use `RouterQueryEngine` when each target has its own query engine and synthesis settings.

```python
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.tools import QueryEngineTool

query_engine_tools = [
    QueryEngineTool.from_defaults(
        query_engine=summary_engine,
        name="summary_engine",
        description="Best for broad summaries over all policy documents.",
    ),
    QueryEngineTool.from_defaults(
        query_engine=vector_engine,
        name="vector_engine",
        description="Best for precise fact lookup in policy chunks.",
    ),
]
router_engine = RouterQueryEngine.from_defaults(
    query_engine_tools=query_engine_tools,
    select_multi=True,
)
```

When `select_multi=True`, selected engine responses are combined with a tree summarizer. Choose an LLM and response mode that can handle the combined context.

## Use Sub-Question Querying

Use `SubQuestionQueryEngine` for compare/contrast or multi-hop questions that should be decomposed across tools.

```python
from llama_index.core.query_engine import SubQuestionQueryEngine

sub_question_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=query_engine_tools,
    use_async=False,
    verbose=True,
)
response = sub_question_engine.query(
    "Compare support response times for enterprise and self-serve customers."
)
```

`from_defaults` may require the optional OpenAI question generator package when it cannot fall back to a compatible generic generator. For provider-neutral setups, construct and pass an explicit `question_gen` and `response_synthesizer`.

## Use Recursive Retrieval

Use `RecursiveRetriever` when retrieved nodes can point to other retrievers or query engines through `IndexNode` ids.

```python
from llama_index.core.retrievers import RecursiveRetriever

recursive = RecursiveRetriever(
    root_id="root",
    retriever_dict={
        "root": root_retriever,
        "policies": policy_retriever,
    },
    query_engine_dict={
        "summaries": summary_query_engine,
    },
    verbose=True,
)
query_engine = RetrieverQueryEngine.from_args(recursive, response_mode="compact")
```

The `root_id` must exist in `retriever_dict`, and ids must not overlap between `retriever_dict` and `query_engine_dict`.

## Choose a Response Mode

Use `get_response_synthesizer(response_mode=...)` or pass `response_mode=...` to `as_query_engine` / `RetrieverQueryEngine.from_args`.

- `compact`: default general-purpose mode; packs chunks before refine to reduce LLM calls.
- `refine`: sequentially refines across nodes; useful when every chunk may matter.
- `tree_summarize`: recursively summarizes; good for summarization and router multi-select combination.
- `simple_summarize`: concatenates all text; fast but can exceed context windows.
- `accumulate` / `compact_accumulate`: answer each chunk and concatenate answers.
- `no_text`: return source nodes without synthesis; best for retrieval debugging.
- `context_only`: return concatenated context only.
- `generation`: ignore retrieved context and use the LLM directly.

## Advanced Persistence with Vector Store Boundaries

When an external vector store owns vectors but not full text, persist local docstore and index store as the boundary record:

```python
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    store_nodes_override=True,
)
index.set_index_id("customer-kb")
storage_context.persist(persist_dir="./storage/customer-kb")

# Later, recreate the same vector_store client/config first.
storage_context = StorageContext.from_defaults(
    persist_dir="./storage/customer-kb",
    vector_store=vector_store,
)
index = load_index_from_storage(storage_context, index_id="customer-kb")
```

Provider-specific vector-store construction, credentials, and package installation are owned by `integrations-and-storage`.
