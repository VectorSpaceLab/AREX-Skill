# OpenAI-Compatible API Reference

`transformers serve` exposes local HTTP endpoints that match common OpenAI SDK patterns while loading Transformers models underneath.

## Base client

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-used")
```

The local server does not require a real OpenAI API key for local requests, but the SDK expects a value.

## Chat completions

Endpoint: `POST /v1/chat/completions`

```python
completion = client.chat.completions.create(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    messages=[{"role": "user", "content": "What is Transformers?"}],
    max_tokens=128,
    temperature=0.7,
)
print(completion.choices[0].message.content)
```

Streaming:

```python
stream = client.chat.completions.create(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    messages=[{"role": "user", "content": "Count to three."}],
    max_tokens=32,
    stream=True,
)
for chunk in stream:
    text = chunk.choices[0].delta.content
    if text:
        print(text, end="")
```

Validation checks:

- Non-streaming response has `choices[0].message.content` and `usage`.
- Streaming chunks use `choices[0].delta.content` and may include role/finish chunks.
- Unsupported OpenAI fields are rejected or warned about rather than silently applied.
- `stop` is mapped to generation stop strings; many other OpenAI-only fields are not implemented.

## Legacy completions

Endpoint: `POST /v1/completions`

```bash
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai-community/gpt2",
    "prompt": "Transformers is",
    "max_tokens": 32
  }'
```

Expected response: `choices[0].text`, plus model and usage fields. Use this for base text completion when chat templates are not appropriate.

## Responses API

Endpoint: `POST /v1/responses`

```python
response = client.responses.create(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    input="Give one reason local inference is useful.",
    max_output_tokens=64,
)
print(response.output_text)
```

Streaming:

```python
for event in client.responses.create(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    input="Write a haiku about caches.",
    stream=True,
):
    if getattr(event, "type", "") == "response.output_text.delta":
        print(event.delta, end="")
```

Use Responses API for newer OpenAI-style clients, multi-turn flows, and tool-call-compatible response structures. Verify event names because SDK versions can expose typed event objects differently.

## Multimodal inputs

Chat completions can accept content lists with text plus media elements when the model and processor support them:

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "Describe this image."},
        {"type": "image_url", "image_url": {"url": "https://example.invalid/image.png"}},
    ],
}]
```

Audio can use OpenAI `input_audio` with base64 data for compatible multimodal models. The implementation also supports an `audio_url` extension; treat it as nonstandard and subject to change. Video workflows use `video_url` content for supported processors.

## Audio transcription

Endpoint: `POST /v1/audio/transcriptions`

```bash
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "model=openai/whisper-large-v3" \
  -F "file=@audio.wav"
```

Expected response: JSON with `text`. Missing audio dependencies can raise import errors; install audio libraries before using this endpoint.

## Model discovery

Endpoint: `GET /v1/models`

```bash
curl http://localhost:8000/v1/models
```

The server scans the local Hugging Face cache and returns generative models in OpenAI list format. If a recently downloaded model is missing, confirm the cache directory and that the model config maps to a supported generative architecture.

## Model warmup and SSE

Endpoint: `POST /load_model`

```bash
curl -N -X POST http://localhost:8000/load_model \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-0.5B-Instruct"}'
```

Expected event patterns:

- Download and loading progress events for fresh models.
- Cached/already-loaded indicators for models already on disk or in memory.
- Exactly one final ready event on success.
- Error events or HTTP errors for nonexistent models, auth failures, dependency failures, OOM, or invalid payloads.

`transformers chat` uses this endpoint automatically before sending messages.

## Reasoning fields

Reasoning-capable models may return reasoning text separately:

- Chat completions can include `reasoning_content` alongside assistant `content`.
- Streaming may emit reasoning deltas separately from visible text depending on client/schema support.
- Responses API can emit reasoning-related output items/events.

Do not promise reasoning for every model. Server `--reasoning on|off|auto` controls chat template kwargs only when templates or tokenizer metadata support it.

## Request body generation controls

Common generation settings accepted through OpenAI-like bodies include token limits, sampling parameters, `stream`, `seed`, and extra generation config fields where implemented. If a setting is specific to Transformers `GenerationConfig`, prefer testing it with a tiny request before relying on it in a service.

For decoding semantics, use [../generation/SKILL.md](../../generation/SKILL.md).
