# OpenAI-compatible API reference

The bundled `scripts/run_openai_api.py` helper starts a Flask server for a loaded Baichuan2 Chat model and exposes an OpenAI-style chat-completions route.

## Launch

Inspect without loading weights:

```bash
python scripts/run_openai_api.py --help
python scripts/run_openai_api.py --dry-run --host 127.0.0.1 --port 8000
```

Start the server:

```bash
python scripts/run_openai_api.py \
  --model baichuan-inc/Baichuan2-13B-Chat \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype float16
```

Important launch options:

| Option | Default | Meaning |
| --- | --- | --- |
| `--model` | `baichuan-inc/Baichuan2-13B-Chat` | Hugging Face model id or local model directory for a Baichuan2 Chat checkpoint. |
| `--host` | `0.0.0.0` | Flask bind address. Use `127.0.0.1` for local-only access. |
| `--port` | `8000` | Flask port. |
| `--dtype` | `float16` | Weight dtype: `float16`, `bfloat16`, `float32`, or `auto`. |
| `--device-map` | `auto` | Transformers device map. |
| `--no-trust-remote-code` | off | Disable remote code trust; Baichuan2 Hugging Face models normally require trusted remote code. |
| `--dry-run` | off | Print resolved config and endpoint without importing Flask/Transformers or loading weights. |

## Health endpoint

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "model": "baichuan-inc/Baichuan2-13B-Chat",
  "streaming": false
}
```

## Chat completions endpoint

```http
POST /v1/chat/completions
Content-Type: application/json
```

### Request body

```json
{
  "model": "baichuan2-chat",
  "messages": [
    {"role": "user", "content": "你好，请介绍一下你自己。"}
  ],
  "stream": false
}
```

Fields:

| Field | Required | Behavior |
| --- | --- | --- |
| `messages` | yes | List of role/content dictionaries passed to `model.chat(tokenizer, messages)`. Use Chat-style `user` and `assistant` turns. |
| `stream` | no | Must be false or omitted. `true` returns HTTP 400 because this helper intentionally preserves the native non-streaming API behavior. |
| `model` | no | Accepted for client compatibility, but the server uses the model loaded at process startup. It does not hot-swap models per request. |
| Other OpenAI fields | no | The helper does not promise OpenAI sampling-parameter parity. Configure defaults through the model generation config, not per request. |

### Response body

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "baichuan-inc/Baichuan2-13B-Chat",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 42,
    "total_tokens": 54
  }
}
```

Token counts are best-effort counts from the configured tokenizer and are intended for observability rather than billing.

### Streaming-not-supported response

If the client sends `"stream": true`:

```json
{
  "error": {
    "message": "Streaming is not supported by this Baichuan2 API helper; send stream=false.",
    "type": "invalid_request_error",
    "code": "streaming_not_supported"
  }
}
```

The HTTP status is `400`.

## Curl examples

Local non-streaming call:

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "解释一下“温故而知新”。"}],
    "stream": false
  }' | python -m json.tool
```

Streaming rejection check:

```bash
curl -i http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "hello"}], "stream": true}'
```

## Client compatibility notes

- Use OpenAI clients that can target a custom `base_url` and send non-streaming chat completion requests.
- Keep request histories small enough for the model context window and available GPU memory.
- If the client sends `system` messages, validate behavior before relying on it. The canonical Baichuan2 examples use `user` and `assistant` turns.
- This server is a demo/helper. Add authentication, TLS, request limits, logging policy, and process supervision before exposing it outside a trusted network.
