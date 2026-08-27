# OpenAI-compatible API

Use this reference when you want the OpenAI-style HTTP surface or the OpenAI Python SDK.

## Base URL distinction

- **Xinference endpoint**: `http://HOST:PORT`
  - Use this with the Xinference Python client.
- **OpenAI-compatible base URL**: `http://HOST:PORT/v1`
  - Use this with OpenAI-style SDK calls and raw HTTP requests.

A launched model UID is required. The API does not infer a model from the family name.

## Auth header

When auth is enabled, send:

```http
Authorization: Bearer YOUR_API_KEY
```

In demos without auth, the SDK still expects a non-empty placeholder string.

## Core request families

| Family | Endpoint | SDK method | Request shape |
| --- | --- | --- | --- |
| Chat | `/v1/chat/completions` | `client.chat.completions.create(...)` | `model`, `messages`, optional `stream`, `tools`, `max_tokens` |
| Generate | `/v1/completions` | `client.completions.create(...)` | `model`, `prompt`, optional `stream` |
| Embeddings | `/v1/embeddings` | `client.embeddings.create(...)` | `model`, `input`, optional truncation fields |
| Rerank | `/v1/rerank` | direct HTTP / `requests` | `model`, `query`, `documents`, optional ranking knobs |
| Audio | `/v1/audio/transcriptions`, `/v1/audio/translations`, `/v1/audio/speech` | HTTP / media helpers | multipart audio payloads |
| Image | `/v1/images/generations`, `/v1/images/variations`, `/v1/images/edits`, `/v1/images/ocr` | HTTP / image helpers | JSON or multipart image payloads |
| Video | `/v1/video/generations`, `/v1/video/generations/image`, `/v1/video/generations/flf` | HTTP | JSON or multipart image payloads |
| Flexible | `/v1/flexible/infers` | HTTP | raw args/kwargs payload |

## Chat example

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:9997/v1", api_key="YOUR_API_KEY")
response = client.chat.completions.create(
    model="MODEL_UID",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a short greeting."},
    ],
)
print(response)
```

```bash
curl -X POST "http://127.0.0.1:9997/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "MODEL_UID",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a short greeting."}
    ]
  }'
```

## Generate example

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:9997/v1", api_key="YOUR_API_KEY")
response = client.completions.create(
    model="MODEL_UID",
    prompt="Write a short paragraph about robotics.",
)
print(response)
```

```bash
curl -X POST "http://127.0.0.1:9997/v1/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "MODEL_UID",
    "prompt": "Write a short paragraph about robotics."
  }'
```

## Embedding example

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:9997/v1", api_key="YOUR_API_KEY")
response = client.embeddings.create(
    model="MODEL_UID",
    input=["A sentence to embed."],
)
print(response)
```

```bash
curl -X POST "http://127.0.0.1:9997/v1/embeddings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "MODEL_UID",
    "input": ["A sentence to embed."]
  }'
```

## Rerank example

Rerank is exposed as a Xinference HTTP endpoint. Use direct HTTP or the Xinference Python client.

```python
import requests

response = requests.post(
    "http://127.0.0.1:9997/v1/rerank",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_API_KEY",
    },
    json={
        "model": "MODEL_UID",
        "query": "A man is eating pasta.",
        "documents": [
            "A man is eating food.",
            "A man is eating a piece of bread.",
            "The girl is carrying a baby.",
        ],
    },
)
print(response.json())
```

```bash
curl -X POST "http://127.0.0.1:9997/v1/rerank" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "MODEL_UID",
    "query": "A man is eating pasta.",
    "documents": [
      "A man is eating food.",
      "A man is eating a piece of bread.",
      "The girl is carrying a baby."
    ]
  }'
```

## Streaming notes

- Chat and generate requests accept `stream=true` and return chunked responses.
- The Xinference client helpers treat streaming as iterators.
- If you use raw HTTP, read SSE `data:` lines instead of calling a plain JSON parser on the socket.

## Validation notes

- For strict chat models, keep the first `system` message first.
- `messages` must be present for chat requests.
- `replica` validation happens at launch time, not here.
- OCR responses are JSON even when the payload looks like plain text.
