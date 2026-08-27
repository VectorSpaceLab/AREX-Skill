# API Contracts

## Simple FastAPI endpoint

The simple service exposes `POST /` and expects a JSON object:

| Field | Type | Default/meaning |
| --- | --- | --- |
| `prompt` | string | Required user query. |
| `history` | list of `[query, response]` pairs or null | Empty history when omitted. |
| `max_length` | integer or null | Source defaults to 2048 when falsey. |
| `top_p` | number or null | Source defaults to 0.7 when falsey. |
| `temperature` | number or null | Source defaults to 0.95 when falsey. |

Example:

```bash
curl -X POST http://127.0.0.1:8000/ \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"你好","history":[]}'
```

The response contains `response` (string), `history` (updated pair list),
`status` (200), and `time` (formatted timestamp). The service calls
`model.chat(tokenizer, prompt, history=...)` and performs a CUDA cache cleanup
when CUDA is available.

## OpenAI-compatible endpoint

`GET /v1/models` returns a model list containing a ChatGPT-style model card.
`POST /v1/chat/completions` accepts:

```json
{
  "model": "chatglm2-6b",
  "messages": [
    {"role": "system", "content": "Answer concisely."},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.8,
  "top_p": 0.8,
  "max_length": 2048,
  "stream": false
}
```

The last message must have role `user`. If the first earlier message is
`system`, the source concatenates its content with the current query. Earlier
messages are converted to ChatGLM history only when they form alternating
`user`/`assistant` pairs; malformed or odd-length histories are not silently
repaired by the service.

Non-streaming responses use `object: "chat.completion"` and one assistant
choice. Streaming responses use `object: "chat.completion.chunk"`, begin with
an assistant-role delta, emit incremental `content` deltas, emit a final
`finish_reason: "stop"` chunk, and then emit `[DONE]`. Use an SSE-aware client
and do not treat each event as a complete Chat Completions response.

The request model includes `temperature`, `top_p`, `max_length`, and `stream`;
these are the repo's documented fields. The legacy implementation does not
provide authentication, usage accounting, tool calls, or batching.
