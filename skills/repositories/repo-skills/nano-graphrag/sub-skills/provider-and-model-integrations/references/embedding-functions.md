# Embedding function contract

Nano-graphrag treats embeddings as an `EmbeddingFunc` object: an async callable plus two required attributes, `embedding_dim` and `max_token_size`. The easiest way to create one is `wrap_embedding_func_with_attrs`.

## Minimal correct shape

```python
import numpy as np
from nano_graphrag._utils import wrap_embedding_func_with_attrs

@wrap_embedding_func_with_attrs(embedding_dim=384, max_token_size=512)
async def my_embedding(texts: list[str]) -> np.ndarray:
    vectors = ...  # produce one vector per input string
    return np.asarray(vectors, dtype=np.float32)
```

Required behavior:

- Input is a `list[str]`; handle both many texts and a single-item list such as `[query]`.
- Return a `numpy.ndarray`, not a Python list.
- Return shape must be exactly `(len(texts), embedding_dim)`.
- Row order must match input order.
- Values should be finite floats; avoid `NaN`, `inf`, empty vectors, ragged arrays, or object dtype arrays.
- `embedding_dim` must match the real vector length returned by the function.
- `max_token_size` should reflect the embedding model's practical input limit; nano-graphrag does not automatically re-tokenize every embedding input to this exact model tokenizer.

## What `wrap_embedding_func_with_attrs` creates

`wrap_embedding_func_with_attrs(embedding_dim=..., max_token_size=...)` returns an `EmbeddingFunc` dataclass instance with:

- `embedding_dim`: used by vector stores when creating indexes.
- `max_token_size`: used as metadata for operating limits and compatibility checks.
- `func`: the wrapped async implementation.
- async `__call__(*args, **kwargs)`: delegates to `func` and returns the embedding array.

This means the decorated name is no longer a plain function; it is a callable object with attributes. Pass that object directly to `GraphRAG(embedding_func=...)`.

## Interaction with vector stores

Built-in vector stores depend on the wrapper attributes:

- NanoVectorDB storage creates a vector database with `embedding_func.embedding_dim`.
- HNSW storage creates an HNSW index with `dim=embedding_func.embedding_dim`.
- Query paths call `embedding_func([query])` and then use `embedding[0]`.
- Upsert paths batch document/entity texts using `embedding_batch_num`, call `embedding_func(batch)` for each batch, and concatenate the returned arrays.

Consequences:

- If you change embedding providers or dimensions, use a new `working_dir` or rebuild/delete old vector index files. Reusing an index created with a different dimension will fail or produce invalid search behavior.
- If `embedding_func([query])` returns a 1D array, query will use the first scalar or vector incorrectly. Always return 2D arrays.
- If your embedding function returns list objects, `np.concatenate` may still appear to work in some upsert paths, but the documented contract is a `numpy.ndarray`; use `np.asarray(..., dtype=np.float32)` explicitly.

## Normalization and similarity

Nano-graphrag's built-in vector retrieval uses cosine-oriented storage/search behavior. Good defaults:

- For sentence-transformers, use `normalize_embeddings=True` unless the selected vector store or model documentation says otherwise.
- Avoid all-zero vectors; cosine similarity becomes meaningless.
- Keep the same normalization policy for indexing and querying.
- If a hosted embedding API already returns normalized vectors, do not normalize twice unless the provider recommends it.

## Batching behavior

`embedding_batch_num` controls how many texts are passed to `embedding_func` per vector-store batch. Choose it by provider type:

- Hosted APIs: use the provider's batch limits and rate limits; start smaller if timeouts or 429s appear.
- CPU local models: smaller batches can reduce memory spikes, but too-small batches waste overhead.
- GPU local models: tune batch size to GPU memory and model size.
- Ollama embedding endpoints: examples often loop one text at a time because the service call accepts a single prompt; wrap the collected results into a 2D `np.ndarray` before returning.

The embedding function should be idempotent for the same input texts. Nano-graphrag does not provide a built-in embedding cache; LLM cache handling is separate.

## Local sentence-transformer pattern

```python
import numpy as np
from sentence_transformers import SentenceTransformer
from nano_graphrag._utils import wrap_embedding_func_with_attrs

_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

@wrap_embedding_func_with_attrs(
    embedding_dim=_model.get_sentence_embedding_dimension(),
    max_token_size=_model.max_seq_length,
)
async def local_embedding(texts: list[str]) -> np.ndarray:
    vectors = _model.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)
```

For production use, pin the model name, device, cache location, and dependency versions in the user's project environment. Model downloads are not part of the safe default skill workflow.

## Hosted embedding pattern

```python
import os
import numpy as np
from openai import OpenAI
from nano_graphrag._utils import wrap_embedding_func_with_attrs

@wrap_embedding_func_with_attrs(embedding_dim=1024, max_token_size=8192)
async def hosted_embedding(texts: list[str]) -> np.ndarray:
    client = OpenAI(
        api_key=os.environ["NANO_GRAPHRAG_EMBED_API_KEY"],
        base_url=os.environ["NANO_GRAPHRAG_EMBED_BASE_URL"],
    )
    response = client.embeddings.create(model="your-embedding-model", input=texts)
    return np.asarray([row.embedding for row in response.data], dtype=np.float32)
```

Even when the provider client is synchronous, the wrapper function itself must be `async` because nano-graphrag awaits `embedding_func(...)`.

## Quick validation checklist

Before using a custom embedding with real indexing:

```python
vectors = await my_embedding(["alpha", "beta"])
assert isinstance(vectors, np.ndarray)
assert vectors.shape == (2, my_embedding.embedding_dim)
assert np.isfinite(vectors).all()
```

You can also run the bundled provider template script to inspect attributes and, when explicitly requested, call a local embedding function with sample texts.
