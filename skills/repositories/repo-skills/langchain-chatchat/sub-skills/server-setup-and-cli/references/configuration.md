# Configuration

## `CHATCHAT_ROOT`

Langchain-Chatchat stores mutable application state under `CHATCHAT_ROOT`. If the variable is unset, the package resolves the current working directory as the root. Always make the root explicit for repeatable deployments.

```bash
export CHATCHAT_ROOT=/path/to/chatchat-data
chatchat init
```

Expected initialized layout includes:

| Item | Purpose |
| --- | --- |
| `basic_settings.yaml` | Data paths, DB URI, API/WebUI host/port, logging and HTTP timeout settings. |
| `kb_settings.yaml` | Default knowledge base, vector-store type, chunking, search thresholds, OCR/splitter settings. |
| `model_settings.yaml` | Model platform endpoints, model names, API keys/proxies, default LLM/embedding/rerank/media models. |
| `tool_settings.yaml` | Tool enablement and per-tool configuration. |
| `prompt_settings.yaml` | Prompt templates for model/chat/RAG/tool workflows. |
| `data/knowledge_base/` | Knowledge-base content and metadata DB by default. |
| `data/logs/` | Runtime logs. |
| `data/media/` and `data/temp/` | Generated media and temporary upload/OpenAI-file state. |

Run `scripts/chatchat_config_audit.py --chatchat-root /path/to/chatchat-data` after initialization to catch missing files and summarize key settings.

## Important settings groups

### `basic_settings.yaml`

Key fields:

- `KB_ROOT_PATH`: default knowledge-base storage path.
- `DB_ROOT_PATH` and `SQLALCHEMY_DATABASE_URI`: metadata database location/URI.
- `API_SERVER`: `host`, `port`, `public_host`, and `public_port` for the FastAPI service.
- `WEBUI_SERVER`: `host` and `port` for Streamlit WebUI.
- `HTTPX_DEFAULT_TIMEOUT`: increase when provider requests are slow.
- `OPEN_CROSS_DOMAIN`: enable CORS only when needed.

### `model_settings.yaml`

Key fields:

- `DEFAULT_LLM_MODEL` and `DEFAULT_EMBEDDING_MODEL`: names must match provider-visible model names.
- `MODEL_PLATFORMS`: list of provider configs. Each platform includes `platform_name`, `platform_type`, `api_base_url`, `api_key`, optional proxy, concurrency, and model lists or auto-detect settings.
- `LLM_MODEL_CONFIG`: per-role model config for preprocess, LLM, action/tool, postprocess, and image generation.
- `SUPPORT_AGENT_MODELS`: model names expected to work well with Agent/tool workflows.

### `kb_settings.yaml`

Key fields:

- `DEFAULT_KNOWLEDGE_BASE`: usually `samples` after initialization.
- `DEFAULT_VS_TYPE`: default `faiss`; alternatives include `milvus`, `zilliz`, `pg`, `es`, `relyt`, and `chromadb` when services/dependencies are configured.
- `CHUNK_SIZE`, `OVERLAP_SIZE`, `TEXT_SPLITTER_NAME`, `ZH_TITLE_ENHANCE`: affect indexing and retrieval.
- `VECTOR_SEARCH_TOP_K` and `SCORE_THRESHOLD`: retrieval breadth and cutoff.
- `kbs_config`: per-vector-store service settings.

## Safe update procedure

1. Stop the API/WebUI process before editing host/port, DB, vector-store, or provider settings.
2. Backup existing YAML and knowledge-base data before package upgrades or destructive KB commands.
3. Run `chatchat init` after package upgrades when templates changed, then reapply custom settings.
4. Validate model provider names before vector rebuilds.
5. Use the configuration audit helper and then API/SDK probes.

## Common pitfalls

- Running `chatchat init` from different directories without setting `CHATCHAT_ROOT` creates multiple independent data roots.
- A public API URL generated from `public_host/public_port` can be wrong if reverse proxy or cloud NAT settings are not configured.
- Vector-store service configs in `kb_settings.yaml` do not prove the service is running.
- Changing chunking or embedding model requires vector rebuild to affect existing documents.
