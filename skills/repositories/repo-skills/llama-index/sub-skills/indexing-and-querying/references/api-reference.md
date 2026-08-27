# Indexing and Querying API Reference

This reference records the core import paths and signatures verified from the installed package and source tree.

## Indexes

### `VectorStoreIndex`

Import:

```python
from llama_index.core import VectorStoreIndex
# or
from llama_index.core.indices.vector_store import VectorStoreIndex
```

Verified constructor shape:

```python
VectorStoreIndex(
    nodes=None,
    use_async=False,
    store_nodes_override=False,
    embed_model=None,
    insert_batch_size=2048,
    objects=None,
    index_struct=None,
    storage_context=None,
    callback_manager=None,
    transformations=None,
    show_progress=False,
    **kwargs,
)
```

High-value methods:

- `VectorStoreIndex.from_documents(documents, storage_context=None, transformations=None, show_progress=False, **kwargs)` transforms `Document` objects into nodes, then builds the index.
- `VectorStoreIndex.from_vector_store(vector_store, embed_model=None, **kwargs)` creates an index over a vector store only when `vector_store.stores_text` is true.
- `index.as_retriever(**kwargs)` returns a `VectorIndexRetriever`.
- `index.as_query_engine(**kwargs)` creates a retriever-backed query engine.
- `index.insert_nodes(nodes, **insert_kwargs)` inserts additional nodes.
- `index.set_index_id(index_id)` updates the persisted index id; persist after setting when reload needs a stable id.

### `SummaryIndex`

Import:

```python
from llama_index.core import SummaryIndex
# or
from llama_index.core.indices.list import SummaryIndex
```

Constructor shape:

```python
SummaryIndex(
    nodes=None,
    objects=None,
    index_struct=None,
    show_progress=False,
    **kwargs,
)
```

Retriever modes:

```python
index.as_retriever(retriever_mode="default")
index.as_retriever(retriever_mode="embedding", embed_model=embed_model)
index.as_retriever(retriever_mode="llm", llm=llm)
```

Aliases retained by the package include `ListIndex` and `GPTListIndex`.

## Storage and Loading

Imports:

```python
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.indices.loading import load_indices_from_storage
```

`StorageContext.from_defaults(...)` accepts:

```python
docstore=None
index_store=None
vector_store=None
image_store=None
vector_stores=None
graph_store=None
property_graph_store=None
persist_dir=None
fs=None
```

`StorageContext.persist(...)` accepts a `persist_dir` plus optional file-name overrides for docstore, index store, vector store, image store, graph store, and property graph store.

`load_index_from_storage(storage_context, index_id=None, **kwargs)` behavior:

- Loads the only index in the index store when `index_id` is omitted.
- Raises if no index is present.
- Raises if multiple indexes are present and `index_id` is omitted.
- Passes `**kwargs` to the index constructor during reconstruction.

`load_indices_from_storage(storage_context, index_ids=None, **kwargs)` loads all indexes when `index_ids` is omitted or the specified ids when provided.

## Retrievers

### `VectorIndexRetriever`

Import:

```python
from llama_index.core.indices.vector_store import VectorIndexRetriever
```

Constructor shape:

```python
VectorIndexRetriever(
    index,
    similarity_top_k=DEFAULT_SIMILARITY_TOP_K,
    vector_store_query_mode="default",
    filters=None,
    alpha=None,
    node_ids=None,
    doc_ids=None,
    sparse_top_k=None,
    hybrid_top_k=None,
    callback_manager=None,
    object_map=None,
    embed_model=None,
    verbose=False,
    **kwargs,
)
```

Pass vector-store-specific query options as `vector_store_kwargs={...}`.

### `QueryFusionRetriever`

Import:

```python
from llama_index.core.retrievers import QueryFusionRetriever
```

Constructor shape:

```python
QueryFusionRetriever(
    retrievers,
    llm=None,
    query_gen_prompt=None,
    mode="simple",
    similarity_top_k=DEFAULT_SIMILARITY_TOP_K,
    num_queries=4,
    use_async=True,
    verbose=False,
    callback_manager=None,
    objects=None,
    object_map=None,
    retriever_weights=None,
)
```

Known modes are `simple`, `reciprocal_rerank`, `relative_score`, and `dist_based_score`. If `num_queries > 1`, an LLM generates additional query variants.

### `RouterRetriever`

Import:

```python
from llama_index.core.retrievers import RouterRetriever
from llama_index.core.tools import RetrieverTool
```

