# Package Overview

## When to read

Read this for the repository's package layout, public entry points, and the relationship between setup, API/RAG workflows, and SDK/adapters.

## Public surfaces

| Surface | Verified facts | Use for |
| --- | --- | --- |
| `langchain-chatchat` distribution | Version `0.3.1.3`; Python `>=3.10,<3.12`; console script `chatchat` | Installed package, CLI, FastAPI service, WebUI, settings, KB/RAG workflows |
| `chatchat` import package | `chatchat.__version__ == "0.3.1.3"` | CLI implementation, settings, server startup, knowledge-base APIs |
| `langchain_chatchat` import package | Exports `ChatPlatformAI` and `PlatformToolsRunnable` | LangChain adapter and tool/agent integration surfaces |
| `open_chatcaht` import package | Import spelling is `open_chatcaht` in the inspected repo; editable metadata reports `0.0.0` | SDK clients for Chatchat API categories |
| `chatchat` CLI | Commands: `init`, `kb`, `start` | Data/config initialization, KB maintenance, service startup |
| FastAPI application | Route families under `/chat`, `/knowledge_base`, `/tools`, `/v1`, `/server`, and `/api/v1/mcp_connections` | HTTP API, OpenAI-compatible calls, tool/MCP surfaces |

## Architecture in one pass

1. **Model providers are external.** Chatchat does not directly load all models in the core `chatchat` CLI path; it configures provider endpoints such as Xinference, Ollama, LocalAI, FastChat, One API, OpenAI, or custom OpenAI-compatible endpoints.
2. **`CHATCHAT_ROOT` owns mutable state.** Data, logs, media, temp files, knowledge-base content, the metadata database, and generated YAML templates live under the selected root.
3. **`chatchat init` bootstraps state.** It creates directories, copies sample KB files, creates database tables, and writes YAML templates. With `--recreate-kb`, it also rebuilds vectors and therefore requires a reachable embedding model.
4. **`chatchat kb` maintains knowledge bases.** It can recreate vectors, update indexed files, incrementally add files, prune stale DB/file entries, create tables, clear tables, or import a sqlite database.
5. **`chatchat start` starts API and/or WebUI.** API default port is `7861`; WebUI default port is `8501`. The service still needs provider and KB settings to answer model/RAG requests.
6. **APIs and SDK mirror the service.** The FastAPI routes implement chat, RAG, tool, OpenAI-compatible, server-state, and MCP surfaces. The `open_chatcaht` SDK wraps the same API families.

## Dependency and backend notes

- CPU is enough to inspect and validate the selected package, CLI, route, settings, and SDK surfaces.
- Full chat generation, embedding/vector rebuilds, and tool/agent workflows need a reachable LLM/embedding provider and may need provider-specific hardware.
- The project documentation warns against installing Chatchat and a heavy provider such as Xinference into the same Python environment by default; use separate environments or containers unless the user explicitly accepts conflicts.
- FAISS CPU is the default vector-store path in package dependencies. Milvus, Zilliz, PostgreSQL/Relyt, Elasticsearch, and Chroma require separate service/config validation.
- Docker deployment depends on Docker Compose, external images, and usually NVIDIA Container Toolkit when using GPU-backed Xinference.

## Skill map

- Setup/deployment/config is owned by [`../sub-skills/server-setup-and-cli/SKILL.md`](../sub-skills/server-setup-and-cli/SKILL.md).
- API/RAG/vector-store request design is owned by [`../sub-skills/knowledge-base-and-api/SKILL.md`](../sub-skills/knowledge-base-and-api/SKILL.md).
- SDK and LangChain adapter usage is owned by [`../sub-skills/python-sdk-and-adapters/SKILL.md`](../sub-skills/python-sdk-and-adapters/SKILL.md).

## Safe probes

Use [`../scripts/chatchat_env_probe.py`](../scripts/chatchat_env_probe.py) first when you only need to know whether the package, imports, and CLI are available. Use sub-skill probes for configuration, API routes, or SDK signatures.
