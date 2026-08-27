# Custom Encoders, CrossEncoders, and Search Protocols

## Protocol Choice

MTEB model objects normally satisfy one of three protocols:

- `EncoderProtocol`: dense or sparse embedding model with `encode(...)`, `similarity(...)`, and `similarity_pairwise(...)`.
- `CrossEncoderProtocol`: pairwise scorer with `predict(...)` for reranking-style tasks.
- `SearchProtocol`: retrieval model with `index(...)` and `search(...)`, usually when the model owns its indexing/search logic.

Run the bundled validator before evaluation:

```bash
python sub-skills/models-and-encoders/scripts/validate_encoder_protocol.py path.to.module:object_name
```

The helper imports a local module or Python object and checks method names/signatures without loading remote model weights. It does not prove numerical correctness; it catches common protocol mismatches early.

## `EncoderProtocol`

An encoder must provide:

```python
def encode(
    self,
    inputs,
    *,
    task_metadata,
    hf_split,
    hf_subset,
    prompt_type=None,
    **kwargs,
):
    ...
```

Expected return shape is `(number_of_inputs, embedding_dimension)` as a NumPy array, torch tensor, or compatible array-like object. MTEB passes dataloaders whose batches contain fields such as `text`, and for multimodal tasks may contain fields such as `image`, `audio`, or `video`.

Recommended encoder extras:

- `mteb_model_meta` property or attribute carrying a `ModelMeta` when model metadata matters.
- `similarity(embeddings1, embeddings2)` returning a matrix of pairwise scores.
- `similarity_pairwise(embeddings1, embeddings2)` returning one score per aligned pair.
- Constructor shape compatible with `__init__(model_name, revision=None, *, device=None, **kwargs)` if the object is loaded by `ModelMeta.loader` or the CLI.

Minimal skeleton:

```python
import numpy as np

class MyEncoder:
    def __init__(self, model_name=None, revision=None, *, device=None, **kwargs):
        self.model_name = model_name

    def encode(self, inputs, *, task_metadata, hf_split, hf_subset, prompt_type=None, **kwargs):
        rows = []
        for batch in inputs:
            texts = batch["text"]
            rows.extend(np.zeros((len(texts), 384), dtype="float32"))
        return np.asarray(rows)

    def similarity(self, embeddings1, embeddings2):
        return np.asarray(embeddings1) @ np.asarray(embeddings2).T

    def similarity_pairwise(self, embeddings1, embeddings2):
        return np.sum(np.asarray(embeddings1) * np.asarray(embeddings2), axis=1)
```

## `CrossEncoderProtocol`

A cross-encoder must provide:

```python
def predict(
    self,
    inputs1,
    inputs2,
    *,
    task_metadata,
    hf_split,
    hf_subset,
    prompt_type=None,
    **kwargs,
):
    ...
```

Expected return is a one-dimensional array-like sequence of relevance scores for aligned pairs from `inputs1` and `inputs2`. MTEB’s `CrossEncoderWrapper` wraps SentenceTransformers `CrossEncoder` instances and collects pairs before calling `model.predict(...)`.

Use cross-encoders for reranking tasks or retrieval pipelines with pre-ranked documents. For full corpus retrieval without pre-ranked candidates, use an encoder/search model first.

## `SearchProtocol`

A search model owns indexing and search:

```python
def index(self, corpus, *, task_metadata, hf_split, hf_subset, encode_kwargs, num_proc):
    ...

def search(
    self,
    queries,
    *,
    task_metadata,
    hf_split,
    hf_subset,
    top_k,
    encode_kwargs,
    top_ranked=None,
    num_proc=None,
):
    ...
```

`search(...)` returns a nested mapping shaped like `{query_id: {corpus_id: score}}`. A `SearchProtocol` implementation should preserve query and corpus IDs exactly as provided by the task datasets.

## Search Wrappers

MTEB provides wrappers when you have an encoder or cross-encoder but need search-task behavior:

- `SearchEncoderWrapper(model, corpus_chunk_size=50000, index_backend=None)` encodes queries and corpus chunks, computes similarity, and returns top-k retrieval results. If `index_backend` is supplied, it calls backend `add_documents`, `search`, and `clear` operations.
- `SearchCrossEncoderWrapper(model)` reranks `top_ranked` documents with a `CrossEncoderProtocol`. It raises `ValueError("CrossEncoder search requires top_ranked documents for reranking.")` if no pre-ranked candidates are supplied.

Common failure signals:

- `ValueError("Corpus must be indexed before searching.")`: `search(...)` was called before `index(...)`, or a wrapper instance was reused after it reset task state.
- `NaN values detected in the similarity scores`: the encoder returned invalid vectors, unsupported dtype values, or similarity overflowed.
- Empty or incorrect rankings: query/corpus IDs were not preserved, `top_k` was too small, or prompt type was ignored.

## ModelMeta Loader Integration

When contributing a new implementation to MTEB, define a `ModelMeta` with a loader that constructs one of the supported protocols. For normal SentenceTransformers models, `SentenceTransformerEncoderWrapper` is usually enough. For pairwise scorers use `CrossEncoderWrapper`. For custom model classes, make the loader accept `model_name`, `revision`, `device`, and `**kwargs`.

Fields commonly needed in `ModelMeta` include:

- `name`, `loader`, `revision`, `languages`, `open_weights`, `release_date`, `license`, `reference`
- `n_parameters`, `memory_usage_mb`, `embed_dim`, `max_tokens`, `similarity_fn_name`
- `framework`, `model_type`, `modalities`, `use_instructions`
- `loader_kwargs`, such as `model_prompts={"query": "query: ", "document": "passage: "}`
- `extra_requirements_groups` for optional provider dependencies
- `output_dtypes` for native compressed/quantized output support

For adding a model implementation to the MTEB repository itself, switch to `../contributing-to-mteb/`.

## Optional Provider Wrappers

Provider-backed wrappers often fail before protocol validation if their optional dependencies or credentials are absent. When debugging OpenAI, Voyage, Jina, Cohere, Bedrock, Gemini, vLLM, or similar wrappers:

1. Install the provider extra or package group documented for that wrapper.
2. Confirm `import mteb` and `pip check` pass.
3. Import the wrapper module in isolation.
4. Validate that the object exposes the expected protocol methods.
5. Only then run a small public task.

When contributing a provider wrapper, import optional packages inside `__init__` or method bodies so base `import mteb` remains usable without the extra.

## Validation Checklist

Before evaluating a custom object:

- Method names match the protocol: `encode`, `predict`, or `index` + `search`.
- Required keyword-only parameters are present: `task_metadata`, `hf_split`, `hf_subset`, and `prompt_type` where relevant.
- Methods accept `**kwargs` or all planned `encode_kwargs`.
- Dense encoders return 2D numeric arrays and preserve row order.
- CrossEncoders return one score per input pair.
- Search models return `{query_id: {doc_id: score}}` using task IDs, not row offsets unless the task IDs are offsets.
- Similarity methods can consume the encoder’s own output dtype.
- Cache/compression wrappers are applied only to encoder-like objects, not bare CrossEncoders.
