# Workflows

Use these workflows as implementation recipes. They are intentionally written to avoid requiring source-repo files at runtime.

## Add Chat History Memory To A ChatAgent

1. Choose a token counter and context budget that match the model used by the agent.
2. Create `ScoreBasedContextCreator(token_counter=..., token_limit=...)`.
3. Use `ChatHistoryMemory(context_creator, storage=InMemoryKeyValueStorage())` for tests or `JsonStorage(path)` for local persistence.
4. Pass memory at construction: `ChatAgent(system_message=..., model=..., memory=memory)`, or assign `agent.memory = memory` before stepping.
5. After several turns, validate with `context, token_count = memory.get_context()` and assert the context contains the expected system/user/assistant records.
6. For long tool-heavy conversations, call `memory.clean_tool_calls()` when using `ChatHistoryMemory` to remove tool/function messages from stored context.

### Minimal Pattern

```python
from pathlib import Path
from camel.agents import ChatAgent
from camel.memories import ChatHistoryMemory
from camel.memories.context_creators import ScoreBasedContextCreator
from camel.storages.key_value_storages import JsonStorage
from camel.types import ModelType
from camel.utils import OpenAITokenCounter

context_creator = ScoreBasedContextCreator(
    token_counter=OpenAITokenCounter(ModelType.GPT_4O_MINI),
    token_limit=1024,
)
memory = ChatHistoryMemory(
    context_creator=context_creator,
    storage=JsonStorage(Path("agent-memory.json")),
    window_size=20,
    agent_id="support-agent",
)
agent = ChatAgent(system_message="You are a helpful assistant", memory=memory)
```

## Add Long-Term Semantic Memory

Use `VectorDBMemory` or `LongtermAgentMemory` when later user messages should retrieve semantically similar earlier facts. The important invariant is embedding dimension equality: `embedding.get_output_dim()` must equal the vector store `vector_dim`.

```python
from camel.embeddings import OpenAIEmbedding
from camel.memories import VectorDBMemory
from camel.memories.context_creators import ScoreBasedContextCreator
from camel.storages.vectordb_storages import QdrantStorage
from camel.types import ModelType
from camel.utils import OpenAITokenCounter

embedding = OpenAIEmbedding()
storage = QdrantStorage(
    vector_dim=embedding.get_output_dim(),
    collection_name="agent_memory",
    path="memory-qdrant",  # omit for in-memory, or use remote url_and_api_key
)
context_creator = ScoreBasedContextCreator(
    OpenAITokenCounter(ModelType.GPT_4O_MINI), token_limit=2048
)
memory = VectorDBMemory(
    context_creator=context_creator,
    storage=storage,
    retrieve_limit=5,
    agent_id="agent-1",
)
```

Prefer a combined long-term memory when the agent needs both recency and semantic recall. If implementing a custom mix, keep a `ChatHistoryBlock` for ordered recent context and a `VectorDBBlock` for semantic matches, then feed both through one context creator.

## Build A Vector RAG Pipeline

1. Select an embedding. For CI, prefer a small local/fake embedding class with a deterministic `get_output_dim`; for production, choose a provider or local sentence-transformers model.
2. Create storage using that exact dimension. Use in-memory Qdrant/Chroma or FAISS for tests, local persistent Qdrant/Chroma/FAISS for developer workflows, and remote vector DBs for production.
3. Instantiate `VectorRetriever(embedding_model=embedding, storage=storage)`.
4. Ingest local text/file fixtures using `process(content=..., should_chunk=True, max_characters=...)`. Avoid remote URLs in tests.
5. Query with `query(query, top_k=..., similarity_threshold=...)`; inspect `text`, `metadata`, `content path`, and `extra_info` before passing retrieved context to an agent.
6. Compose an agent prompt that clearly separates original query and retrieved context.

```python
from camel.retrievers import VectorRetriever
from camel.storages.vectordb_storages import QdrantStorage

embedding = MyEmbedding()  # implements BaseEmbedding
storage = QdrantStorage(vector_dim=embedding.get_output_dim())
retriever = VectorRetriever(embedding_model=embedding, storage=storage)
retriever.process(
    content="CAMEL is a multi-agent framework.",
    should_chunk=False,
    extra_info={"source": "ci-fixture"},
)
results = retriever.query("What is CAMEL?", top_k=1, similarity_threshold=0.0)
context = "\n\n".join(item["text"] for item in results)
```

## Swap CI In-Memory Storage For Production Qdrant

Use a factory that receives the embedding instance and environment-specific settings. Never hard-code dimensions independently.

```python
from camel.storages.vectordb_storages import QdrantStorage


def make_vector_storage(embedding, env, collection_name):
    vector_dim = embedding.get_output_dim()
    if env == "ci":
        return QdrantStorage(vector_dim=vector_dim, collection_name=collection_name)
    if env == "local":
        return QdrantStorage(
            vector_dim=vector_dim,
            collection_name=collection_name,
            path="rag-qdrant",
        )
    if env == "prod":
        import os

        return QdrantStorage(
            vector_dim=vector_dim,
            collection_name=collection_name,
            url_and_api_key=(os.environ["QDRANT_URL"], os.environ["QDRANT_API_KEY"]),
        )
    raise ValueError(f"Unsupported env: {env}")
```

Validation steps for this pattern:

- Assert `storage.status().vector_dim == embedding.get_output_dim()` after initialization when the backend reports status.
- Use a collection name that encodes the embedding family or dimension, such as `docs_text_embedding_3_small_1536`.
- On migrations, create a new collection and re-embed; do not reuse an existing collection with a different vector dimension.

## Build Hybrid Retrieval

Use `HybridRetriever` when vector search misses exact terms or when BM25 exact matches are important. It internally uses `VectorRetriever` plus `BM25Retriever` and combines results with reciprocal rank fusion.

```python
from camel.retrievers import HybridRetriever

retriever = HybridRetriever(embedding_model=embedding, vector_storage=storage)
retriever.process(content_input_path="local-doc.md")
results = retriever.query(
    query="installation extras for qdrant",
    top_k=5,
    vector_retriever_top_k=20,
    bm25_retriever_top_k=20,
    vector_weight=0.7,
    bm25_weight=0.3,
)
```

If `top_k` is larger than both internal retriever top-k values, CAMEL raises a `ValueError`. Keep weights non-negative.

## Use AutoRetriever For Fast Experiments

`AutoRetriever` is useful for notebooks and prototypes because it initializes vector storage per content and query. It is less explicit than `VectorRetriever`, so production code should usually construct storage and embeddings directly.

```python
from camel.retrievers import AutoRetriever
from camel.types import StorageType

retriever = AutoRetriever(
    vector_storage_local_path="retriever-store",
    storage_type=StorageType.QDRANT,
    embedding_model=embedding,
)
result = retriever.run_vector_retriever(
    query="What does the document say about memory?",
    contents=["local-doc.md"],
    return_detailed_info=True,
    max_characters=800,
)
```

## Validate RAG Data Before Agent Use

Before sending retrieved text into a `ChatAgent`, check:

- `results` is non-empty and every item has non-empty `text`.
- Metadata includes a source identifier, filename, URL, or fixture name.
- Similarity thresholds are tuned for the embedding/storage pair.
- Chunk size is neither so small that context loses meaning nor so large that retrieval returns irrelevant text.
- Retrieved text is deduplicated before prompt construction if using hybrid retrieval.

## Evidence Coverage

The recipes above distill CAMEL's memory attachment, persisted chat memory, semantic memory, hybrid RAG, vector retriever, and vector-storage test patterns into self-contained guidance. They do not require access to the original repository examples or tests at runtime.
