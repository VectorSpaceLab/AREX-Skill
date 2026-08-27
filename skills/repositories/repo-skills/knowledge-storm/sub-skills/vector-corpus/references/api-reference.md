# Vector corpus API reference

Use these APIs after installing the public `knowledge-storm` package. Examples use the current `LitellmModel` wrapper; avoid legacy provider-specific OpenAI/Azure wrappers for new scripts.

## `VectorRM`

Import:

```python
from knowledge_storm.rm import VectorRM
```

Constructor:

```python
VectorRM(
    collection_name: str,
    embedding_model: str,
    device: str = "mps",
    k: int = 3,
)
```

Behavior:

- Creates a Hugging Face embedding model immediately with `model_kwargs={"device": device}` and `encode_kwargs={"normalize_embeddings": True}`.
- Requires a non-empty `collection_name`; otherwise raises `ValueError("Please provide a collection name.")`.
- Requires a non-empty `embedding_model`; otherwise raises `ValueError("Please provide an embedding model.")`.
- Does not connect to Qdrant until `init_offline_vector_db(...)` or `init_online_vector_db(...)` is called.
- `k` controls how many vector chunks are retrieved per query.

Device choices:

| Device | Use when | Notes |
| --- | --- | --- |
| `cpu` | Safe default and functional baseline. | Slower, but works without accelerator hardware. |
| `cuda` | CUDA GPU is available and torch/sentence-transformers can use it. | Acceleration only; not required for correctness. |
| `mps` | Apple Silicon with PyTorch MPS support. | Package default, but unsuitable on most Linux hosts. |

### `init_offline_vector_db`

```python
rm.init_offline_vector_db(vector_store_path: str)
```

Behavior:

- Opens a local Qdrant client with `QdrantClient(path=vector_store_path)`.
- Requires `vector_store_path`; if `None`, raises `ValueError("Please provide a folder path.")`.
- Loads an existing collection with the same `collection_name`.
- If the collection does not exist, raises `ValueError("Collection <name> does not exist. Please create the collection first.")`.
- Wraps client/path failures as `ValueError("Error occurs when loading the vector store: ...")`.

### `init_online_vector_db`

```python
rm.init_online_vector_db(url: str, api_key: str)
```

Behavior:

- Opens a remote Qdrant client with `QdrantClient(url=url, api_key=api_key)`.
- If `api_key` is `None`, reads `QDRANT_API_KEY` from the environment.
- If no key is available, raises `ValueError("Please provide an api key.")`.
- If `url` is `None`, raises `ValueError("Please provide a url for the Qdrant server.")`.
- Loads an existing collection with the same `collection_name`.
- If the collection does not exist, raises `ValueError("Collection <name> does not exist. Please create the collection first.")`.
- Wraps connection failures as `ValueError("Error occurs when connecting to the server: ...")`.

### `get_vector_count`

```python
count_result = rm.get_vector_count()
```

Behavior:

- Calls Qdrant `count(collection_name=rm.collection_name)` through the initialized client.
- Requires `rm.qdrant` to be initialized first.
- Depending on the Qdrant client version, the returned value may be a count object with a `.count` field rather than a bare integer:

```python
count_result = rm.get_vector_count()
vector_count = getattr(count_result, "count", count_result)
print(vector_count)
```

### `forward`

```python
results = rm.forward(query_or_queries, exclude_urls)
```

Signature:

```python
forward(query_or_queries: str | list[str], exclude_urls: list[str])
```

Behavior:

- Accepts one query string or a list of query strings.
- `exclude_urls` is present for STORM retriever interface compatibility; current `VectorRM` does not use it for filtering.
- Increments internal usage by the number of queries.
- For each query, runs Qdrant similarity search with `k=rm.k`.
- Returns a flat list of dictionaries shaped for STORM:

```python
{
    "description": "...",
    "snippets": ["retrieved chunk text"],
    "title": "...",
    "url": "doc-001",
}
```

## `QdrantVectorStoreManager`

Import:

```python
from knowledge_storm.utils import QdrantVectorStoreManager
```

