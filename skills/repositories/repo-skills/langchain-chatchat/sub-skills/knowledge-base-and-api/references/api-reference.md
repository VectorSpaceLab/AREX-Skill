# API Reference

## When to read

Read this to choose the correct Langchain-Chatchat route family. Route names come from the installed FastAPI app and current source route registrations.

## Service roots

- API server default host/port is configured by `basic_settings.yaml` and commonly uses `http://127.0.0.1:7861`.
- The root path redirects to API docs (`/docs`) when the FastAPI server is running.
- WebUI is separate and commonly uses port `8501`.

## Chat routes

| Route | Method | Use |
| --- | --- | --- |
| `/chat/chat/completions` | POST | Unified OpenAI-compatible chat entry. It can do pure LLM chat, agent/tool chat, or manual tool calls depending on `tools`, `tool_choice`, and extra fields. |
| `/chat/kb_chat` | POST | Specific knowledge-base chat helper used by SDK legacy methods. |
| `/chat/file_chat` | POST | Specific file-chat helper used by SDK legacy methods. |
| `/chat/feedback` | POST | Store feedback for a chat message. |

`/chat/chat/completions` accepts OpenAI-style `model`, `messages`, `stream`, `temperature`, `max_tokens`, `tools`, and `tool_choice`. Chatchat adds behavior through model-extra fields such as conversation metadata, tool config, and manual `tool_input`.

## Knowledge-base routes

| Route | Method | Use |
| --- | --- | --- |
| `/knowledge_base/{mode}/{param}/chat/completions` | POST | OpenAI-compatible RAG route. `mode` is `local_kb`, `temp_kb`, or `search_engine`; `param` is KB name, temp knowledge id, or search engine name. |
| `/knowledge_base/list_knowledge_bases` | GET | List KB names. |
| `/knowledge_base/create_knowledge_base` | POST | Create a KB. |
| `/knowledge_base/delete_knowledge_base` | POST | Delete a KB. |
| `/knowledge_base/list_files` | GET | List files in a KB. |
| `/knowledge_base/search_docs` | POST | Search documents in a KB. |
| `/knowledge_base/upload_docs` | POST | Upload files to KB and optionally vectorize. |
| `/knowledge_base/delete_docs` | POST | Delete KB docs. |
| `/knowledge_base/update_info` | POST | Update KB description/info. |
| `/knowledge_base/update_docs` | POST | Update existing KB docs. |
| `/knowledge_base/download_doc` | GET | Download or preview a KB file. |
| `/knowledge_base/recreate_vector_store` | POST | Rebuild vector store with streaming progress. |
| `/knowledge_base/upload_temp_docs` | POST | Upload docs to a temporary KB for file chat. |
| `/knowledge_base/search_temp_docs` | POST | Search temporary KB docs. |

Summary routes under `/knowledge_base/kb_summary_api/` include `summary_file_to_vector_store`, `summary_doc_ids_to_vector_store`, and `recreate_summary_vector_store`.

## Tool and server routes

| Route | Method | Use |
| --- | --- | --- |
| `/tools` | GET | List all registered tools, argument schemas, and tool config. |
| `/tools/call` | POST | Invoke a named tool with `tool_input`. |
| `/server/configs` | POST | Get raw server configs. |
| `/server/get_prompt_template` | POST | Get a prompt template by type and name. |

## OpenAI-compatible `/v1` routes

| Route | Method | Use |
| --- | --- | --- |
| `/v1/models` | GET | Aggregate provider model list. Depends on provider config/reachability. |
| `/v1/chat/completions` | POST | Provider-backed chat completions through configured model platforms. |
| `/v1/completions` | POST | Provider-backed completions compatibility route. |
| `/v1/embeddings` | POST | Provider-backed embeddings. |
| `/v1/images/generations`, `/v1/images/variations`, `/v1/images/edit` | POST | Image routes if provider/model supports them. |
| `/v1/audio/translations`, `/v1/audio/transcriptions`, `/v1/audio/speech` | POST | Marked deprecated/limited in source for some audio surfaces. |
| `/v1/files`, `/v1/files/{file_id}`, `/v1/files/{file_id}/content` | GET/POST/DELETE | File storage compatibility using Chatchat temp directory. |

## MCP routes

Installed route inspection also found `/api/v1/mcp_connections/*` routes for MCP connection profiles, listing, search, status, and enabled connection management. Use SDK/adapter guidance for MCP prompt/tool client behavior and treat live MCP servers as external services.

## Route probe

Run:

```bash
python sub-skills/knowledge-base-and-api/scripts/api_surface_probe.py --json
```

By default the probe creates a temporary initialized data root so route import can access the metadata DB. It does not bind a port or call providers.
