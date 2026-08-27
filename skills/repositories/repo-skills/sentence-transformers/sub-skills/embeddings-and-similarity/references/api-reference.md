# Dense Embedding API Reference

## Core Imports

```python
from sentence_transformers import SentenceTransformer, SimilarityFunction
```

`SentenceTransformer` is the dense bi-encoder class. Do not use this sub-skill for `CrossEncoder` or `SparseEncoder` workflows.

## Construction

Common constructor parameters:

- `model_name_or_path`: Hugging Face model id, local model directory, or `None` when manually passing modules.
- `device`: single device string such as `"cpu"`, `"cuda"`, or `"mps"`; leave unset to let the library choose.
- `prompts` and `default_prompt_name`: prompt templates used by prompt-aware embedding models.
- `cache_folder`: Hugging Face/Sentence Transformers cache location; keep this user-configurable in scripts.
- `trust_remote_code`: keep `False` unless the user explicitly accepts remote custom code.
- `revision`, `token`, `local_files_only`: control model download, private access, and offline behavior.
- `backend`: `"torch"`, `"onnx"`, or `"openvino"`; route export/optimized backend preparation to `../backend-export-optimization/`.
- `similarity_fn_name`: `"cosine"`, `"dot"`, `"euclidean"`, or `"manhattan"`.
- `truncate_dim`: default embedding dimension truncation for Matryoshka-style models or compact indexes.

Offline-safe loading pattern:

```python
model = SentenceTransformer(
    model_id_or_path,
    local_files_only=True,
    trust_remote_code=False,
)
```

## Encoding Methods

Use `model.encode(inputs, ...)` for symmetric embedding tasks such as STS, clustering, classification features, and direct similarity. `inputs` can be a single item or a list; supported item types depend on the model.

Important encode options:

- `prompt_name` or `prompt`: selects an instruction template for models that were trained with prompts.
- `batch_size`: start with `32`, then benchmark against sequence length and device memory.
- `show_progress_bar`: set explicitly in scripts instead of relying on notebook/terminal detection.
- `output_value`: keep `"sentence_embedding"` for dense vectors; `"token_embeddings"` is a specialized diagnostic path.
- `precision`: `"float32"`, `"int8"`, `"uint8"`, `"binary"`, or `"ubinary"`; non-float options quantize returned embeddings and can change dtype/shape expectations.
- `convert_to_numpy` / `convert_to_tensor`: choose the container required by the next step.
- `device`: can be a single device or a list for multi-process/multi-device encoding.
- `normalize_embeddings`: use `True` when downstream dot-product search assumes unit vectors.
- `truncate_dim`: per-call override for shortened embeddings.
- `pool` and `chunk_size`: advanced multi-process knobs; prefer simple single-process encoding unless corpus size justifies it.

## Query and Document Encoding

For retrieval-flavored dense models, prefer:

```python
query_embeddings = model.encode_query(queries, normalize_embeddings=True)
document_embeddings = model.encode_document(documents, normalize_embeddings=True)
```

`encode_query` uses the model's `"query"` prompt when available and sets the task as query. `encode_document` tries document-style prompts such as `"document"`, `"passage"`, or `"corpus"` and sets the task as document. For models without such prompts, these methods behave like `encode` while preserving future compatibility.

Use manual `prompt` or `prompt_name` only when the model card or local model config documents the expected instruction. Do not mix incompatible prompt text between queries and documents in the same similarity space.

## Similarity API

`model.similarity(a, b)` returns all pairwise scores with shape `(len(a), len(b))`. `model.similarity_pairwise(a, b)` returns aligned pair scores and requires compatible row counts.

The configured metric is `model.similarity_fn_name`:

- `"cosine"`: default and usually safest.
- `"dot"`: good for already-normalized embeddings and dot-tuned retrieval models.
- `"euclidean"`: negative Euclidean distance, so larger values are more similar.
- `"manhattan"`: negative Manhattan distance, so larger values are more similar.

If a model normalizes embeddings internally or you pass `normalize_embeddings=True`, dot product can be faster than cosine because cosine re-normalizes vectors.

## Multimodal Inputs

Some dense models support non-text inputs. Check before encoding:

```python
print(model.modalities)
print(model.supports("image"))
```

Supported forms can include:

- Text strings.
- Image file paths, URLs, PIL images, NumPy arrays, or Torch tensors.
- Audio file paths, arrays/tensors, dicts with `"array"` and `"sampling_rate"`, or TorchCodec decoders when installed.
- Video file paths, arrays/tensors, dicts with `"array"` and `"video_metadata"`, or TorchCodec decoders when installed.
- Multimodal dicts with `"text"`, `"image"`, `"audio"`, or `"video"` keys.
- Chat-style message lists for models that expose a `"message"` modality.

Install optional extras for the modality before diagnosing model logic: `sentence-transformers[image]`, `sentence-transformers[audio]`, or `sentence-transformers[video]`.

## Output Validation Checklist

- Single input may return a one-dimensional embedding; list input should return one row per input.
- `embeddings.shape[0]` must equal the number of input items for list encoding.
- `truncate_dim` should reduce the final dimension and never exceed the native embedding dimension.
- Non-float `precision` can return quantized arrays; downstream similarity libraries may require float embeddings.
- Similarity matrices should have query rows and document columns in the intended order.
- Normalized embeddings should have norms close to `1.0` when represented as float vectors.
