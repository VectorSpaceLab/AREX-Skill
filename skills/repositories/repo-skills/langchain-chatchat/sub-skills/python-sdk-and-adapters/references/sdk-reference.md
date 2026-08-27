# SDK Reference

## When to read

Read this for `open_chatcaht` SDK classes, method families, constructor defaults, and live-service requirements. Method names and signatures were verified by installed package inspection.

## Import spelling

Use:

```python
import open_chatcaht
from open_chatcaht.chatchat_api import ChatChat
```

Do not use `open_chatchat` unless a future upstream version changes the import package and the repo skill has been refreshed.

## `ApiClient` constructor

```python
ApiClient(
    base_url='http://127.0.0.1:7861/',
    timeout=60,
    use_async=False,
    use_proxy=False,
    proxies=None,
    log_level=logging.INFO,
    retry=3,
    retry_interval=1,
)
```

The client has internal `_get`, `_post`, `_delete`, `_httpx_stream2generator`, and `_get_response_value` helpers. Public category clients inherit from it.

## `ChatChat` aggregate client

```python
ChatChat(base_url='http://127.0.0.1:7861/', timeout=60, use_async=False, use_proxy=False, proxies=None, log_level=logging.INFO, retry=3, retry_interval=1)
```

Attributes created at initialization:

| Attribute | Client class | Purpose |
| --- | --- | --- |
| `knowledge` | `KbClient` | KB CRUD, document upload/search/download, temp docs, vector rebuild. |
| `tool` | `ToolClient` | List and call registered tools. |
| `server` | `ServerClient` | Get configs and prompt templates. |
| `chat` | `ChatClient` | KB/file chat helpers and chat feedback. |
| `openai_adapter` | `StandardOpenaiClient` | OpenAI-compatible `/v1` route wrappers. |

## `KbClient` highlights

Selected methods:

- `create_kb(knowledge_base_name, kb_info='', vector_store_type='faiss', embed_model='bge-large-zh-v1.5')`
- `delete_kb(knowledge_base_name)`
- `list_kb()`
- `list_kb_docs_file(knowledge_base_name)`
- `search_kb_docs(knowledge_base_name, query='', top_k=3, score_threshold=0.4, file_name='', metadata={})`
- `upload_kb_docs(files, knowledge_base_name, override=False, to_vector_store=True, chunk_size=250, chunk_overlap=50, zh_title_enhance=False, docs={}, not_refresh_vs_cache=False)`
- `delete_kb_docs(knowledge_base_name, file_names, delete_content=False, not_refresh_vs_cache=False)`
- `recreate_vector_store(knowledge_base_name, allow_empty_kb=True, vs_type='faiss', embed_model='bge-large-zh-v1.5', chunk_size=250, chunk_overlap=50, zh_title_enhance=False)`
- `upload_temp_docs(files, knowledge_id=None, chunk_size=250, chunk_overlap=50, zh_title_enhance=False)`
- `search_temp_kb_docs(knowledge_id, query, top_k=3, score_threshold=0.4)`
- `download_kb_doc_file(knowledge_base_name, file_name, file_path=None)`
- `kb_doc_file_content(knowledge_base_name, file_name)`

Mutation caution: create/delete/upload/update/rebuild methods change KB state. Use a test KB or temp docs for experiments.

## `ChatClient` highlights

- `chat_feedback(message_id, score=100, reason='')`
- `kb_chat(query, mode='local_kb', kb_name='', top_k=3, score_threshold=0.4, history=[], stream=True, model='chatglm-6b', temperature=0.7, max_tokens=2048, prompt_name='default', return_direct=False)`
- `file_chat(query, knowledge_id, top_k=3, score_threshold=0.4, history=[], stream=True, model_name='chatglm-6b', temperature=0.01, max_tokens=2048, prompt_name='default')`

`kb_chat` and `file_chat` use streaming HTTP calls and return generators from `_httpx_stream2generator`.

## `ToolClient` and `ServerClient`

```python
client.tool.list()
client.tool.call(name='calculate', tool_input={'text': '3+5/2'})
client.server.get_server_configs()
client.server.get_prompt_template(_type='knowledge_base_chat', name='default')
```

`ToolClient.call` requires exact tool names from `ToolClient.list()` and may require external service/API keys depending on the tool.

## `StandardOpenaiClient` highlights

- `list_models()` -> `/v1/models`
- `chat_completions(chat_input)` -> `/v1/chat/completions`, streaming generator
- `completions(chat_input)` -> `/v1/completions`, streaming generator
- `embeddings(embeddings_input)` -> `/v1/embeddings`
- image/audio/file methods for matching `/v1` routes

Some media/audio/file wrappers in the inspected SDK are incomplete or route strings contain double slashes. Prefer raw route checks from the API sub-skill when a wrapper behaves unexpectedly.

## Live-call checklist

- Start API server and verify base URL.
- Ensure model provider names are configured.
- Use `server.get_server_configs()` or `tool.list()` before mutating KBs.
- For streaming generators, handle dictionaries with `code`/`msg` errors as well as normal chunks.
- Pass explicit `base_url` for scripts and tests.
