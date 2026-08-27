# RAG Workflows

## End-To-End Pattern

Feast RAG workflows usually follow this path:

1. Load documents or document metadata into a DataFrame.
2. Chunk long documents into passages.
3. Embed each passage into a fixed-length vector.
4. Store `passage_id`, text/context fields, embeddings, and `event_timestamp` in a Feast feature view.
5. Apply the feature repo and write rows to the online vector store.
6. Embed the user query and call `retrieve_online_documents_v2(...)`.
7. Format returned context rows into an LLM prompt.

Keep server endpoint setup separate; route remote serving/MCP questions to `../../servers-and-remote/SKILL.md`.

## Manual RAG Skeleton

Feature definition:

```python
from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource, ValueType
from feast.types import Array, Float32, String

passage = Entity(name="passage_id", join_keys=["passage_id"], value_type=ValueType.STRING)
source = FileSource(name="rag_source", path="data/passages.parquet", timestamp_field="event_timestamp")

rag_view = FeatureView(
    name="rag_passages",
    entities=[passage],
    ttl=timedelta(days=1),
    schema=[
        Field(name="text", dtype=String, description="Chunk text"),
        Field(name="source_id", dtype=String, description="Original document ID"),
        Field(
            name="embedding",
            dtype=Array(Float32),
            description="Embedding vector",
            vector_index=True,
            vector_length=384,
            vector_search_metric="COSINE",
        ),
    ],
    source=source,
    online=True,
)
```

Write and retrieve:

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
store.write_to_online_store(feature_view_name="rag_passages", df=embedded_df)

context = store.retrieve_online_documents_v2(
    features=["rag_passages:embedding", "rag_passages:text", "rag_passages:source_id"],
    query=query_embedding,
    top_k=3,
    distance_metric="COSINE",
).to_df()
```

Expected `context` should contain the requested context fields plus store-specific distance metadata. If it is empty, verify rows were written online, vector dimensions match, and the online store has vector search enabled.

## DocEmbedder Pipeline

`DocEmbedder` automates document chunking, embedding, schema transform, feature view generation, repo apply, and online writes.

Key classes:

- `DocEmbedder(repo_path, yaml_file="feature_store.yaml", feature_view_name="text_feature_view", chunker=None, embedder=None, schema_transform_fn=default_schema_transform_fn, create_feature_view=True, vector_length=None, auto_apply_repo=True)`.
- `TextChunker(ChunkingConfig(...))` splits text by word count.
- `MultiModalEmbedder(EmbeddingConfig(...))` supports text and image modalities with lazy model loading.
- `default_schema_transform_fn(df)` maps chunk/embed output to `passage_id`, `text`, `embedding`, `event_timestamp`, and `source_id`.

Basic ingestion:

```python
import pandas as pd
from feast import DocEmbedder

documents = pd.DataFrame(
    {
        "id": ["doc1", "doc2"],
        "text": ["First document content", "Second document content"],
    }
)

embedder = DocEmbedder(
    repo_path="feature_repo",
    feature_view_name="text_feature_view",
    vector_length=384,
)
result = embedder.embed_documents(
    documents=documents,
    id_column="id",
    source_column="text",
    column_mapping=("text", "text_embedding"),
)
```

Use explicit `vector_length` when the embedding dimension is known. If omitted, `DocEmbedder` tries `embedder.get_embedding_dim("text")` and falls back to `384`.

Custom chunking:

```python
from feast.chunker import ChunkingConfig, TextChunker

chunker = TextChunker(
    ChunkingConfig(chunk_size=120, chunk_overlap=30, min_chunk_size=20, max_chunk_chars=700)
)
```

Custom embedding:

```python
from feast.embedder import BaseEmbedder

class MyEmbedder(BaseEmbedder):
    def _register_default_modalities(self):
        self.register_modality("text", self._embed_text)

    def get_embedding_dim(self, modality):
        return 768 if modality == "text" else None

    def embed(self, values, modality):
        return self._modality_handlers[modality](values)

    def _embed_text(self, values):
        # Return a NumPy array shaped (len(values), 768).
        ...
