# CLI and OpenAI-compatible API

This reference covers the serving command line, `--omni` routing, stage launch
choices, and request payload selection. It is distilled so a future agent does
not need the original checkout.

## `--omni` CLI routing

vLLM-Omni installs a dedicated `vllm-omni` console entry point and also supports
`vllm serve MODEL --omni` with a compatible vLLM installation.

- `vllm-omni ...` without `--omni` delegates to ordinary upstream vLLM CLI
  behavior.
- `vllm-omni serve MODEL --omni ...` selects the Omni parser and starts the
  Omni OpenAI-compatible server.
- `vllm serve MODEL --omni ...` is the normal user-facing spelling when the
  installed vLLM version understands the `--omni` flag.
- If `vllm` reports an unknown `--omni` flag, or Omni-specific routes are
  absent, treat it as a version/alignment issue and use `vllm-omni` while fixing
  the installed vLLM / vLLM-Omni pair.

The prepared inspection environment verified the help path:

```bash
vllm-omni serve --omni --help=OmniConfig
```

The OmniConfig help group includes launch/deploy controls, stage controls,
diffusion/offload/parallel controls, TTS controls, and serving diagnostics. Use
that help command before changing unfamiliar flags; it is parser-only and does
not load a model.

## Minimal server launches

Single-runtime launch, letting the package choose its default deploy profile for
models that provide one:

```bash
vllm serve MODEL --omni --host 0.0.0.0 --port 8091 --trust-remote-code
```

Use `vllm-omni serve` instead of `vllm serve` when the user reports that the
plain `vllm` executable does not recognize `--omni`:

```bash
vllm-omni serve MODEL --omni --host 0.0.0.0 --port 8091 --trust-remote-code
```

Common launch additions:

- `--deploy-config PATH_TO_DEPLOY_YAML`: override the package default or use a
  custom stage topology.
- `--stage-overrides '{"1":{"gpu_memory_utilization":0.5}}'`: single-runtime
  JSON overrides; for stage-based launches prefer discrete per-process flags.
- `--gpu-memory-utilization 0.8`, `--enforce-eager`, `--dtype`,
  `--max-model-len`: ordinary vLLM engine controls when they apply to the local
  stage.
- `--uvicorn-log-level debug`, `--log-file PATH`, `--log-stats`: diagnostics.

## Stage head and headless launches

Use the stage-based CLI when the deployment needs isolated OS processes, separate
GPU masks, or separate hosts. The head process runs the API server and the Omni
master; headless processes register worker stages with the same master address
and port.

Head / API process, stage 0:

```bash
CUDA_VISIBLE_DEVICES=0 vllm serve MODEL --omni \
  --port 8091 \
  --stage-id 0 \
  --omni-master-address 127.0.0.1 \
  --omni-master-port 26000
```

Headless worker, stage 1:

```bash
CUDA_VISIBLE_DEVICES=1 vllm serve MODEL --omni \
  --stage-id 1 \
  --headless \
  --omni-master-address 127.0.0.1 \
  --omni-master-port 26000
```

Validation rules enforced by the Omni serve parser:

- `--stage-id` requires both `--omni-master-address` and
  `--omni-master-port`.
- `--headless` requires `--stage-id`, `--omni-master-address`,
  `--omni-master-port`, a model, and `worker_backend=multi_process`.
- `--omni-replica-address` is only valid with `--headless`; it is for multi-NIC
  hosts where the auto-detected replica address is wrong.
- `--omni-dp-size-local` must be `>= 1`; values other than `1` require
  `--stage-id` because the value is process-local for a single stage.
- `--omni-lb-policy` accepts `random`, `round-robin`, or
  `least-queue-length` on the head runtime.
- If `--stage-id` names a stage that the resolved deploy config does not
  contain, the process fails before serving.

Do not pass upstream vLLM data-parallel flags under `--omni`. The parser rejects
these explicit flags because Omni parallelism comes from per-stage deploy config
and Omni replica controls:

- `--data-parallel-size`
- `--data-parallel-size-local`
- `--data-parallel-address`
- `--data-parallel-rpc-port`
- `--data-parallel-start-rank`
- `--data-parallel-backend`
- `--api-server-count`
- `--enable-expert-parallel`

Use deploy YAML fields, per-stage `num_replicas`, and `--omni-dp-size-local`
instead.

## Endpoint chooser

| Task | Endpoint | Wire format | Main response |
| --- | --- | --- | --- |
| General chat / multimodal chat / many Omni model demos | `POST /v1/chat/completions` | JSON OpenAI Chat schema; Omni extras go in `extra_body` for curl/requests | OpenAI chat completion; image/audio/video may be embedded in message content depending on model |
| Text-to-image diffusion | `POST /v1/images/generations` | JSON | `data[].b64_json` by default, or raw file when `response_format="file"` |
| Image edit / image-to-image | `POST /v1/images/edits` | `multipart/form-data`; can also use URL fields through SDK `extra_body` | image edit response; optional SSE for multi-stage AR+image edit |
| Text-to-video / image-to-video / speech-to-video | `POST /v1/videos` | `multipart/form-data` async job | job id, then poll/download |
| Synchronous video benchmark/simple script | `POST /v1/videos/sync` | `multipart/form-data` | raw video bytes |
| Text-to-speech | `POST /v1/audio/speech` | JSON | binary audio, raw audio stream, or `speech.audio.*` SSE |
| Batch text-to-speech | `POST /v1/audio/speech/batch` | JSON | JSON items with base64 audio and usage |
| Voice list/upload/delete for TTS | `GET/POST/DELETE /v1/audio/voices` | JSON or multipart | voice metadata |
| General text-to-audio/sound effect | `POST /v1/audio/generate` | JSON | binary audio |
| Health/model listing | `GET /health`, `GET /v1/models` | HTTP GET | readiness or model metadata |

