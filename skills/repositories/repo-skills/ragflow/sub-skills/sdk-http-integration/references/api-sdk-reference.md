# RAGFlow API and SDK Reference

RAGFlow 0.26.1 exposes public HTTP APIs under `/api/v1` and a Python SDK published as `ragflow-sdk`. The SDK imports as `ragflow_sdk` and centers on `RAGFlow(api_key, base_url, version="v1")`; the constructor appends `/api/{version}` to `base_url`, so pass only the server origin, for example `http://localhost:9380`, not a URL already ending in `/api/v1`.

## Client selection

- Use raw HTTP when integrating from shell, JavaScript, non-Python services, or when the exact endpoint/payload must be controlled.
- Use `ragflow-sdk` when writing Python automation around datasets, documents, chunks, retrieval, chats, agents, sessions, and memories.
- Use an OpenAI client only for OpenAI-compatible chat completions, where the base URL includes the chat assistant ID.
- Use `/api/v1/system/healthz` for service readiness checks; it does not require API-key authorization.

## Endpoint families

| Family | Public endpoints | Notes |
| --- | --- | --- |
| System | `GET /api/v1/system/healthz` | Returns dependency health for database, Redis, document engine, storage, and overall status. |
| OpenAI-compatible chat | `POST /api/v1/openai/{chat_id}/chat/completions` | OpenAI request/response shape for a RAGFlow chat assistant. Supports `extra_body.reference` and metadata filters. |
| OpenAI-compatible agent | `POST /api/v1/agents_openai/{agent_id}/chat/completions` | OpenAI-style agent completion endpoint. |
| Datasets | `POST /api/v1/datasets`, `GET /api/v1/datasets`, `PUT /api/v1/datasets/{dataset_id}`, `DELETE /api/v1/datasets` | `DELETE` expects a JSON body with `ids` or `delete_all`. |
| Documents | `POST /api/v1/datasets/{dataset_id}/documents`, `GET/PUT /api/v1/datasets/{dataset_id}/documents/{document_id}`, `GET/DELETE /api/v1/datasets/{dataset_id}/documents` | Upload local files, crawl web URLs, or create empty documents. `DELETE` expects a JSON body. |
| Parsing | `POST /api/v1/datasets/{dataset_id}/chunks`, `DELETE /api/v1/datasets/{dataset_id}/chunks` | Starts or stops parsing for `document_ids`. |
| Chunks | `POST/GET/PATCH/DELETE /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks`, `GET/PATCH /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}` | Chunk deletion uses `chunk_ids`, not `ids`. Chunk update uses `PATCH`. |
| Retrieval | `POST /api/v1/retrieval` | Searches chunks across `dataset_ids` and/or `document_ids`; supports hybrid weights, reranker, keyword, metadata, knowledge graph, and table-of-contents options. |
| Chats | `POST/GET/DELETE /api/v1/chats`, `GET/PATCH/DELETE /api/v1/chats/{chat_id}` | `PATCH` deep-merges nested chat settings such as `llm_setting` and `prompt_config`. |
| Chat sessions | `POST/GET/DELETE /api/v1/chats/{chat_id}/sessions`, `GET/PATCH /api/v1/chats/{chat_id}/sessions/{session_id}` | `PATCH` replaces the deprecated `PUT` update. |
| Native chat completions | `POST /api/v1/chat/completions` | Supports default model, chat assistant, and existing-session modes. Streaming ends with a final `data: {"code": 0, "data": true}` chunk. |
| Agents | `GET /api/v1/agents`, `GET/PUT/DELETE /api/v1/agents/{agent_id}`, `POST /api/v1/agents`, `POST /api/v1/agents/chat/completions` | Native agent completions support inputs, traces, streaming events, and OpenAI-compatible mode. |
| Memories/messages | `POST/GET/PUT/DELETE /api/v1/memories`, message add/search/list/content/status endpoints | The SDK exposes the common memory/message operations directly. |
| File management | `POST/GET/DELETE /api/v1/files`, move/link/parent/ancestor endpoints | Use when managing personal files outside a dataset-specific document upload. |

## Raw HTTP patterns

Always send API-key protected calls with:

```http
Authorization: Bearer <RAGFLOW_API_KEY>
Content-Type: application/json
```

Health check without API key:

```bash
curl --request GET \
  --url "${RAGFLOW_BASE_URL}/api/v1/system/healthz" \
  --header 'Content-Type: application/json'
```

Create and list datasets:

```bash
curl --request POST \
  --url "${RAGFLOW_BASE_URL}/api/v1/datasets" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  --data '{"name":"kb_1","chunk_method":"naive"}'

curl --request GET \
  --url "${RAGFLOW_BASE_URL}/api/v1/datasets?page=1&page_size=30" \
  --header "Authorization: Bearer ${RAGFLOW_API_KEY}"
```