```

Custom schema transform must be annotated exactly as taking and returning `pd.DataFrame`; `DocEmbedder` validates the function signature.

```python
import pandas as pd

def to_rag_schema(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "passage_id": df["chunk_id"],
            "text": df["text"],
            "embedding": df["text_embedding"],
            "event_timestamp": pd.Timestamp.utcnow(),
            "source_id": df["original_id"],
        }
    )
```

## FeastVectorStore

`FeastVectorStore(repo_path, rag_view, features)` is a convenience wrapper used by `FeastRAGRetriever`.

Behavior from source evidence:

- Lazily constructs `FeatureStore(repo_path=repo_path)`.
- Applies the provided RAG feature view before querying.
- Finds the first schema field with `vector_index=True` and passes its `vector_search_metric` to retrieval.
- Calls `store.retrieve_online_documents_v2(features=..., query=..., query_string=..., query_image_bytes=..., top_k=..., distance_metric=...)`.

Direct use:

```python
from feast.vector_store import FeastVectorStore

vector_store = FeastVectorStore(
    repo_path="feature_repo",
    rag_view=rag_view,
    features=["rag_passages:embedding", "rag_passages:text", "rag_passages:source_id"],
)
response = vector_store.query(query_vector=query_embedding_np, query_string=None, top_k=5)
rows = response.to_df()
```

## FeastRAGRetriever

`FeastRAGRetriever` extends HuggingFace `RagRetriever` and supports `search_type` values `"text"`, `"vector"`, and `"hybrid"`.

Constructor essentials:

```python
from feast.rag_retriever import FeastIndex, FeastRAGRetriever

retriever = FeastRAGRetriever(
    question_encoder_tokenizer=question_encoder_tokenizer,
    question_encoder=question_encoder,
    generator_tokenizer=generator_tokenizer,
    generator_model=generator_model,
    feast_repo_path="feature_repo",
    feature_view=rag_view,
    features=["rag_passages:text", "rag_passages:source_id", "rag_passages:embedding"],
    search_type="hybrid",
    config=rag_config,
    index=FeastIndex(),
    id_field="passage_id",
    text_field="text",
)
```

Retrieval behavior:

- Moves encoder/generator models to CUDA if available, otherwise CPU.
- Normalizes hidden states into query vectors.
- For `search_type="text"`, calls vector store query with `query_vector=None` and `query_string=...`.
- For `search_type="vector"`, calls with `query_vector=...` and `query_string=None`.
- For `search_type="hybrid"`, passes both when available.
- Requires a schema field with `vector_index=True`; otherwise raises a `ValueError` when extracting embeddings.
- Pads missing documents with empty text, zero vectors, and ID `-1` so the HuggingFace RAG shape contract is preserved.
- Default document formatting omits long vector fields and includes non-vector metadata.

## Milvus With Local Fallback Plan

When a user wants Milvus but the service is unavailable:

1. Keep the production target config documented with `type: milvus`, remote `host`, `port`, credentials, `vector_enabled: true`, `embedding_dim`, `index_type`, and `metric_type`.
2. For local planning, create a second config using local path-based Milvus if supported by the installed Milvus client, or SQLite vector mode if the Python/runtime supports it.
3. Keep feature definitions identical across environments; only switch `feature_store.yaml` online store settings.
4. Use `../scripts/vector_config_lint.py feature_store.yaml --config-only` and `../scripts/vector_config_lint.py feature_repo.py` before connecting to the service.
5. Run `feast apply` only after service dependencies are installed and reachable.
6. If native vector DB checks are unsafe or unavailable, validate schema and query code with a mocked `FeastVectorStore` or small local store before service integration.

## Prompt Context Formatting

After retrieval, build a compact prompt from text/context fields, not from embeddings:

```python
def format_context(df):
    lines = []
    for row in df.to_dict("records"):
        source = row.get("source_id", "unknown")
        text = row.get("text", "")
        lines.append(f"Source: {source}\n{text}")
    return "\n\n".join(lines)
```

Do not pass vector arrays directly to the LLM unless the user explicitly asks for diagnostics.
