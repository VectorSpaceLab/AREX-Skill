# Model API, Metadata, Prompts, and Wrappers

## Built-in Model Metadata

MTEB exposes model metadata separately from model loading:

- `mteb.get_model_meta(model_name, revision=None, fetch_from_hf=False, fill_missing=False, experiment_kwargs=None)` returns a `ModelMeta` without necessarily loading model weights.
- `mteb.get_model(model_name, revision=None, device=None, *, embed_dim=None, **kwargs)` loads the model object and passes extra kwargs to the registered loader.
- `mteb.get_model_metas(...)` filters registered metadata by `model_names`, `languages`, `open_weights`, `frameworks`, `n_parameters_range`, `use_instructions`, `zero_shot_on`, `model_types`, `modalities`, and `exclusive_modality_filter`.
- `ModelMeta.load_model(device=None, embed_dim=None, **kwargs)` is useful when you want to keep metadata around and defer loading until needed.

Recommended pattern:

```python
import mteb

meta = mteb.get_model_meta("intfloat/multilingual-e5-small")
print(meta.name, meta.revision, meta.embed_dim, meta.framework)
model = meta.load_model(device="cpu")
```

Use `mteb.get_model(...)` when immediate loading is acceptable. Use `get_model_meta(...)` when checking metadata, filtering models, deferring load, or passing a metadata object into a later evaluation workflow.

## Fallback Loading and Revisions

If a model is registered, `get_model_meta` returns the registry entry and validates that a supplied `revision` matches the recorded revision. If `fetch_from_hf=True` and the model is not in the registry, MTEB attempts to infer metadata from the Hugging Face Hub.

Expected signals:

- Unknown registered name without Hub fallback raises a `KeyError` with close-match suggestions.
- Wrong revision for a registered model raises `ValueError` with the expected revision.
- Some renamed baselines emit a deprecation warning and map to canonical names such as `mteb/baseline-bm25s`.

## SentenceTransformers and CrossEncoders

MTEB can evaluate plain SentenceTransformers-compatible models, but registered MTEB loaders are preferred because they often include required prompts, prefixes, modalities, output dtypes, or provider-specific kwargs.

Dense encoder:

```python
import mteb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
tasks = mteb.get_tasks(tasks=["Banking77Classification"])
results = mteb.evaluate(model, tasks=tasks)
```

CrossEncoder reranker:

```python
import mteb
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
tasks = mteb.get_tasks(tasks=["AskUbuntuDupQuestions"])
results = mteb.evaluate(model, tasks=tasks)
```

For registered SentenceTransformer models, MTEB uses wrappers such as `SentenceTransformerEncoderWrapper` and `CrossEncoderWrapper`. These wrappers support `revision`, `device`, `embed_dim`, prompt routing, and selected multimodal options such as `fps`, `max_frames`, `num_frames`, `target_sampling_rate`, and `max_samples` when task inputs contain non-text modalities.

## Prompt Routing

`SentenceTransformerEncoderWrapper` accepts `model_prompts: dict[str, str] | None`. Prompt lookup prefers more specific keys before generic keys:

1. `"<task-name>-<prompt-type>"`, for example `"MSMARCO-query"`
2. `"<task-name>"`
3. `"<task-type>-<prompt-type>"`, for example `"Retrieval-document"`
4. `"<task-type>"`
5. `"query"` or `"document"`

MTEB passes `PromptType.query` for query-side encoding and `PromptType.document` for corpus/document-side encoding. If a SentenceTransformers model has prompts but only one of `query` or `document` is configured, expect warnings because many instruction models need both sides for reliable retrieval results.

Example:

```python
import mteb
from mteb.models import SentenceTransformerEncoderWrapper

model = SentenceTransformerEncoderWrapper(
    "intfloat/multilingual-e5-small",
    model_prompts={"query": "query: ", "document": "passage: "},
)
```

## `encode_kwargs`