Upload and parse documents:

```bash
curl --request POST \
  --url "${RAGFLOW_BASE_URL}/api/v1/datasets/${DATASET_ID}/documents" \
  --header "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  --form "file=@./notes.txt"

curl --request POST \
  --url "${RAGFLOW_BASE_URL}/api/v1/datasets/${DATASET_ID}/chunks" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  --data '{"document_ids":["'"${DOCUMENT_ID}"'"]}'
```

Retrieve chunks:

```bash
curl --request POST \
  --url "${RAGFLOW_BASE_URL}/api/v1/retrieval" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  --data '{
    "question":"What does the policy say about renewals?",
    "dataset_ids":["'"${DATASET_ID}"'"],
    "page":1,
    "page_size":10,
    "similarity_threshold":0.2,
    "vector_similarity_weight":0.3,
    "top_k":1024,
    "metadata_condition":{
      "logic":"and",
      "conditions":[{"name":"author","comparison_operator":"is","value":"alice"}]
    }
  }'
```

Delete with bodies, not query strings:

```bash
curl --request DELETE \
  --url "${RAGFLOW_BASE_URL}/api/v1/datasets/${DATASET_ID}/documents/${DOCUMENT_ID}/chunks" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  --data '{"chunk_ids":["'"${CHUNK_ID}"'"],"delete_all":false}'
```

## Python SDK entrypoints

Install the client package with `pip install ragflow-sdk`, then import from `ragflow_sdk`:

```python
from ragflow_sdk import RAGFlow

rag = RAGFlow(api_key="<RAGFLOW_API_KEY>", base_url="http://localhost:9380")
```

Important constructor behavior:

- `base_url="http://localhost:9380"` produces SDK request URLs such as `http://localhost:9380/api/v1/datasets`.
- `base_url="http://localhost:9380/api/v1"` is wrong for the SDK because it produces duplicated API prefixes.
- `version="v1"` is the default and matches RAGFlow 0.26.1 public endpoints.

## SDK object and method summary

| Object | Creation/access | Public methods and semantics |
| --- | --- | --- |
| `RAGFlow` | `RAGFlow(api_key, base_url, version="v1")` | `create_dataset`, `delete_datasets`, `get_dataset`, `list_datasets`, `create_chat`, `delete_chats`, `get_chat`, `list_chats`, `retrieve`, `list_agents`, `get_agent`, `create_agent`, `update_agent`, `delete_agent`, `create_memory`, `list_memory`, `delete_memory`, `add_message`, `search_message`, `get_recent_messages`. |
| `DataSet` | Returned from dataset methods | `update`, `upload_documents`, `list_documents`, `delete_documents`, `async_parse_documents`, `parse_documents`, `async_cancel_parse_documents`, `get_auto_metadata`, `update_auto_metadata`. |
| `Document` | Returned from dataset document methods | `update`, `download`, `list_chunks`, `add_chunk`, `delete_chunks`. |
| `Chunk` | Returned from retrieval or document chunk methods | `update`; chunk instances also expose IDs, content, scores, document/dataset fields when present in the response. |
| `Chat` | Returned from chat methods | `update`, `create_session`, `list_sessions`, `delete_sessions`. |
| `Session` | Returned from chat/agent session methods | `ask(question, stream=False, **kwargs)`, `update`. Chat sessions call chat completion endpoints; agent sessions call agent completion endpoints. |
| `Agent` | Returned from agent methods | `create_session`, `list_sessions`, `delete_sessions`; root `RAGFlow` manages agent CRUD. |
| `Memory` | Returned from memory methods | `update`, `get_config`, `list_memory_messages`, `forget_message`, `update_message_status`, `get_message_content`. |

Common SDK workflow:

```python
from ragflow_sdk import RAGFlow

rag = RAGFlow(api_key="<RAGFLOW_API_KEY>", base_url="http://localhost:9380")

dataset = rag.create_dataset(name="kb_1", chunk_method="naive")
documents = dataset.upload_documents([
    {"display_name": "notes.txt", "blob": b"RAGFlow can retrieve cited chunks."}
])
dataset.async_parse_documents([documents[0].id])

chunks = rag.retrieve(
    question="What can RAGFlow retrieve?",
    dataset_ids=[dataset.id],
    page=1,
    page_size=5,
)

assistant = rag.create_chat("support-bot", dataset_ids=[dataset.id])
session = assistant.create_session("smoke session")
answer = session.ask("Summarize the uploaded notes", stream=False)
print(answer.content)
print(answer.reference)
```

## OpenAI-compatible chat completions

OpenAI-compatible chat uses a special base URL that ends in `/api/v1/openai/{chat_id}/chat` and then the OpenAI client appends `/completions`:

