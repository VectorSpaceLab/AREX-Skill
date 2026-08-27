# API reference

## Ports

| Port | Role | Notes |
| --- | --- | --- |
| 8000 | vLLM / OpenAI-compatible model endpoint | Used by `DeepAnalyzeVLLM` and by the API server's internal model client |
| 8100 | File download server | Serves the thread workspace and generated artifacts |
| 8200 | DeepAnalyze API server | OpenAI-compatible file, chat, models, health, and admin routes |

## Files API

| Method | Path | Purpose | Notes |
| --- | --- | --- | --- |
| POST | `/v1/files` | Upload one file | Multipart form field `file`; optional `purpose` defaults to `file-extract` |
| GET | `/v1/files` | List uploaded files | Optional `purpose` filter |
| GET | `/v1/files/{file_id}` | Fetch file metadata | Returns an OpenAI-style file object |
| GET | `/v1/files/{file_id}/content` | Download file bytes | Binary response |
| DELETE | `/v1/files/{file_id}` | Delete an uploaded file | Returns `deleted: true` on success |

Accepted file purposes:
- `fine-tune`
- `answers`
- `file-extract`
- `assistants`

### Upload pattern

```python
import requests

with open("data.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8200/v1/files",
        files={"file": ("data.csv", f, "text/csv")},
        data={"purpose": "file-extract"},
    )
file_id = response.json()["id"]
```

## Chat completions

### Route

`POST /v1/chat/completions`

### Request shape

```json
{
  "model": "DeepAnalyze-8B",
  "messages": [
    {
      "role": "user",
      "content": "Analyze the uploaded files.",
      "file_ids": ["file-..." ]
    },
    {
      "role": "assistant",
      "content": "..."
    },
    {
      "role": "user",
      "content": "Continue the same thread.",
      "thread_id": "thread-...",
      "file_ids": ["file-..." ]
    }
  ],
  "temperature": 0.4,
  "stream": false
}
```

Rules:
- Put `file_ids` on the latest user message for OpenAI compatibility.
- `file_ids` at the top level is still accepted for backward compatibility.
- Put `thread_id` only on the latest user message when continuing a conversation.
- Keep the full conversation history in every follow-up request.

### Non-streaming response

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "...",
        "thread_id": "thread-...",
        "files": [
          {"name": "Conversation_Report_...md", "url": "http://localhost:8100/thread-.../generated/...md"}
        ]
      },
      "finish_reason": "stop"
    }
  ],
  "generated_files": [
    {"name": "Conversation_Report_...md", "url": "http://localhost:8100/thread-.../generated/...md"}
  ],
  "attached_files": ["file-..."]
}
```

### Streaming response

The stream emits SSE `data:` chunks. Watch for:
- `choices[0].delta.content`
- `choices[0].delta.thread_id`
- `choices[0].delta.files`
- top-level `generated_files` on the final chunk
- `[DONE]` terminator

Example parsing pattern:

```python
import json
import requests

response = requests.post(
    "http://localhost:8200/v1/chat/completions",
    json={"model": "DeepAnalyze-8B", "messages": messages, "stream": True},
    stream=True,
)

for line in response.iter_lines():
    if not line:
        continue
    text = line.decode("utf-8")
    if not text.startswith("data: "):
        continue
    payload = text[6:]
    if payload == "[DONE]":
        break
    chunk = json.loads(payload)
    delta = chunk["choices"][0].get("delta", {})
    if delta.get("content"):
        print(delta["content"], end="")
    if delta.get("thread_id"):
        print("thread_id:", delta["thread_id"])
```

## Models and health

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/v1/models` | List available model ids |
| GET | `/health` | Check the API server status |

## Admin

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/v1/admin/cleanup-threads` | Remove expired thread workspaces |
| GET | `/v1/admin/threads-stats` | Inspect thread counts by age bucket |

## Download URLs

Generated files are served from the thread workspace on port 8100. A typical URL looks like:

```text
http://localhost:8100/thread-.../generated/Conversation_Report_....md
```

## OpenAI client pattern

```python
import openai

client = openai.OpenAI(base_url="http://localhost:8200/v1", api_key="dummy")
result = client.chat.completions.create(
    model="DeepAnalyze-8B",
    messages=[{"role": "user", "content": "Summarize the file.", "file_ids": [file_id]}],
)
message = result.choices[0].message
```

Notes:
- Check both `message.files` and response-level `generated_files`.
- For older code, keep `hasattr(message, "files")` and `hasattr(chunk, "generated_files")` guards.