Constructor shape:

```python
RouterRetriever(
    selector,
    retriever_tools,
    llm=None,
    objects=None,
    object_map=None,
    verbose=False,
)
```

Factory:

```python
RouterRetriever.from_defaults(
    retriever_tools,
    llm=None,
    selector=None,
    select_multi=False,
)
```

Candidate retrievers must be wrapped as `RetrieverTool` objects so selectors can inspect metadata.

### `RecursiveRetriever`

Import:

```python
from llama_index.core.retrievers import RecursiveRetriever
```

Constructor shape:

```python
RecursiveRetriever(
    root_id,
    retriever_dict,
    query_engine_dict=None,
    node_dict=None,
    callback_manager=None,
    query_response_tmpl=None,
    verbose=False,
)
```

`root_id` must be a key in `retriever_dict`. Keys must not overlap between `retriever_dict` and `query_engine_dict`.

## Query Engines

### `RetrieverQueryEngine`

Import:

```python
from llama_index.core.query_engine import RetrieverQueryEngine
```

Constructor shape:

```python
RetrieverQueryEngine(
    retriever,
    response_synthesizer=None,
    node_postprocessors=None,
    callback_manager=None,
)
```

Factory:

```python
RetrieverQueryEngine.from_args(
    retriever,
    llm=None,
    response_synthesizer=None,
    node_postprocessors=None,
    callback_manager=None,
    response_mode="compact",
    text_qa_template=None,
    refine_template=None,
    summary_template=None,
    simple_template=None,
    chat_content_qa_template=None,
    chat_content_refine_template=None,
    output_cls=None,
    use_async=False,
    streaming=False,
    verbose=False,
    multimodal=False,
    **kwargs,
)
```

Useful methods include `retrieve(query_bundle_or_str)`, `query(...)`, `aquery(...)`, `synthesize(...)`, and `with_retriever(retriever)`.

### `RouterQueryEngine`

Import:

```python
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.tools import QueryEngineTool
```

Constructor shape:

```python
RouterQueryEngine(
    selector,
    query_engine_tools,
    llm=None,
    summarizer=None,
    verbose=False,
)
```

Factory:

```python
RouterQueryEngine.from_defaults(
    query_engine_tools,
    llm=None,
    selector=None,
    summarizer=None,
    select_multi=False,
    **kwargs,
)
```

Selected result metadata is stored under `response.metadata["selector_result"]`.

### `SubQuestionQueryEngine`

Import:

```python
from llama_index.core.query_engine import SubQuestionQueryEngine
```

Constructor shape:

```python
SubQuestionQueryEngine(
    question_gen,
    response_synthesizer,
    query_engine_tools,
    callback_manager=None,
    verbose=True,
    use_async=False,
)
```

Factory:

```python
SubQuestionQueryEngine.from_defaults(
    query_engine_tools,
    llm=None,
    question_gen=None,
    response_synthesizer=None,
    verbose=True,
    use_async=True,
)
```

`from_defaults` can try to import the OpenAI question-generator package before falling back. For portable skills and tests, pass an explicit `question_gen` when possible.

## Response Synthesizers

Import:

```python
from llama_index.core.response_synthesizers import ResponseMode, get_response_synthesizer
```

Factory shape:

```python
get_response_synthesizer(
    llm=None,
    prompt_helper=None,
    chat_prompt_helper=None,
    text_qa_template=None,
    refine_template=None,
    summary_template=None,
    simple_template=None,
    chat_content_qa_template=None,
    chat_content_refine_template=None,
    chat_summary_template=None,
    response_mode="compact",
    callback_manager=None,
    use_async=False,
    streaming=False,
    structured_answer_filtering=False,
    output_cls=None,
    program_factory=None,
    verbose=False,
    multimodal=False,
)
```

Response modes:

- `refine`
- `compact`
- `simple_summarize`
- `tree_summarize`
- `generation`
- `no_text`
- `context_only`
- `accumulate`
- `compact_accumulate`

## Global Settings Relevant to This Sub-Skill

`Settings` exposes global defaults used when constructors do not receive explicit components:

- `Settings.llm`
- `Settings.embed_model`
- `Settings.node_parser` / `Settings.text_splitter`
- `Settings.transformations`
- `Settings.callback_manager`
- `Settings.tokenizer`
- `Settings.chunk_size` and `Settings.chunk_overlap`

Set `Settings.llm` and `Settings.embed_model` deliberately in offline tests or credential-free scripts.
