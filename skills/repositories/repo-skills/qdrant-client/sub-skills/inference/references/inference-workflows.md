# Inference Workflows

This reference covers qdrant-client inference workflows in version 1.18.0. Inference means passing `qdrant_client.models.Document`, `models.Image`, or `models.InferenceObject` where a vector is normally accepted, so the client or Qdrant Cloud turns raw text or image data into vectors.

## Choose Local or Remote Inference

| Mode | Client setup | Dependencies | Where embedding happens | Best for |
| --- | --- | --- | --- | --- |
| Local FastEmbed | `QdrantClient(":memory:")`, `QdrantClient(path=...)`, or a remote client with default `cloud_inference=False` | `qdrant-client[fastembed]` or `qdrant-client[fastembed-gpu]` | Inside the Python process using FastEmbed | Local prototypes, offline tests, self-hosted servers |
| Qdrant Cloud remote inference | Remote Cloud `QdrantClient(..., cloud_inference=True)` | No local FastEmbed required for embedding calls | Qdrant Cloud inference service | Cloud deployments on plans that support inference |

Local mode rejects `cloud_inference=True`; use FastEmbed locally or connect to a Cloud cluster. Remote inference still needs normal Cloud connection details such as `url` and `api_key`; route connection setup to `connection-and-transport`.

## Local FastEmbed Setup

Install one optional extra, not both:

```bash
pip install "qdrant-client[fastembed]"
```

For GPU-backed FastEmbed, install the GPU extra in a clean environment instead:

```bash
pip install "qdrant-client[fastembed-gpu]"
```

`fastembed` and `fastembed-gpu` are mutually exclusive package choices. If CPU FastEmbed was already installed, use a fresh environment before installing the GPU extra.

Local inference behavior:

- `QdrantClient` checks whether FastEmbed is installed and stores the result in `_FASTEMBED_INSTALLED`.
- If a regular method sees `models.Document`, `models.Image`, or `models.InferenceObject` and `cloud_inference=False`, it embeds locally before sending the request.
- Local inference can download model weights when the first embedding call initializes a model. Ask before running examples that actually embed data.
- `local_inference_batch_size` on the client constructor controls the batch size for regular-method inference object embedding.
- `options` on `models.Document` or `models.Image` are passed to the selected model. Examples include `{"cuda": True}`, `{"providers": [...]}`, `{"cache_dir": "..."}`, and provider/model-specific options.

## Dense Text with Regular Methods

Use regular Qdrant methods and wrap text as `models.Document` where a vector or query vector would normally go.

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
model_name = "sentence-transformers/all-MiniLM-L6-v2"

client.create_collection(
    collection_name="docs",
    vectors_config=models.VectorParams(
        size=client.get_embedding_size(model_name),
        distance=models.Distance.COSINE,
    ),
)

client.upsert(
    collection_name="docs",
    points=[
        models.PointStruct(
            id=1,
            vector=models.Document(text="Qdrant supports FastEmbed", model=model_name),
            payload={"kind": "doc"},
        )
    ],
)

hits = client.query_points(
    collection_name="docs",
    query=models.Document(text="embedding search", model=model_name),
    limit=5,
).points
```

The same inference object can also appear inside `models.NearestQuery`, `models.RecommendQuery`, `models.DiscoverQuery`, `models.ContextQuery`, `models.Prefetch`, `models.QueryRequest`, `models.PointStruct`, `models.PointVectors`, `models.Batch`, and update-operation models. The schema inspector finds these nested fields and replaces only the inference objects with vectors.

## Named Dense, Sparse, Image, and Multivector Inputs

When a collection has multiple vector fields, use a vector dictionary and put the inference object under the field that matches the model family.

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
text_model = "sentence-transformers/all-MiniLM-L6-v2"
sparse_model = "Qdrant/bm25"
image_model = "Qdrant/resnet50-onnx"

client.create_collection(
    "multi_input",
    vectors_config={
        "text": models.VectorParams(
            size=client.get_embedding_size(text_model),
            distance=models.Distance.COSINE,
        ),
        "image": models.VectorParams(
            size=client.get_embedding_size(image_model),
            distance=models.Distance.COSINE,
        ),
    },
    sparse_vectors_config={
        "sparse-text": models.SparseVectorParams(modifier=models.Modifier.IDF),
    },
)

client.upsert(
    "multi_input",
    points=[
        models.PointStruct(
            id=1,
            vector={
                "text": models.Document(text="text to embed", model=text_model),
                "sparse-text": models.Document(text="text to index sparsely", model=sparse_model),
                "image": models.Image(image="https://example.com/image.png", model=image_model),
            },
        )
    ],
)
```

For local image inference, FastEmbed image models may accept image input types supported by FastEmbed. For Cloud inference, images must be URLs or base64-encoded strings.

## Hybrid Dense and Sparse Search

Hybrid search usually stores dense and sparse vectors in separate named vector fields, runs dense and sparse prefetches, then fuses the results.

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
dense_model = "sentence-transformers/all-MiniLM-L6-v2"
sparse_model = "Qdrant/bm25"

client.create_collection(
    "hybrid_docs",
    vectors_config={
        "dense": models.VectorParams(
            size=client.get_embedding_size(dense_model),
            distance=models.Distance.COSINE,
        )
    },
    sparse_vectors_config={
        "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF),
    },
)

client.upsert(
    "hybrid_docs",
    points=[
        models.PointStruct(
            id=1,
            vector={
                "dense": models.Document(text="neural search", model=dense_model),
                "sparse": models.Document(text="keyword scoring", model=sparse_model),
            },
        )
    ],
)

