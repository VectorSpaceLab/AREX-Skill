# Troubleshooting embeddings and generative workflows

This guide assumes no live model/API verification unless the user has explicitly provided credentials, network permission, model download permission, and a verification target.

## Fast triage

1. **Is the task allowed to use downloads or external APIs?** If not, do not instantiate provider embeddings, `SlumberChunker` with a real provider, or uncached local model identifiers.
2. **Are optional modules installed?** Run `../scripts/optional_dependency_probe.py` from this sub-skill directory or pass its path directly.
3. **Is the failure from Chonkie Cloud/API or from a third-party provider?** `CHONKIE_API_KEY` belongs to Chonkie Cloud/API. Embedding/genie providers use their own keys such as `OPENAI_API_KEY`, `GEMINI_API_KEY`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `COHERE_API_KEY`, `JINA_API_KEY`, `VOYAGE_API_KEY`, `GROQ_API_KEY`, or `CEREBRAS_API_KEY`.
4. **Can a deterministic fallback satisfy the task?** If yes, route to `../chunking-and-types/` for deterministic chunkers and return to embeddings only when vectors are truly needed.
5. **Does the workflow belong in a pipeline or vector store?** Pipeline ordering belongs to `../pipelines-and-processing/`; vector DB writes belong to `../integrations-and-storage/`.

## Dependency errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `model2vec is not available` | `Model2VecEmbeddings` or semantic default without model2vec dependency. | Install `chonkie[model2vec]` or `chonkie[semantic]`, or pass a prebuilt `BaseEmbeddings` object. |
| `sentence_transformers is not available` | `SentenceTransformerEmbeddings` or `LateChunker` without the `st` extra. | Install `chonkie[st]`; for no-download operation, also use an already cached/local model. |
| `transformers is not installed` | `NeuralChunker` without neural dependencies. | Install `chonkie[neural]`; verify Torch device selection separately. |
| `catsu package is not available` from OpenAI/Gemini/Jina/Cohere/Voyage embeddings | Provider wrapper delegates to `CatsuEmbeddings` in this release. | Install `chonkie[catsu]` or the aggregate `chonkie[embeddings]`. |
| `litellm package is not available` | `LiteLLMEmbeddings` without LiteLLM. | Install `chonkie[litellm]`. |
| Azure imports fail | Missing `openai`, `tiktoken`, or `azure-identity`. | Install `chonkie[azure-openai]`. |
| Genie JSON mode complains about Pydantic | `SlumberChunker(extract_mode="json")` or provider genie JSON support without Pydantic. | Install the provider/aggregate genie extra or use `extract_mode="text"`. |
| `No provider found for ...` from `AutoEmbeddings` | Provider alias is not registered or typoed. | Use registered aliases such as `model2vec`, `st`, `openai`, `azure_openai`, `gemini`, `cohere`, `jina`, `voyageai`, `catsu`, or `litellm`. |

Avoid installing broad extras by default. The required Chonkie skill environment did not require provider/model extras, so install only the optional family needed for the user's selected workflow.

## Model download and cache failures

Common symptoms:

- Model identifier works on another machine but fails here.
- A workflow hangs or errors while loading `minishlab/...`, `sentence-transformers/...`, `nomic-ai/...`, or `mirth/chonky...`.
- Offline/air-gapped execution unexpectedly attempts to contact a model hub.

Actions:

1. Ask whether model downloads are allowed. If not, do not retry network model loads.
2. Prefer passing an already-created `BaseEmbeddings`, `SentenceTransformerEmbeddings`, or local model path/object that the user confirms is present.
3. For SentenceTransformer models, pass constructor kwargs supported by SentenceTransformer for cache/offline/device behavior.
4. For Model2Vec models, use a known local model path/object when available; otherwise choose a deterministic chunker.
5. For `NeuralChunker`, verify both `transformers` and `torch`, then verify the exact model weights are available before using it in production.
6. If the goal is only chunk boundaries, choose deterministic chunking. If the goal is retrieval vectors, chunk deterministically and attach embeddings later.

Do not claim model-cache success solely because the optional Python package imports. A model identifier can still fail at load time.

## Credential and endpoint failures

| Class/family | Required credential pattern | Common mistake |
| --- | --- | --- |
| `OpenAIEmbeddings`, `OpenAIGenie` | `api_key` or `OPENAI_API_KEY` | Confusing `CHONKIE_API_KEY` with OpenAI's key. |
| `AzureOpenAIEmbeddings`, `AzureOpenAIGenie` | Azure endpoint plus `AZURE_OPENAI_API_KEY` or Azure identity | Supplying a model name but no `azure_endpoint`; forgetting deployment name differs from model. |
| `GeminiEmbeddings`, `GeminiGenie` | `api_key` or `GEMINI_API_KEY` | Installing only package deps but not setting credentials. |
| `JinaEmbeddings` | `api_key` or `JINA_API_KEY` | Using provider alias `jinaai` with `AutoEmbeddings`; Chonkie alias is `jina`, while Catsu provider name is `jinaai`. |
| `CohereEmbeddings` | `api_key` or `COHERE_API_KEY` | Requesting a batch size above Cohere wrapper cap of 96. |
| `VoyageAIEmbeddings` | `api_key`, `VOYAGE_API_KEY`, or `VOYAGEAI_API_KEY` | Requesting a batch size above wrapper cap of 128. |
| `LiteLLMEmbeddings` | Provider-specific key/env recognized by LiteLLM, or `api_key` | Omitting `dimension` for an unknown model, causing an initialization-time test embed call. |
| `GroqGenie` | `api_key` or `GROQ_API_KEY` | Expecting OpenAI key/base URL behavior. |
| `CerebrasGenie` | `api_key` or `CEREBRAS_API_KEY` | Expecting strict schema enforcement; Cerebras path guides JSON via prompt plus JSON object mode. |

