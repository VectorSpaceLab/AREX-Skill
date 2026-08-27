# Troubleshooting

## Install And Optional Extras

Symptoms:

- `ModuleNotFoundError: No module named 'pymilvus'`, `qdrant_client`, `faiss`, `sentence_transformers`, `transformers`, `torch`, `PIL`, or `docling`.
- `ImportError` when importing `DocEmbedder`, `MultiModalEmbedder`, `FeastRAGRetriever`, or vector online store classes.
- Model download failures during the first call to `MultiModalEmbedder.text_model` or image model access.

Actions:

```bash
python -c "import feast; print(feast.__version__)"
python -c "from feast import DocEmbedder; from feast.rag_retriever import FeastRAGRetriever; print('ok')"
pip install 'feast[milvus,rag]'
pip install 'feast[qdrant]'
pip install 'feast[elasticsearch]'
pip install 'feast[faiss]'
pip install 'feast[sqlite_vec]'
```

Install only the extras needed for the target store/workflow. For a pure config review, do not install service clients; run the bundled lint script instead.

## Vector Schema Validation

Common schema errors:

- `vector_index=True` without `vector_length` or with `vector_length=0`.
- Query vector length does not match the feature field/store dimension.
- Multiple vector-indexed fields in one feature view.
- A vector field is missing from the retrieval `features` list.
- Feature view is not `online=True` or has not been applied/written to online store.
- Store-level `embedding_dim` disagrees with field-level `vector_length`.

Run:

```bash
python ../scripts/vector_config_lint.py feature_repo.py
python ../scripts/vector_config_lint.py feature_store.yaml --config-only
```

Expected failure signal for missing vector length:

```text
ERROR: field embedding has vector_index=True but no positive vector_length
```

Fix by setting the model output dimension explicitly:

```python
Field(
    name="embedding",
    dtype=Array(Float32),
    vector_index=True,
    vector_length=384,
    vector_search_metric="COSINE",
)
```

## Retrieval API Misuse

Prefer `retrieve_online_documents_v2(...)` when available:

```python
store.retrieve_online_documents_v2(
    features=["rag_passages:embedding", "rag_passages:text"],
    query=query_embedding,      # flat list[float]
    top_k=3,
    distance_metric="COSINE",
).to_df()
```

Misuse patterns:

- Passing a tensor or nested batch instead of a flat `list[float]`; convert with `tensor.detach().cpu().numpy().tolist()[0]` or `np_array.tolist()`.
- Passing `query_string` without a store that supports text/hybrid search.
- Passing feature refs without the `feature_view:feature` format.
- Calling retrieval before `feast apply` or before writing/materializing online data.
- Using legacy `retrieve_online_documents(...)` when v2 is supported and needed for standard features plus embeddings.

If `FeastRAGRetriever` raises unsupported search type, use one of:

```python
search_type="text"
search_type="vector"
search_type="hybrid"
```

If it raises `No field with 'vector_index=True' found`, inspect the exact `FeatureView` instance passed to the retriever and confirm its schema includes the vector field.

## Empty Or Low-Quality Results

Symptoms:

- Retrieval returns an empty DataFrame or fewer than `top_k` rows.
- RAG answers ignore the knowledge base.
- Returned rows lack text/context columns.

Actions:

1. Confirm rows are written to the online store:

   ```python
   store.write_to_online_store(feature_view_name="rag_passages", df=embedded_df)
   ```

2. Confirm query and stored vectors share the same model/dimension.
3. Include text/context fields in `features`, not only the embedding field.
4. Use the same metric style as schema/store config, e.g. `COSINE` with cosine-normalized vectors.
5. For `TextChunker`, tune `chunk_size`, `chunk_overlap`, `min_chunk_size`, and `max_chunk_chars`; default small trailing chunks may be dropped.
6. Verify the prompt formatter uses retrieved text fields and not embedding arrays.

## Service And Credential Failures

Milvus:

- Check `host`, `port` (`19530` is common), credentials, and network reachability.
- Check `vector_enabled: true`, `embedding_dim`, `index_type`, and `metric_type`.
- For local development, use path/local mode when supported or plan a SQLite vector fallback.

Postgres/pgvector:

- Ensure the Postgres service is reachable and the pgvector extension is installed/enabled.
- Set `vector_enabled: true`; otherwise retrieval may fail with a pgvector disabled message.

Qdrant/Elasticsearch/MongoDB:

- Check URL/host/API key and index permissions.
- For MongoDB Atlas vector search, vector indexes may not be immediately queryable; increase wait timeout/poll interval if index creation times out.

Faiss:

- Install `feast[faiss]` and provide `dimension`, `index_path`, and index options.
- Treat Faiss as experimental in this Feast version because the alpha support matrix marks retrieval/indexing incomplete.

## DocEmbedder Failures

Signature validation:

- `schema_transform_fn must be a function that takes a DataFrame and returns a DataFrame` means the custom transform lacks exact `pd.DataFrame` annotations or has the wrong parameter count.

Chunking:

- `chunk_overlap (...) must be less than chunk_size (...)` means the sliding window step would be zero or negative.
- Empty source text can produce no chunks.
- Trailing chunks shorter than `min_chunk_size` are intentionally dropped.

Embedding:

- `Unsupported modality: 'video'` or similar means `MultiModalEmbedder` does not have a handler for that modality. Register a custom modality or subclass `BaseEmbedder`.
- First model access may download SentenceTransformer or CLIP weights; use a mocked/custom embedder for offline tests.

Generated repo:

- `feature_view_name` must be a valid Feast name and Python identifier; avoid hyphens and leading underscores.
- `DocEmbedder` may auto-apply the repo; set `auto_apply_repo=False` while drafting configs without service access.

## FeastRAGRetriever Failures

- Requires HuggingFace transformers-style tokenizers/models and a `RagConfig` with a retrieval vector size matching retrieved embeddings.
- Moves models to GPU when CUDA is available; CUDA/torch setup issues are environment problems, not Feast schema problems.
- `id_field` and `text_field` must match keys returned by the vector retrieval response.
- If fewer than `n_docs` are returned, the retriever pads empty documents; this can hide upstream retrieval sparsity, so inspect raw `vector_store.query(...).to_dict()`.

## Safe Debug Order

1. Lint feature definitions/config snippets with `../scripts/vector_config_lint.py`.
2. Import Feast and optional classes locally.
3. Apply repo only after config is valid.
4. Write one known vector row to the online store.
5. Retrieve with the same vector and `top_k=1`.
6. Add text/hybrid query only after vector retrieval works.
7. Add LLM calls last; keep API keys and prompts outside skill/runtime artifacts.