hits = client.query_points(
    "hybrid_docs",
    prefetch=[
        models.Prefetch(
            query=models.Document(text="semantic keywords", model=dense_model),
            using="dense",
            limit=20,
        ),
        models.Prefetch(
            query=models.Document(text="semantic keywords", model=sparse_model),
            using="sparse",
            limit=20,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=5,
).points
```

If the sparse model is IDF-based, configure `models.SparseVectorParams(modifier=models.Modifier.IDF)`. The deprecated `set_sparse_model()` and `get_fastembed_sparse_vector_params()` helpers apply `IDF` automatically for qdrant-client's known IDF sparse models.

## Helper-Driven Dense and Sparse Collection Config

The deprecated helper workflow keeps default vector names derived from the current FastEmbed model names:

```python
from qdrant_client import QdrantClient

client = QdrantClient(":memory:")
client.set_model("sentence-transformers/all-MiniLM-L6-v2")
client.set_sparse_model("Qdrant/bm25")
client.create_collection(
    "helper_configured",
    vectors_config=client.get_fastembed_vector_params(),
    sparse_vectors_config=client.get_fastembed_sparse_vector_params(),
)
```

Helper naming rules:

- Dense vector field: `fast-` plus the final model path segment lowercased, such as `fast-all-minilm-l6-v2`.
- Sparse vector field: `fast-sparse-` plus the final sparse model path segment lowercased, such as `fast-sparse-bm25`.
- `get_fastembed_vector_params()` returns `{field_name: models.VectorParams(...)}` for the current dense model.
- `get_fastembed_sparse_vector_params()` returns `{field_name: models.SparseVectorParams(...)}` or `None` when no sparse model is set.

Prefer explicit named vector fields in new code when you need stable schema names across model changes.

## Remote Qdrant Cloud Inference

Remote inference uses the same request models but sends inference objects to Qdrant Cloud instead of embedding locally.

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(
    url="https://example-cluster.region.cloud.qdrant.io:6333",
    api_key="<qdrant-api-key>",
    cloud_inference=True,
)

client.upsert(
    "cloud_docs",
    points=[
        models.PointStruct(
            id=1,
            vector=models.Document(
                text="Qdrant Cloud performs the embedding",
                model="sentence-transformers/all-MiniLM-L6-v2",
            ),
        )
    ],
)
```

Important Cloud inference constraints:

- The Cloud cluster and plan must support inference.
- The model name must be available in the Cloud inference provider, which can differ from local FastEmbed catalogs.
- Local FastEmbed is not required for remote inference, but `get_embedding_size()` is local FastEmbed catalog based. For Cloud-only workflows, get dimensions from the Cloud model/provider metadata or use known dimensions from the chosen Cloud model.
- Remote image inference requires `models.Image(image=...)` to contain a URL or base64-encoded string.
- Do not pass local file paths as Cloud image input; encode the file to base64 first or host it at a URL.

## `Document`, `Image`, and `InferenceObject`

`models.Document` is for text:

```python
models.Document(
    text="text to embed",
    model="sentence-transformers/all-MiniLM-L6-v2",
    options={"cuda": True},
)
```

`models.Image` is for image data:

```python
models.Image(
    image="https://example.com/image.png",
    model="Qdrant/resnet50-onnx",
)
```

`models.InferenceObject` is a generic object wrapper:

```python
models.InferenceObject(
    object="text or provider-specific object",
    model="sentence-transformers/all-MiniLM-L6-v2",
    options={"cache_dir": "fastembed_cache"},
)
```

For local inference, `InferenceObject` resolves to `Document` for supported text, sparse, and late-interaction text models, to `Image` for supported image models, and raises for late-interaction multimodal models that do not support the generic interface.

## Deprecated `add`, `query`, and `query_batch`

`QdrantClient.add()`, `QdrantClient.query()`, and `QdrantClient.query_batch()` are deprecated compatibility helpers. They initialize FastEmbed directly, create or validate helper-named collections, and return legacy `QueryResponse` objects. Use regular methods with inference objects instead.

| Deprecated helper | Prefer this |
| --- | --- |
| `client.add(collection_name, documents=..., metadata=..., ids=...)` | `client.upsert()` or `client.upload_collection()` with `models.Document` vectors |
| `client.query(collection_name, query_text=...)` | `client.query_points(query=models.Document(...))` |
| `client.query_batch(collection_name, query_texts=[...])` | `client.query_batch_points()` with `models.QueryRequest(query=models.Document(...))` |

Legacy helper caveats:

- `add()` creates a collection if missing using `get_fastembed_vector_params()` and optionally `get_fastembed_sparse_vector_params()`.
- `query()` embeds the query text; when a sparse model is set, it runs dense and sparse requests and fuses them with reciprocal rank fusion.
- `query_batch()` batches dense requests and, when sparse is set, appends sparse requests and fuses paired dense/sparse results.
- Helper collection validation asserts matching vector names, dense size, distance, and IDF modifier for known IDF sparse models.
- Deprecation warnings may mention removal in older version wording; treat the methods as legacy even if still present.

## No-Download Inspection

To inspect optional dependency state without embedding data or downloading model weights, run:

```bash
python sub-skills/inference/scripts/check_inference_optional_deps.py
```

The script imports qdrant-client, checks package metadata, tries importing FastEmbed, and lists model catalog names/counts if the FastEmbed catalog APIs are available. It does not instantiate embedding models or call `embed`, `query_embed`, or `passage_embed`.