```python
from openai import OpenAI

client = OpenAI(
    api_key="<RAGFLOW_API_KEY>",
    base_url="http://localhost:9380/api/v1/openai/<CHAT_ID>/chat",
)

response = client.chat.completions.create(
    model="model",
    messages=[{"role": "user", "content": "What is in the knowledge base?"}],
    stream=False,
    extra_body={
        "reference": True,
        "reference_metadata": {"include": True, "fields": ["author", "source"]},
    },
)
print(response.choices[0].message.content)
```

Notes:

- Use `model="model"` when you want RAGFlow to use the chat assistant's configured model; use a real `model_name@provider` value only when intentionally overriding.
- The last message must be a user message. If it is not, RAGFlow can return a `code: 102` payload such as “The last content of this conversation is not from user.”
- With `extra_body.reference=true`, streaming responses may place references on the final streamed delta (`choices[0].delta.reference`), while non-streaming responses may place references on `choices[0].message.reference`.
- With `extra_body.reference_metadata.include=true`, reference chunks can include `document_metadata`.
- For migration, replace deprecated `/api/v1/chats_openai/{chat_id}/chat/completions` with `/api/v1/openai/{chat_id}/chat/completions`.

## Native chat and agent streaming

Native chat completion endpoint:

```bash
curl --request POST \
  --url "${RAGFLOW_BASE_URL}/api/v1/chat/completions" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer ${RAGFLOW_API_KEY}" \
  --data '{
    "chat_id":"'"${CHAT_ID}"'",
    "session_id":"'"${SESSION_ID}"'",
    "stream":true,
    "messages":[{"role":"user","content":"Hello"}]
  }'
```

Streaming client handling rules:

- Treat each Server-Sent Event `data:` line as an independent JSON payload unless it is `[DONE]`.
- For native chat streams, expect a terminal `data: {"code": 0, "data": true}` chunk.
- For native agent streams, handle `message`, `message_end`, and `node_finished` events; the stream terminates with `[DONE]`.
- Do not assume every streamed chunk has references. References may be empty, absent, or only present in a final event.
- If requesting trace output from agents, set `return_trace=true` and inspect component trace fields in the response.

## Deprecated alias migration map

Prefer current endpoints when adapting older scripts:

| Deprecated | Current replacement |
| --- | --- |
| `POST /api/v1/chats_openai/{chat_id}/chat/completions` | `POST /api/v1/openai/{chat_id}/chat/completions` |
| `PUT /api/v1/chats/{chat_id}/sessions/{session_id}` | `PATCH /api/v1/chats/{chat_id}/sessions/{session_id}` |
| `POST /api/v1/chats/{chat_id}/completions` | `POST /api/v1/chat/completions` |
| `POST /api/v1/sessions/related_questions` | `POST /api/v1/chat/recommandation` |
| `PUT /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}` | `PATCH /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}` |
| `GET /v1/system/healthz` | `GET /api/v1/system/healthz` |
| `POST /api/v1/file/upload` or `/api/v1/file/create` | `POST /api/v1/files` |
| `GET /api/v1/file/list` | `GET /api/v1/files` |
| `POST /api/v1/file/rm` | `DELETE /api/v1/files` |
| `POST /api/v1/file/rename` or `/api/v1/file/mv` | `POST /api/v1/files/move` |
| `POST /api/v1/file/convert` | `POST /api/v1/files/link-to-datasets` |

## ID and payload guardrails

- `dataset_id` identifies a dataset/knowledge base and appears under `/datasets/{dataset_id}`.
- `document_id` identifies a document within a dataset and appears under `/datasets/{dataset_id}/documents/{document_id}`.
- `chunk_id` identifies a chunk within a document; delete chunk bodies use `chunk_ids`, while most other bulk delete bodies use `ids`.
- `chat_id` identifies a chat assistant; `session_id` identifies a conversation inside a chat assistant or agent.
- `agent_id` identifies an agent/canvas app; native agent completions use `agent_id` in the JSON body for `/api/v1/agents/chat/completions`.
- `memory_id` identifies a memory collection; message APIs may combine memory and message identifiers depending on the SDK method.
- `DELETE` bodies matter in RAGFlow. Do not convert them to query strings unless an endpoint explicitly documents query parameters.
- Avoid `delete_all=true` unless the user requested a full cleanup and understands the scope.

## Version and packaging notes

- RAGFlow 0.26.1 declares Python `>=3.13,<3.14`.
- The public SDK package is `ragflow-sdk`; the Python import package is `ragflow_sdk`.
- The monorepo package name is `ragflow`; if editable installation of the full server package fails because package discovery expects a top-level `graphrag` package, use the published SDK for client integration and treat the server install issue as deployment/environment troubleshooting rather than an SDK client failure.
