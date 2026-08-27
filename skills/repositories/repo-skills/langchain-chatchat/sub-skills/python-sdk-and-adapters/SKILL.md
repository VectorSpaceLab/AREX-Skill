---
name: python-sdk-and-adapters
description: "Use Langchain-Chatchat's open_chatcaht SDK clients, typed API
  wrappers, streaming helpers, and langchain_chatchat adapter classes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Python SDK and Adapters

Use this sub-skill when a task asks for the Langchain-Chatchat Python SDK, `open_chatcaht` import spelling, `ChatChat` client, category clients, typed parameters, streaming helper behavior, OpenAI-compatible SDK calls, or LangChain adapter classes such as `ChatPlatformAI` and `PlatformToolsRunnable`.

## Read first

- [`references/sdk-reference.md`](references/sdk-reference.md) maps SDK classes, constructor defaults, method families, and live-service requirements.
- [`references/langchain-adapters.md`](references/langchain-adapters.md) covers `ChatPlatformAI`, `PlatformToolsRunnable`, and MCP prompt/tool utility boundaries.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers SDK import spelling, base URL, streaming, and service errors.
- Run [`scripts/sdk_surface_probe.py`](scripts/sdk_surface_probe.py) to inspect installed SDK/adapters without making HTTP calls.

## Import and constructor facts

The SDK import package is spelled `open_chatcaht` in this repo:

```python
from open_chatcaht.chatchat_api import ChatChat

client = ChatChat(base_url="http://127.0.0.1:7861/", timeout=60)
```

`ChatChat` constructs category clients:

- `client.knowledge` (`KbClient`)
- `client.tool` (`ToolClient`)
- `client.server` (`ServerClient`)
- `client.chat` (`ChatClient`)
- `client.openai_adapter` (`StandardOpenaiClient`)

All of these wrap HTTP requests. Importing or inspecting methods is safe; calling methods requires a running Chatchat API server and often model/provider availability.

## Base URL and environment variables

`ApiClient` defaults to the package constant API base URL (`http://127.0.0.1:7861/` in inspected source). Environment variables used by the API client include:

- `CHATCHAT_API_BASE`
- `CHATCHAT_CLIENT_TIME_OUT`
- `CHATCHAT_CLIENT_DEFAULT_RETRY`
- `CHATCHAT_CLIENT_DEFAULT_RETRY_INTERVAL`

Prefer passing `base_url=` explicitly in reusable code so tasks do not depend on ambient environment variables.

## SDK workflow map

| Task | SDK surface | Notes |
| --- | --- | --- |
| List/create/delete KBs, upload/search docs, temp docs | `client.knowledge` | Mutates or reads KB state; upload/rebuild requires embedding provider. |
| Tool list/call | `client.tool` | Fetch tool schemas before calling; tool execution may need external services. |
| Server configs/prompts | `client.server` | Good first live API smoke after server starts. |
| KB/file chat and feedback | `client.chat` | Streaming methods return generators over chunks. |
| OpenAI-compatible models/chat/embeddings/files/media | `client.openai_adapter` | Provider-backed; model names must match Chatchat settings. |
| LangChain model adapter | `langchain_chatchat.ChatPlatformAI` | Use when integrating Chatchat provider config into LangChain chat model flows. |
| Agent/tool runnable | `langchain_chatchat.PlatformToolsRunnable` | Advanced agent/tool integration; requires an `AgentExecutor` and callback wiring. |

## Safe development pattern

1. Run `scripts/sdk_surface_probe.py --json` to verify imports and signatures.
2. Start Chatchat API separately if live calls are required.
3. Use `client.server.get_server_configs()` or a simple `/tools` list as the first live call.
4. For streaming methods, iterate the generator and handle error dictionaries as well as chunks.
5. For KB mutations, isolate a test KB or temporary docs; do not call delete/prune/update methods against production KBs without approval.

## Boundaries with sibling sub-skills

- Use [`../server-setup-and-cli/SKILL.md`](../server-setup-and-cli/SKILL.md) for installing packages, starting API/WebUI, setting `CHATCHAT_ROOT`, and provider model names.
- Use [`../knowledge-base-and-api/SKILL.md`](../knowledge-base-and-api/SKILL.md) for raw HTTP route paths, request bodies, vector-store semantics, and RAG debugging.
