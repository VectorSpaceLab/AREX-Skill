---
name: langchain-chatchat
description: "Route Langchain-Chatchat setup, RAG/API service, Python SDK, and
  LangChain adapter workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Langchain-Chatchat Repo Skill

Use this skill when a task involves Langchain-Chatchat: installing or initializing the package, configuring model providers and knowledge bases, operating the FastAPI/WebUI service, calling the RAG/OpenAI-compatible APIs, or using the Python SDK and LangChain adapter objects.

Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is current for a new checkout. Read [`references/package-overview.md`](references/package-overview.md) for the package layout, distribution/import names, and high-level workflow map. Use [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import/provider/service failures.

## Quick orientation

Langchain-Chatchat is an offline-friendly RAG and Agent application that wraps LLM/embedding providers behind a Chatchat API server and WebUI. The selected core surfaces are:

- `langchain-chatchat` distribution, importing `chatchat` and `langchain_chatchat`.
- `chatchat` CLI with `init`, `kb`, and `start` subcommands.
- FastAPI routes for chat, knowledge-base management, OpenAI-compatible `/v1/*`, tools, server state, and MCP connection management.
- A separate SDK import package spelled `open_chatcaht` in this repository.

Minimal public install and import smoke:

```bash
python -m pip install -U langchain-chatchat
python - <<'PY'
import chatchat, langchain_chatchat
print(chatchat.__version__)
print(langchain_chatchat.__all__)
PY
chatchat --help
```

If the task uses the SDK package, verify the import spelling explicitly:

```bash
python - <<'PY'
import open_chatcaht
from open_chatcaht.chatchat_api import ChatChat
print(ChatChat)
PY
```

## Route map

| User request shape | Read next |
| --- | --- |
| Install, initialize data/config, pick `CHATCHAT_ROOT`, run `chatchat init`, rebuild KB files, start API/WebUI, Docker/Xinference deployment, model-provider setup | [`sub-skills/server-setup-and-cli/SKILL.md`](sub-skills/server-setup-and-cli/SKILL.md) |
| Build or troubleshoot chat/RAG/API calls, `/chat/chat/completions`, `/knowledge_base/*`, tools, OpenAI-compatible `/v1/*`, vector stores, temp-file chat, search-engine RAG | [`sub-skills/knowledge-base-and-api/SKILL.md`](sub-skills/knowledge-base-and-api/SKILL.md) |
| Use the `open_chatcaht` SDK, `ChatChat` client, typed request models, streaming generators, `ChatPlatformAI`, `PlatformToolsRunnable`, MCP prompt utilities | [`sub-skills/python-sdk-and-adapters/SKILL.md`](sub-skills/python-sdk-and-adapters/SKILL.md) |
| Need a safe environment/package smoke from any current directory | Run [`scripts/chatchat_env_probe.py`](scripts/chatchat_env_probe.py) |

## Standard operating sequence

1. Decide installation mode: prefer `pip install -U langchain-chatchat` for users; use editable source installs only for repository development or when matching a specific checkout.
2. Set `CHATCHAT_ROOT` to the persistent data/config directory if the current working directory is not the intended data root.
3. Run `chatchat init` once to create data directories, copy samples, initialize the metadata database, and generate YAML templates.
4. Edit model-provider and KB YAML settings before vector rebuild or service startup. Chatchat expects an OpenAI-compatible provider such as Xinference, Ollama, LocalAI, FastChat, One API, OpenAI, or a custom OpenAI endpoint.
5. Run `chatchat kb -r` only after the embedding provider is reachable. Use `chatchat kb --help` for incremental/update/prune modes.
6. Start the service with `chatchat start --api`, `chatchat start --webui`, or `chatchat start -a` after provider and KB settings are valid.
7. For API/SDK tasks, confirm the API URL and model names before diagnosing request payloads.

## Verification helpers

- [`scripts/chatchat_env_probe.py`](scripts/chatchat_env_probe.py) checks importability, optional package presence, CLI availability, and selected package metadata without starting a server.
- [`sub-skills/server-setup-and-cli/scripts/chatchat_config_audit.py`](sub-skills/server-setup-and-cli/scripts/chatchat_config_audit.py) inspects an initialized `CHATCHAT_ROOT` for expected YAML/data directories and key settings.
- [`sub-skills/knowledge-base-and-api/scripts/api_surface_probe.py`](sub-skills/knowledge-base-and-api/scripts/api_surface_probe.py) lists FastAPI routes using a temp or initialized data root without binding a port.
- [`sub-skills/python-sdk-and-adapters/scripts/sdk_surface_probe.py`](sub-skills/python-sdk-and-adapters/scripts/sdk_surface_probe.py) lists SDK and adapter signatures without making HTTP calls.

Run each helper with `--help` first. None of these helpers downloads models, starts long-running services, calls external APIs, or mutates user data unless a documented option says it will create a temporary local root.

## Boundaries and cautions

- Do not treat a CPU import as proof that a live LLM/embedding provider, Docker runtime, GPU model server, or external vector DB is working. Those are service/provider checks.
- Do not install Chatchat and a heavy model-serving framework into the same environment by default; the project documentation warns that model providers such as Xinference can conflict with the Chatchat environment.
- Do not run vector rebuilds, live chat tests, Docker Compose, or AutoDL-style scripts unless the user has approved model downloads/services, data mutation, and hardware use.
- Do not copy old command names from stale docs. Current CLI help exposes `chatchat init`, `chatchat kb`, and `chatchat start`.
