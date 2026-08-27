---
name: knowledge-base-and-api
description: "Use Langchain-Chatchat FastAPI, OpenAI-compatible chat,
  knowledge-base RAG, file RAG, tools, and vector-store workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Knowledge Base and API

Use this sub-skill when a task asks for Langchain-Chatchat HTTP APIs, RAG modes, knowledge-base document operations, file/temp KB chat, search-engine chat, tools, OpenAI-compatible endpoints, route discovery, or vector-store behavior.

## Read first

- [`references/api-reference.md`](references/api-reference.md) maps verified route families and request patterns.
- [`references/rag-workflows.md`](references/rag-workflows.md) covers local KB, temp-file, search-engine, direct retrieval, and tool-choice workflows.
- [`references/vector-store-and-data-formats.md`](references/vector-store-and-data-formats.md) covers document/vector-store settings and supported backends.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers route, provider, streaming, KB, and vector-store failures.
- Run [`scripts/api_surface_probe.py`](scripts/api_surface_probe.py) to list the installed API routes without binding a service port.

## Preconditions

1. `langchain-chatchat` is installed and imports.
2. `CHATCHAT_ROOT` has been initialized with `chatchat init`.
3. API server is running for live HTTP calls: `chatchat start --api` or `chatchat start -a`.
4. Model provider settings are valid for any route that invokes LLMs or embeddings.
5. For vector rebuilds or retrieval over indexed docs, the embedding model is reachable.

If any precondition is false, route setup/config work to [`../server-setup-and-cli/SKILL.md`](../server-setup-and-cli/SKILL.md).

## Route families

| Task | Route family |
| --- | --- |
| Unified chat, pure LLM chat, agent/tool chat | `/chat/chat/completions` |
| Legacy/specific KB and file chat helpers | `/chat/kb_chat`, `/chat/file_chat` |
| OpenAI-compatible RAG by mode | `/knowledge_base/{local_kb|temp_kb|search_engine}/{param}/chat/completions` |
| KB CRUD and document operations | `/knowledge_base/list_knowledge_bases`, `/create_knowledge_base`, `/delete_knowledge_base`, `/list_files`, `/upload_docs`, `/delete_docs`, `/update_docs`, `/search_docs`, `/download_doc`, `/recreate_vector_store` |
| Temp docs | `/knowledge_base/upload_temp_docs`, `/search_temp_docs` |
| Summary routes | `/knowledge_base/kb_summary_api/*` |
| Tool registry/calls | `/tools`, `/tools/call` |
| OpenAI-compatible provider proxy | `/v1/models`, `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, `/v1/images/*`, `/v1/audio/*`, `/v1/files*` |
| Server state/prompts | `/server/configs`, `/server/get_prompt_template` |
| MCP connections | `/api/v1/mcp_connections/*` |

## Common API patterns

### Direct retrieval from local KB without LLM generation

Use OpenAI-compatible RAG route plus `return_direct=True` in `extra_body` when the task only needs retrieved documents.

```python
from openai import Client

client = Client(base_url="http://127.0.0.1:7861/knowledge_base/local_kb/samples", api_key="EMPTY")
resp = client.chat.completions.create(
    model="configured-llm-name",
    messages=[{"role": "user", "content": "How do I ask high-quality questions?"}],
    stream=True,
    extra_body={"top_k": 3, "score_threshold": 2.0, "return_direct": True},
)
for chunk in resp:
    print(chunk)
```

### Tool-assisted chat

Fetch `/tools` first. If the model can choose tools, pass `tools`. If it cannot reliably infer arguments, pass `tool_choice` and `extra_body.tool_input` to make the tool call explicit.

### File/temp KB chat

Upload temporary docs first, capture `knowledge_id`, then use `/knowledge_base/temp_kb/{knowledge_id}/chat/completions` or the SDK's temp-doc methods.

## Verification boundaries

- `api_surface_probe.py` verifies installed route registration only; it does not prove the API server, provider, or models are running.
- A `return_direct=True` RAG route still needs retrieval inputs and often an initialized vector store, but it avoids LLM answer generation.
- Live `/v1/models` depends on provider configuration; failures there are often provider setup failures, not route-definition failures.
