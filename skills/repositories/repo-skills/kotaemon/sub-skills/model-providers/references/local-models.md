# Local Models

Kotaemon supports local/private model workflows through OpenAI-compatible servers, native Ollama chat wrappers, and `llama-cpp-python`/GGUF wrappers. Treat all local-model setup as side-effectful: starting servers, downloading models, pulling Ollama images, or loading GGUF weights can be slow and resource intensive.

## Recommended path: Ollama OpenAI-compatible endpoint

Use the OpenAI-compatible Ollama endpoint when you want both chat and embeddings to work with the same Kotaemon provider shape.

Typical `.env` values:

```shell
KH_OLLAMA_URL=http://localhost:11434/v1/
LOCAL_MODEL=llama3.1:8b
LOCAL_MODEL_EMBEDDINGS=nomic-embed-text
```

`flowsettings.py` creates:

- LLM `ollama` as `kotaemon.llms.ChatOpenAI` with `base_url=KH_OLLAMA_URL`, `api_key=ollama`, and `model=LOCAL_MODEL`.
- Embedding `ollama` as `kotaemon.embeddings.OpenAIEmbeddings` with `base_url=KH_OLLAMA_URL`, `api_key=ollama`, and `model=LOCAL_MODEL_EMBEDDINGS`.
- LLM `ollama-long-context` as `kotaemon.llms.LCOllamaChat` with `base_url=KH_OLLAMA_URL.replace("v1/", "")`, `model=LOCAL_MODEL`, and `num_ctx=8192`.

For Resources UI entries with vendor `ChatOpenAI` or `OpenAIEmbeddings`, keep the base URL ending in `/v1/`. For native `LCOllamaChat`, use the Ollama host URL without the `/v1/` suffix, such as `http://localhost:11434/` or `http://localhost:11434`.

## Docker host vs localhost

Inside Docker, `localhost` means the container, not the host machine. If Ollama or another local server runs on the host while Kotaemon runs in a container, use a host-reachable URL such as:

```shell
KH_OLLAMA_URL=http://host.docker.internal:11434/v1/
```

Use `localhost` only when the model server runs in the same network namespace as the Kotaemon process. The offline validator warns about `localhost` when `--docker` is passed.

## OpenAI-compatible local servers

Several local backends can expose OpenAI-compatible APIs. Configure them as `ChatOpenAI` and, when the backend supports embeddings, `OpenAIEmbeddings`.

| Backend | UI/provider type | Base URL shape | API key | Notes |
| --- | --- | --- | --- | --- |
| Ollama OpenAI-compatible | `ChatOpenAI`, `OpenAIEmbeddings` | `http://localhost:11434/v1/` | `ollama` | Recommended for local chat plus local embeddings |
| text-generation-webui | `ChatOpenAI`, sometimes `OpenAIEmbeddings` if embedding support is configured | `http://localhost:5000/v1/` | `dummy` or backend-specific | Needs text-generation-webui API mode and embedding dependencies for embeddings |
| llama-cpp-python OpenAI server | `ChatOpenAI` | `http://localhost:8000/v1/` | `dummy` | LLM server only in Kotaemon docs; use separate embedding model |
| Groq/Mistral-compatible hosted APIs | `ChatOpenAI` | provider-specific `/openai/v1` or `/v1` | real key | These are not local, but they share OpenAI-compatible specs |

The validator checks URL syntax and likely suffix mistakes, but it does not open sockets or send requests.

## GGUF with `llama-cpp-python`

Kotaemon includes `LlamaCppChat` for direct in-process GGUF loading. The class requires either:

- `model_path` pointing to a local GGUF file, plus `chat_format`; or
- `repo_id` and `filename`, plus `chat_format`.

Important fields:

| Field | Meaning |
| --- | --- |
| `model_path` | Path to a local GGUF file |
| `repo_id` / `filename` | Hugging Face model repo and file selector for lazy loading |
| `chat_format` | Required format understood by `llama_cpp.llama_chat_format` |
| `n_ctx` | Context size, default in code is `512` unless changed |
| `n_gpu_layers` | `0` CPU-only; `-1` offload all possible layers |
| `vocab_only` | Useful for import/init tests without full generation |

Common failures:

- `llama-cpp-python is not installed`: install the optional package in the active Kotaemon environment.
- Missing `model_path` and missing `repo_id`/`filename`: the wrapper cannot locate weights.
- Missing `chat_format`: the wrapper rejects initialization.
- File path points to a nonexistent or non-GGUF file: fix the path before starting the app.
- Model too large for available RAM/VRAM: choose a smaller quantized file or reduce GPU offload.

## Local embeddings

Local RAG needs an embedding model as well as a chat model. Options include:

- Ollama embedding model through `OpenAIEmbeddings` with `/v1/` base URL and `LOCAL_MODEL_EMBEDDINGS`, commonly `nomic-embed-text`.
- `FastEmbedEmbeddings` for a local embedding model such as `BAAI/bge-base-en-v1.5`, if `fastembed` is installed.
- `LCHuggingFaceEmbeddings` with a sentence-transformers model, if the required packages and model cache are available.
- TEI endpoint embeddings when a text-embeddings-inference server is available.

When configuring a File Collection, choose an embedding model explicitly in collection/index settings. A valid chat model alone is not enough to index documents.

## Local reranking and LLM scoring

Kotaemon retrieval settings can use reranking models and an LLM scoring model. Local models are safer for privacy but can be slow under parallel scoring. Setup code sets `use_llm_reranking` to `False` for Ollama by default. If answers are slow or local models time out, disable LLM reranking first, then tune batch/concurrency or switch to a lighter reranker.

## Safe offline checks

Use:

```bash
python scripts/check_provider_env.py --env-file .env --select local --docker
```

The script checks `KH_OLLAMA_URL`, local model names, OpenAI-compatible suffixes, Docker localhost warnings, and GGUF path existence when `LOCAL_MODEL` or `LOCAL_MODEL_PATH` looks like a file path. It never starts Ollama or loads a model.
