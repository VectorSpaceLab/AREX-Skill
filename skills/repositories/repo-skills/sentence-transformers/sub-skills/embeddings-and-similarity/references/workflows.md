# Dense Embedding Workflows

## Symmetric Text Similarity

Use this for semantic textual similarity, duplicate detection on small batches, clustering features, or classification features.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
sentences = ["The weather is lovely today.", "It's sunny outside.", "He drove to the stadium."]
embeddings = model.encode(sentences, convert_to_numpy=True)
scores = model.similarity(embeddings, embeddings)
```

Validate that `embeddings.shape[0] == len(sentences)` and `scores.shape == (len(sentences), len(sentences))`.

## Prompt-Aware Query and Document Embeddings

Use this when a model card mentions query/document prompts, instructions, or asymmetric retrieval.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")
queries = ["How do I reset my password?"]
documents = ["Users can reset passwords from account settings.", "Invoices are emailed monthly."]
query_embeddings = model.encode_query(queries, normalize_embeddings=True, truncate_dim=128)
document_embeddings = model.encode_document(documents, normalize_embeddings=True, truncate_dim=128)
scores = model.similarity(query_embeddings, document_embeddings)
```

Decision rules:

- Use `encode_query` for search questions and `encode_document` for corpus entries.
- Use the same `truncate_dim` for both sides.
- Use `normalize_embeddings=True` when scores will feed dot-product search; cosine is safe for direct scoring.
- If you choose `precision="int8"`, `"uint8"`, `"binary"`, or `"ubinary"`, verify downstream code can handle quantized embeddings.

## Batch and Device Tuning

Start simple:

```python
embeddings = model.encode(texts, batch_size=32, device="cuda", show_progress_bar=True)
```

Then tune:

- Reduce `batch_size` on out-of-memory errors or long inputs.
- Increase `batch_size` when GPU/CPU utilization is low and memory is stable.
- Use `device="cpu"` for deterministic smoke tests and small local validation.
- Use a list of devices only for large batches where multi-process overhead is worthwhile.
- Keep service code explicit about `convert_to_numpy` or `convert_to_tensor` so callers receive stable types.

## Local and Private Models

For reproducible or offline workflows:

```python
model = SentenceTransformer(
    model_path_or_id,
    local_files_only=True,
    revision=revision,
    token=token,
    trust_remote_code=False,
)
```

Guidelines:

- Use a local model path or pre-populated cache with `local_files_only=True`; otherwise construction may fail.
- Pass private model tokens via environment/config, not hardcoded source.
- Pin `revision` for production reproducibility.
- Do not enable `trust_remote_code=True` unless the user has reviewed and accepted the model repository code.

## Multimodal Routing

Before encoding images, audio, video, or mixed inputs:

```python
model = SentenceTransformer(model_id)
if not model.supports("image"):
    raise ValueError(f"Model modalities are {model.modalities}; choose an image-capable model")
```

Then pass the input format supported by the model and installed extras. For images, a model may accept file paths, URLs, PIL images, arrays, or tensors. For audio/video, extras and sometimes `torchcodec` are required. When optional dependencies are missing, fix the install before rewriting encode logic.

## Smoke Script

Use `scripts/dense_embedding_smoke.py` for a help-safe, no-default-network CLI adapted from the repository's computing-embeddings example:

```bash
python scripts/dense_embedding_smoke.py --help
python scripts/dense_embedding_smoke.py --model sentence-transformers/all-MiniLM-L6-v2 --sentences "hello" "hello world" --normalize
```

The script intentionally requires `--model` so it does not download a model by default. Add `--local-files-only` when the model must already exist locally.
