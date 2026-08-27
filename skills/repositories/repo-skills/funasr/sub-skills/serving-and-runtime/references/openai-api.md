# OpenAI-compatible HTTP API

This reference covers the packaged `funasr-server` CLI, the HTTP health and transcription routes, and the safe smoke helper bundled with this sub-skill.

## Best entry point

- Use `funasr-server` for the OpenAI-compatible API.
- Use [`scripts/openai_api_smoke_test.py`](../scripts/openai_api_smoke_test.py) for a cross-platform HTTP smoke that only checks health and model listing unless you also supply a local audio file.

```bash
funasr-server --device cpu --model sensevoice --port 8000
python scripts/openai_api_smoke_test.py --base-url http://127.0.0.1:8000
python scripts/openai_api_smoke_test.py \
  --base-url http://127.0.0.1:8000 \
  --audio-path sample.wav \
  --model sensevoice \
  --response-format verbose_json
```

## Route map

| Route | Method | Purpose | Notes |
|---|---|---|---|
| `/health` | `GET` | Report server state | Returns device and loaded model names. |
| `/v1/models` | `GET` | List model ids | Includes the packaged aliases the server can serve. |
| `/v1/audio/transcriptions` | `POST` | OpenAI-compatible transcription | Accepts `file`, `model`, `language`, `response_format`, and `spk`. |
| `/asr` | `POST` | FunASR-native ASR output | Adds `processing_time` and `rtf` to the returned JSON. |
| `/docs` | `GET` | Interactive API docs | Available once the server is up. |

## CLI options that matter

| Flag | Default | Why it matters |
|---|---|---|
| `--host` | `0.0.0.0` | Bind address for the server. |
| `--port` | `8000` | Port for HTTP clients and browser demos. |
| `--device` | `cuda` | Use `cpu`, `cuda`, or `mps` depending on the host. |
| `--model` | `auto` | Preloads a model alias at startup. `auto` maps to a practical default for the chosen device. |
| `--model-path` | unset | Local path or remote model id that overrides `--model`. |
| `--hub` | `ms` | Remote hub selector for `--model-path` or remote model ids. |
| `--spk-model` | `cam++` | Speaker model loaded lazily when `spk=true` is requested. |
| `--cors-origin` | unset | Repeatable trusted browser origins; duplicates are normalized away. |

## Response formats

The transcription route understands three output styles:

- `json` → `{"text": ...}`
- `text` → plain text payload with the transcript text
- `verbose_json` → structured JSON with `task`, `language`, `duration`, `text`, and `segments`

`verbose_json` is the best choice when you need to check timestamps or speaker labels. The server preserves `speaker` on each returned segment when the backend provides it and the request uses `spk=true`.

## Model-loading behavior

- `--model-path` overrides `--model`.
- `--hub` chooses the remote provider when the server needs to resolve a remote model id.
- `--spk-model` is loaded only when a request asks for speaker diarization.
- `fun-asr-nano` attempts the vLLM-backed path first and falls back to the standard `AutoModel` path if that runtime is unavailable.
- For non-LLM models such as SenseVoice or Paraformer, the packaged HTTP server does not need vLLM.

## Practical smoke expectations

- `GET /health` should succeed without any transcription file.
- `GET /v1/models` should succeed without a downloaded sample.
- A transcription check is optional and should use a local audio file that the user already has.
- The bundled smoke helper does not download a sample on its own.

## Example OpenAI SDK usage

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="x")
result = client.audio.transcriptions.create(
    model="sensevoice",
    file=open("sample.wav", "rb"),
    response_format="verbose_json",
)
print(result.text)
```

## When to stop and route elsewhere

- If the problem is chunk sizing, endpoint mode, or delayed streaming output, use the realtime WebSocket reference instead.
- If the problem is model-family selection, vLLM dtype choice, or Nano/GLM/Qwen3 behavior, route to `llm-asr-and-vllm`.
- If the problem is punctuation cleanup or ITN/TN, route to `text-normalization`.