Static method signature:

```python
QdrantVectorStoreManager.create_or_update_vector_store(
    collection_name: str,
    vector_db_mode: str,
    file_path: str,
    content_column: str,
    title_column: str = "title",
    url_column: str = "url",
    desc_column: str = "description",
    batch_size: int = 64,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    vector_store_path: str = None,
    url: str = None,
    qdrant_api_key: str = None,
    embedding_model: str = "BAAI/bge-m3",
    device: str = "mps",
)
```

Important keyword: use `qdrant_api_key=...`, not `api_key=...`, when calling `create_or_update_vector_store` directly.

Behavior:

1. Validates `collection_name`, `file_path`, `content_column`, and `url_column` are provided.
2. Rejects non-CSV paths with `ValueError("Not valid file format. Please provide a csv file.")`.
3. Creates a Hugging Face embedding model with normalized embeddings.
4. Initializes Qdrant according to `vector_db_mode`:
   - `offline`: uses `vector_store_path` and creates/loads a local collection.
   - `online`: uses `url` and `qdrant_api_key`; if `qdrant_api_key` is `None`, reads `QDRANT_API_KEY`.
5. Creates the collection if missing; loads it if present.
6. Reads the CSV, checks that `content_column` and `url_column` exist, and builds one document per row with metadata `title`, `url`, and `description`.
7. Splits row content into chunks with `chunk_size` and `chunk_overlap`.
8. Adds chunked documents to Qdrant in batches of `batch_size`.
9. Closes the Qdrant client.

Collection creation caveat:

- The built-in collection creator uses cosine distance and a hard-coded vector size of `1024`, which matches the default `BAAI/bge-m3` embedding model.
- If you choose a different embedding model, verify its embedding dimension. A dimension mismatch can surface as Qdrant vector-size errors during `add_documents` or retrieval.

Offline creation example:

```python
QdrantVectorStoreManager.create_or_update_vector_store(
    collection_name="my_documents",
    vector_db_mode="offline",
    file_path="corpus.csv",
    content_column="content",
    title_column="title",
    url_column="url",
    desc_column="description",
    vector_store_path="./vector_store",
    embedding_model="BAAI/bge-m3",
    device="cpu",
    batch_size=64,
    chunk_size=500,
    chunk_overlap=100,
)
```

Online creation example:

```python
QdrantVectorStoreManager.create_or_update_vector_store(
    collection_name="my_documents",
    vector_db_mode="online",
    file_path="corpus.csv",
    content_column="content",
    url_column="url",
    url="https://YOUR-QDRANT-ENDPOINT",
    qdrant_api_key=None,  # read QDRANT_API_KEY from environment
    embedding_model="BAAI/bge-m3",
    device="cpu",
)
```

## STORM runner integration

`STORMWikiRunner` accepts `rm` as its retriever dependency:

```python
runner = STORMWikiRunner(engine_args, engine_lm_configs, rm)
```

For corpus-grounded runs:

1. Create/update a Qdrant collection with `QdrantVectorStoreManager.create_or_update_vector_store(...)`, unless the collection already exists.
2. Instantiate `VectorRM(collection_name=..., embedding_model=..., device=..., k=engine_args.search_top_k)`.
3. Initialize it with either `init_offline_vector_db(...)` or `init_online_vector_db(...)`.
4. Pass `rm` to `STORMWikiRunner`.
5. Call `runner.run(...)`, then `runner.post_run()` and `runner.summary()`.

## Current model wrapper: `LitellmModel`

Import:

```python
from knowledge_storm.lm import LitellmModel
```

Typical constructor:

```python
LitellmModel(
    model="openai/gpt-4o-mini",
    api_key=None,
    model_type="chat",
    max_tokens=500,
    temperature=1.0,
    top_p=0.9,
)
```

Use LiteLLM provider model names such as `openai/gpt-4o-mini`, `openai/gpt-4o`, or provider-specific names supported by LiteLLM. Provider credentials are usually read from environment variables such as `OPENAI_API_KEY` unless you pass `api_key` explicitly.