For provider debugging, first instantiate only after verifying the package and credential names. Then perform the smallest possible authorized request. Respect user quotas and do not run live calls from skill diagnostics unless the script or prompt explicitly opts in.

## Batch, timeout, and rate-limit issues

- Reduce `batch_size` when providers reject large batches, time out, or return partial failures.
- Increase `timeout` only after confirming that retries are not masking credential/model-name errors.
- `OpenAIGenie` retries rate limit, API, and timeout errors with exponential backoff up to five attempts. Other classes may not apply the same retry policy.
- `CatsuEmbeddings.embed_batch` batches and can fall back to single calls if a batch fails; this improves robustness but can increase cost/latency.
- `CohereEmbeddings` caps batch size at 96; `VoyageAIEmbeddings` caps at 128.
- For long documents, prefer chunking deterministically first, then embedding chunks in bounded batches.

## `AutoEmbeddings` surprises

Symptom: a provider or local model fails, then Chonkie attempts SentenceTransformer loading.

Cause: `AutoEmbeddings` falls back to `SentenceTransformerEmbeddings` after registry/constructor failure.

Fixes:

- Use an explicit embedding class when failure should be hard and visible.
- Pass a concrete `BaseEmbeddings` instance to `SemanticChunker` or `EmbeddingsRefinery`.
- If offline, avoid unknown string identifiers and verify optional dependencies with the probe script before constructing the model.

## `SemanticChunker` problems

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| Parameter validation error | `threshold`, `chunk_size`, `similarity_window`, filter settings, or delimiter type out of range. | Use `0 < threshold < 1`, positive sizes/windows, `filter_polyorder < filter_window`, and `str`/`list[str]` delimiters. |
| Too few or too many chunks | Threshold/window/filter settings do not fit text structure. | Compare with deterministic `SentenceChunker`; adjust `threshold`, `similarity_window`, and `min_sentences_per_chunk`. |
| Hidden model load/download | String `embedding_model` resolved through `AutoEmbeddings`. | Pass a prebuilt embedding object or choose deterministic fallback. |
| Need embeddings in output chunks | `SemanticChunker` uses embeddings internally but does not guarantee chunks carry vectors. | Run `EmbeddingsRefinery` after chunking or use `LateChunker` if its token-level strategy is appropriate. |

## `LateChunker` problems

- Missing dependency: install `chonkie[st]`.
- Model cannot load: use a cached/local SentenceTransformer model or deterministic fallback.
- Token-count mismatch errors: verify the tokenizer/model pair and avoid custom models that do not expose compatible token embeddings.
- Memory pressure: use a smaller model, smaller text batches, deterministic chunking plus `EmbeddingsRefinery`, or a provider embedding path with explicit batching.

## `NeuralChunker` problems

- Unsupported model: choose one of Chonkie's supported identifiers or pass a compatible Transformers token-classification model object.
- Tokenizer failure: use the matching tokenizer for the selected model.
- Device errors: set `device_map="cpu"` for CPU-only operation or verify accelerator support before using `device_map="auto"`.
- Inconsistent boundaries: check reconstruction (`"".join(chunk.text for chunk in chunks) == original_text`) and minimum-length constraints; fall back to deterministic chunking if reproducibility matters.

## `SlumberChunker` problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Constructor fails without a key | `genie=None` creates `GeminiGenie()` by default. | Pass an explicit `BaseGenie`, a test/mock genie, or provider credentials. |
| JSON mode import error | Pydantic missing or provider does not support structured output. | Install the genie extra or set `extract_mode="text"`. |
| Repeated invalid split indices | Provider output is not a clean integer/JSON or exceeds candidate bounds. | Lower `candidate_size`, improve prompt/provider settings externally, use JSON mode if supported, or accept fallback grouping. |
| Progress output pollutes logs | `verbose=True` default. | Use `verbose=False` in scripts and automated workflows. |
| Nondeterministic boundaries | LLM/provider behavior varies. | Use deterministic chunking, a mock/test genie, or provider-side deterministic settings when available. |

## Safe fallback recipes

### Offline semantic request fallback

```python
from chonkie import RecursiveChunker

chunker = RecursiveChunker(tokenizer="character", chunk_size=512)
chunks = chunker.chunk(text)
```

### Defer embeddings until dependencies exist

```python
from chonkie import RecursiveChunker

chunks = RecursiveChunker(tokenizer="character", chunk_size=512).chunk(text)
# Later, when model/provider access is approved:
# chunks = EmbeddingsRefinery(embedding_model=...).refine(chunks)
```

### Development-only Slumber test

```python
from chonkie import BaseGenie, SlumberChunker

class FixedGenie(BaseGenie):
    def generate(self, prompt: str) -> str:
        return "1"

chunks = SlumberChunker(genie=FixedGenie(), extract_mode="text", verbose=False).chunk(text)
```

These fallbacks avoid live model/provider verification claims and keep the task moving when optional resources are unavailable.
