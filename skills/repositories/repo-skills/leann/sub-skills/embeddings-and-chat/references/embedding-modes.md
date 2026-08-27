# Embedding Modes

## The Index Metadata Is The Contract

A LEANN index records `embedding_model`, `embedding_mode`, `dimensions`, and, when nonempty, `embedding_options` in `<index>.meta.json`. `LeannSearcher` reads these values and forwards the stored options to the embedding server. A query must therefore reproduce the representation used at build time.

Before diagnosing a search failure, compare all of these fields:

| Field | Why it must match |
|---|---|
| `embedding_model` | Different model weights usually produce a different vector space and may produce a different width. |
| `embedding_mode` | Selects the sentence-transformers, MLX, or OpenAI-compatible implementation and dependencies. |
| `dimensions` | The backend was built for this exact vector width. |
| `embedding_options` | Endpoint and task-template differences can change either availability or vector meaning. |
| distance/normalization behavior | Mixing normalized and unnormalized build/query vectors changes scoring even when widths match. |

`LeannBuilder(..., dimensions=None)` infers the width from one dummy embedding before building. Supplying `dimensions` does not transform model output; it only declares the expected backend width. Rebuild after changing a model, mode, output width, or normalization policy.

## Selected Modes

| Mode | Typical model | Runtime and network | Device and cache | Output behavior |
|---|---|---|---|---|
| `sentence-transformers` | `sentence-transformers/all-MiniLM-L6-v2`, `BAAI/bge-base-en-v1.5`, `Qwen/Qwen3-Embedding-0.6B` | Requires `sentence-transformers` and PyTorch. Loading tries the local model cache first, then permits a model download. | `LEANN_EMBEDDING_DEVICE` overrides auto-selection; otherwise CUDA, then Apple Metal Performance Shaders (MPS), then CPU. Models are cached in-process by model, device, precision, and optimization mode. | The implementation calls `encode(..., normalize_embeddings=False)`. It does not force L2 normalization. |
| `mlx` | `mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ` | Requires `mlx` and `mlx-lm`; intended for Apple silicon. First load can download model files. | LEANN caches the loaded MLX model/tokenizer in-process. There is no LEANN device override for this mode. | Mean-pools model outputs and returns float32 vectors; no explicit L2 normalization is applied. |
| `openai` | `text-embedding-3-small`, `text-embedding-3-large`, or an embedding model behind an OpenAI-compatible endpoint | Requires `openai` and `tiktoken`, a reachable endpoint, and a nonempty API-key value. Text is truncated to the discovered or registered token limit. | Computation is remote; local CUDA/MPS settings do not apply. | LEANN recognizes common OpenAI embedding models as normalized and defaults the backend distance metric to cosine when no metric was supplied. It does not expose an OpenAI `dimensions` request option in this path. |

The current embedding dispatcher also contains other modes, but this sub-skill's verified operating scope is the three modes above. Ollama embedding workflows should be handled through the package's current CLI/API documentation rather than inferred from LLM-provider behavior.

## Sentence-Transformers Controls

The direct embedding function supports adaptive batching and these environment overrides:

| Variable | Effect |
|---|---|
| `LEANN_EMBEDDING_DEVICE` | Explicit device such as `cpu`, `cuda`, `cuda:0`, or `mps`. An unavailable or incompatible value fails during model/tensor setup. |
| `LEANN_CPU_THREADS` | Positive CPU thread count; default is at most 8. |
| `LEANN_CUDA_BATCH_SIZE` | Positive adaptive CUDA batch size. |
| `LEANN_MPS_BATCH_SIZE` | Positive adaptive MPS batch size. |
| `LEANN_CUDA_AUTO_BATCH` | Set to `0`, `false`, or `no` to disable free-video-memory-based batch capping. |

`embedding_options.batch_size` overrides adaptive batching for sentence-transformers. CUDA out-of-memory errors are retried with successively halved batches. This retry does not fix an invalid device, missing package, or a model that cannot fit even at batch size 1.

Offline operation is possible only when all model/tokenizer artifacts and Python packages are already cached. LEANN's sentence-transformers loader deliberately falls back from local-only loading to a network-enabled load.

## OpenAI-Compatible Embedding Options

Pass options at build time so they are persisted for later query recomputation:

```python
from leann import LeannBuilder

builder = LeannBuilder(
    backend_name="hnsw",
    embedding_mode="openai",
    embedding_model="text-embedding-3-small",
    embedding_options={
        "base_url": "https://api.openai.com/v1",
        # Prefer OPENAI_API_KEY over an inline api_key.
    },
)
```

Resolution rules are:

- API key: explicit `embedding_options.api_key`, then `OPENAI_API_KEY`. The current embedding implementation rejects a missing/empty key before making a request.
- Base URL: explicit `embedding_options.base_url`, then `LEANN_OPENAI_BASE_URL`, `OPENAI_BASE_URL`, `LOCAL_OPENAI_BASE_URL`, then `https://api.openai.com/v1`.
- Even when a local OpenAI-compatible endpoint does not enforce authentication, LEANN still requires a nonempty key value. If the service documentation permits it, use a non-secret placeholder from the environment rather than persisting a production credential in index metadata.

OpenAI-compatible embedding calls leave the machine and can incur provider charges. LEANN batches requests and has endpoint-specific batch caps for Gemini-compatible and DashScope URLs. Do not assume that an LLM model identifier is also an embedding model.

## Task-Specific Embedding Templates

Task-specific models may require different document and query prefixes:

```python
embedding_options = {
    "build_prompt_template": "title: none | text: ",
    "query_prompt_template": "task: search result | query: ",
}
```

At build time, `build_prompt_template` takes precedence over legacy `prompt_template`. At query time, an explicit search-call `provider_options["prompt_template"]` takes precedence over stored `query_prompt_template`, which takes precedence over stored legacy `prompt_template`.

Only configure these for a model trained for asymmetric document/query prompts. Adding them to ordinary models such as `text-embedding-3-small`, `nomic-embed-text`, or `bge-base-en-v1.5` changes the embedding text and can degrade retrieval. Changing only the query prefix after build creates a semantic mismatch even when the vector width remains valid.

## Build-Time Versus Query-Time Compute

- Index building computes embeddings in-process (`use_server=False`).
- Query recomputation normally uses a backend embedding server (`recompute_embeddings=True`).
- `LeannSearcher` defaults to `enable_warmup=True`, `use_daemon=True`, and `daemon_ttl_seconds=900`.
- `LeannChat` constructs its searcher with warmup disabled by default, so its first query may pay startup/model-load cost.
- `use_daemon=True` allows a matching process to outlive a searcher and be adopted by another process. `use_daemon=False` creates an ephemeral server that cleanup terminates.

Daemon reuse is keyed by model, mode, provider options, passages metadata/signature, and distance metric. The manager starts at the requested port (normally 5557), but selects another free port if necessary. Managed callers receive the actual port; external code must not assume the starting port is the active one.

## MLX And Multimodal Scope

The repository's MLX demo is reference-only for this skill: it is Apple-silicon-specific and loads a model that may require a download. The safe reusable pattern is the `LeannBuilder(..., embedding_mode="mlx")` configuration above, not copying a script that writes a fixed local index.

ColQwen/ColPali multimodal PDF retrieval is also reference-only here. It has separate vision-model, PDF-conversion, application, and download requirements and belongs to [rag-applications](../../rag-applications/SKILL.md).