## `extra_body`: curl/requests versus OpenAI SDK

For `/v1/chat/completions`, diffusion parameters such as `height`, `width`,
`num_inference_steps`, `seed`, `guidance_scale`, `num_frames`, and
`negative_prompt` are not fields in the standard OpenAI Chat schema. vLLM-Omni
supports them, but the placement depends on the client.

### curl / requests JSON

Wrap extra fields under a nested JSON key named `extra_body`:

```bash
curl -s http://localhost:8091/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "MODEL",
    "messages": [{"role": "user", "content": "a cup of coffee on a table"}],
    "extra_body": {
      "height": 1024,
      "width": 1024,
      "num_inference_steps": 50,
      "guidance_scale": 4.0,
      "seed": 42
    }
  }'
```

Python `requests` follows the same nested shape:

```python
payload = {
    "model": "MODEL",
    "messages": [{"role": "user", "content": "a cup of coffee on a table"}],
    "extra_body": {"height": 1024, "width": 1024, "seed": 42},
}
```

### OpenAI Python SDK

Use the `extra_body=` keyword argument. The SDK merges that dict into the final
request body, so do not nest another `extra_body` inside it:

```python
response = client.chat.completions.create(
    model="MODEL",
    messages=[{"role": "user", "content": "a cup of coffee on a table"}],
    extra_body={"height": 1024, "width": 1024, "seed": 42},
)
```

A server log warning that fields such as `height` or `width` were "ignored" can
be harmless for chat-completions requests: upstream OpenAI schema validation does
not know those Omni fields, but vLLM-Omni stores and forwards them internally.
If the output proves the fields were not applied, first check that you used the
right nested-vs-keyword shape.

## Payload patterns by endpoint

### Chat completions

Text-only request:

```json
{
  "model": "MODEL",
  "messages": [{"role": "user", "content": "Briefly introduce yourself."}],
  "extra_body": {"modalities": ["text"]}
}
```

Multimodal request with an image URL or data URL:

```json
{
  "model": "MODEL",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image."},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}}
      ]
    }
  ],
  "extra_body": {"modalities": ["text"]}
}
```

For image-generating chat models, outputs may appear in
`choices[0].message.content[*].image_url.url` as a data URL. For speech-capable
chat models, inspect the message content and audio fields instead of assuming a
plain text-only response.

### Image generation

Dedicated image generation accepts standard OpenAI image fields plus Omni
diffusion fields at top level:

```json
{
  "model": "MODEL",
  "prompt": "a dragon over a mountain lake",
  "size": "1024x1024",
  "response_format": "b64_json",
  "num_inference_steps": 50,
  "guidance_scale": 4.0,
  "seed": 42
}
```

Use direct HTTP for extension fields when the OpenAI SDK resource does not expose
them.

### Image edit

The dedicated edit endpoint is multipart. Send one or more uploaded `image`
parts, or pass URL/data references through the extension `url` field when using a
compatible SDK/direct HTTP wrapper:

```bash
curl -s http://localhost:8091/v1/images/edits \
  -F 'model=MODEL' \
  -F 'image=@input.png' \
  -F 'prompt=make the product photo look like a clean studio ad' \
  -F 'size=1024x1024' \
  -F 'output_format=png' \
  -F 'num_inference_steps=50' \
  -F 'guidance_scale=1' \
  -F 'seed=777'
```

`stream=true` is only for multi-stage image-edit pipelines that emit AR text
before the final image; single-stage edit pipelines reject it.

### Videos

The async video endpoint is multipart. Create a job, poll it, then download the
content:

```bash
create_response=$(curl -s http://localhost:8091/v1/videos \
  -F 'prompt=A cinematic tracking shot of a mountain lake at sunrise' \
  -F 'size=1280x720' \
  -F 'num_frames=80' \
  -F 'fps=16' \
  -F 'num_inference_steps=40' \
  -F 'guidance_scale=4.0' \
  -F 'seed=42')
video_id=$(printf '%s' "$create_response" | jq -r '.id')
curl -s "http://localhost:8091/v1/videos/${video_id}" | jq .
curl -L "http://localhost:8091/v1/videos/${video_id}/content" -o output.mp4
```

Reference inputs:

- Upload a local image or video with `input_reference=@file`.
- Use `image_reference={"image_url":"https://..."}` for URL/data image refs.
- Use `video_reference={"video_url":"https://..."}` for URL/data video refs.
- Use `audio_reference={"audio_url":"https://..."}` for speech-to-video.
- Do not combine `input_reference` with `image_reference`/`video_reference` for
  the same request.

### Speech / TTS

Text-to-speech uses JSON and returns binary audio by default:

```json
{
  "model": "MODEL",
  "input": "Hello, how are you?",
  "voice": "vivian",
  "response_format": "wav",
  "language": "English"
}
```

Voice cloning adds `task_type`, `ref_audio`, and `ref_text` when the loaded model
supports it:

```json
{
  "model": "MODEL",
  "input": "Hello in the cloned voice",
  "task_type": "Base",
  "ref_audio": "https://example.com/reference.wav",
  "ref_text": "Transcript of the reference audio",
  "response_format": "wav"
}
```

Use `/v1/audio/voices` to list model voices before debugging an unsupported
speaker.

### Audio generation

General text-to-audio/sound-effect diffusion uses `/v1/audio/generate`:

```json
{
  "model": "MODEL",
  "input": "The sound of ocean waves crashing on a beach",
  "audio_length": 8.0,
  "negative_prompt": "Low quality, distorted, noisy",
  "guidance_scale": 7.0,
  "num_inference_steps": 100,
  "seed": 42,
  "response_format": "wav"
}
```

This is separate from TTS `/v1/audio/speech`.