`mteb.evaluate` accepts `encode_kwargs=None` and forwards those kwargs through wrapper `encode(...)` calls. Common examples include `batch_size`, SentenceTransformers options, provider-specific options, or precision settings. In `SentenceTransformerEncoderWrapper`, an `encode_kwargs` key named `precision` updates the model metadata `experiment_kwargs["output_dtypes"]` to reflect compressed/native precision runs.

Safe pattern:

```python
results = mteb.evaluate(
    model,
    tasks=tasks,
    encode_kwargs={"batch_size": 64},
)
```

Validation steps:

- Keep kwargs accepted by the underlying model’s `encode`, `predict`, `index`, or `search` implementation.
- If a custom encoder rejects unexpected kwargs, add `**kwargs` to the method signature or remove the option from `encode_kwargs`.
- Use a small public task first to confirm prompt and kwargs behavior before long benchmark runs.

## Embedding Cache Wrapper

`CachedEmbeddingWrapper` saves embeddings per task under `<cache_path>/<task_name>` and requires a wrapped model with `encode`, `similarity`, `similarity_pairwise`, and `mteb_model_meta` behavior compatible with `EncoderProtocol`.

```python
import mteb
from mteb.models.cache_wrappers import CachedEmbeddingWrapper

model = mteb.get_model("sentence-transformers/all-MiniLM-L6-v2")
model = CachedEmbeddingWrapper(model, cache_path=".mteb-embedding-cache")
results = mteb.evaluate(model, tasks=tasks)
```

Backends:

- Default backend is `NumpyCache`, a memory-mapped NumPy cache.
- `FaissCache` can be supplied with `cache_backend=FaissCache` when FAISS is installed.
- A custom backend must implement MTEB’s `CacheBackendProtocol`.

Cache hygiene:

- Use a cache directory separate from result directories.
- Reuse a cache only when task, split, model, prompt config, tokenizer, preprocessing, modality settings, and encode kwargs are compatible.
- Delete or version the cache after changing prompt templates, `embed_dim`, quantization, tokenizer, or provider model revision.

## Compression Wrapper

`CompressionWrapper(model, output_dtype=OutputDType.INT8, clipping_margin=None)` quantizes embeddings after encoding and updates model metadata experiment kwargs. It supports output dtypes from `mteb.types.OutputDType`, including integer, binary, float16/bfloat16, and float8 variants depending on runtime support.

```python
import mteb
from mteb.models import CompressionWrapper
from mteb.types import OutputDType

model = mteb.get_model("intfloat/multilingual-e5-large-instruct")
model = CompressionWrapper(model, output_dtype=OutputDType.INT8, clipping_margin=(0.025, 0.975))
results = mteb.evaluate(model, tasks=tasks)
```

Expected signals:

- Invalid `clipping_margin` must satisfy `0 < lower < upper < 1` and otherwise raises `ValueError`.
- Integer quantization estimates per-dimension thresholds; very small batches can trigger warnings that parameters are unstable.
- If a model natively supports the requested dtype, MTEB warns that native compressed embeddings may perform better than wrapper-side quantization.

## BM25 Baselines and Optional Extras

MTEB includes BM25 baselines loaded through the same model API:

```python
import mteb

model = mteb.get_model("mteb/baseline-bm25s")
model = mteb.get_model("mteb/baseline-bm25s-subword")
```

Install the matching extra first:

```bash
pip install "mteb[bm25s]"
```

The BM25 loader can accept a Hugging Face tokenizer name or a custom `text -> list[str]` callable:

```python
model = mteb.get_model("mteb/baseline-bm25s", tokenizer="bert-base-multilingual-cased")
```

Provider-backed models such as OpenAI, Voyage, Jina, Cohere, Bedrock, Gemini, or vLLM wrappers can require optional extras and credentials. Prefer installing only the extra for the provider under test, for example `pip install "mteb[openai]"` or the documented extra group for that wrapper. Optional dependencies should be imported inside wrapper code rather than at module import time when contributing a new model implementation.
