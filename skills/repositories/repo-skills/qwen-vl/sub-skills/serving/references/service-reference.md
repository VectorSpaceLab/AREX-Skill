# Qwen-VL service reference

This reference helps prepare commands or diagnose service behavior without
starting a listener by default. The bundled scripts are self-contained runtime
copies; they still require installed Qwen-VL dependencies and model weights at
launch time.

## Service surfaces

| Surface | Bundled script | Best for | Default checkpoint | Notes |
| --- | --- | --- | --- | --- |
| Gradio multimodal demo | [`../scripts/web_demo_mm.py`](../scripts/web_demo_mm.py) | Human interactive image upload, chat, regenerate, and grounding-box rendering | `qwen/Qwen-VL-Chat` | Uses ModelScope loader; supports `--share` and `--inbrowser`. |
| OpenAI-compatible FastAPI API | [`../scripts/openai_api.py`](../scripts/openai_api.py) | Programmatic chat through `/v1/models` and `/v1/chat/completions` | `QWen/QWen-7B-Chat` inherited from source | For Qwen-VL service, normally pass `-c Qwen/Qwen-VL-Chat` or a local Qwen-VL-Chat checkpoint. |

Both scripts load the tokenizer, model, and generation config during startup;
this may download or read large checkpoint files. Use `--help` and command
construction for planning, and launch only after user approval.

## Dependency groups

Install the base Qwen-VL requirements plus the service-specific extras for the
chosen surface:

| Surface | Extra packages listed by the repo |
| --- | --- |
| Gradio demo | `gradio`, `modelscope` |
| OpenAI-compatible API | `fastapi`, `uvicorn`, `openai`, `pydantic`, `sse_starlette` |

These package groups should be enough for non-listener help/import checks.
Full model loading and service startup are long-running and checkpoint-dependent,
so run them only after the user approves a launch.

## Common safe launch workflow

1. Pick the checkpoint. Prefer a chat checkpoint such as `Qwen/Qwen-VL-Chat`,
   `qwen/Qwen-VL-Chat`, or a user-supplied local checkpoint directory for chat
   service behavior. Base `Qwen-VL` checkpoints may not follow instructions like
   the chat model.
2. Inspect the CLI without loading weights:

   ```bash
   python scripts/web_demo_mm.py --help
   python scripts/openai_api.py --help
   ```

3. Choose the bind address:
   - `127.0.0.1`: localhost only; safest default for local testing.
   - `0.0.0.0`: bind all interfaces; use only with deliberate network exposure,
     firewall/proxy controls, and authentication at an outer layer.
4. Choose a port that is free on the host. Both scripts default to `8000` unless
   changed.
5. Start exactly one service command only when requested.

## Gradio web demo CLI

Help output and source defaults expose these flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `-h`, `--help` | n/a | Print help and exit without loading model weights. |
| `-c`, `--checkpoint-path` | `qwen/Qwen-VL-Chat` | ModelScope model id or local checkpoint path. |
| `--cpu-only` | `false` | Force CPU device map. Functional but slow for real inference. |
| `--share` | `false` | Ask Gradio to create a public share link. Treat as public exposure. |
| `--inbrowser` | `false` | Open a browser tab on the launching machine. |
| `--server-port` | `8000` | Gradio listener port. |
| `--server-name` | `127.0.0.1` from source | Host/interface to bind. Help text does not print the default, but source does. |

Safe local command template:

```bash
python scripts/web_demo_mm.py \
  -c qwen/Qwen-VL-Chat \
  --server-name 127.0.0.1 \
  --server-port 8000
```

Exposed command template, only after the user accepts the risk:

```bash
python scripts/web_demo_mm.py \
  -c qwen/Qwen-VL-Chat \
  --server-name 0.0.0.0 \
  --server-port 8000
```

Add `--share` only when a public Gradio link is explicitly desired. Add
`--inbrowser` only on an interactive desktop where opening a browser is useful.
The demo stores uploaded images under Gradio's temporary directory and may write
rendered grounding-box images there.

## OpenAI-compatible FastAPI CLI

Help output and source defaults expose these flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `-h`, `--help` | n/a | Print help and exit without loading model weights. |
| `-c`, `--checkpoint-path` | `QWen/QWen-7B-Chat` | Checkpoint name or local path. Override for Qwen-VL-Chat service. |
| `--cpu-only` | `false` | Force CPU device map; otherwise `device_map="auto"`. |
| `--server-port` | `8000` | Uvicorn listener port. |
| `--server-name` | `127.0.0.1` | Host/interface to bind. Help warns to use `0.0.0.0` for remote access. |

Safe local command template:

```bash
python scripts/openai_api.py \
  -c Qwen/Qwen-VL-Chat \
  --server-name 127.0.0.1 \
  --server-port 8000
```

The script starts Uvicorn with one worker. It adds permissive CORS middleware:
all origins, credentials, methods, and headers are allowed. That is convenient
for local prototyping but should be restricted by a reverse proxy or edited
server if exposed beyond a trusted network.

## OpenAI-compatible endpoints

### `GET /v1/models`

Returns a `ModelList` containing one model card with id `gpt-3.5-turbo`. This
is a compatibility shim and does not reflect the actual checkpoint selected by
`--checkpoint-path`.

Smoke query after a requested launch:

```bash
curl http://127.0.0.1:8000/v1/models
```

### `POST /v1/chat/completions`

Request fields accepted by the Pydantic model:

| Field | Required | Notes |
| --- | --- | --- |
| `model` | yes | Echoed in the response; not used to switch loaded checkpoints. |
| `messages` | yes | Roles: `user`, `assistant`, `system`, or `function`. At least one `user` message is required. |
| `functions` | no | Converted into a ReAct-style tool instruction; see function-call behavior below. |
| `temperature` | no | Passed to `model.chat`. |
| `top_p` | no | Passed to `model.chat`. |
| `max_length` | no | Accepted by schema, but the non-streaming `model.chat` path does not pass it through. |
| `stream` | no | `true` returns HTTP 400; streaming is disabled in the current handler. |
| `stop` | no | Extra stop strings; function calls also add `Observation:` as a stop marker. |

Minimal non-streaming request:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen-vl-chat",
    "messages": [
      {"role": "user", "content": "Describe this service in one sentence."}
    ],
    "stream": false
  }'
```

The response object is `chat.completion` with one choice. When no function call
is parsed, the assistant message contains plain `content` and `finish_reason` is
`stop`.

## Streaming behavior

The API source contains an unfinished streaming generator, but the request
handler deliberately rejects streaming:

- `stream: true` with functions: HTTP 400, function calling is not implemented
  for stream mode.
- `stream: true` without functions: HTTP 400, stream requests are not supported
  currently.

Set `stream: false` or omit the field. Do not build clients that require Server
Sent Events from this service unless the script is extended and retested.

## Function-call formatting

The OpenAI-compatible function-call path is a ReAct-style adapter rather than a
full OpenAI tools implementation:

1. Each item in `functions` is converted to a textual tool description using
   `name`, optional `name_for_model`, optional `name_for_human`, description
   fields, and JSON-encoded `parameters`.
2. That tool text is appended to a system instruction that asks the model to
   write `Thought`, `Action`, `Action Input`, `Observation`, and `Final Answer`
   sections.
3. Prior assistant `function_call` messages are rendered back into `Action:` and
   `Action Input:` text. `function` role messages are appended as
   `Observation:` and must follow an assistant turn.
4. The final model output is parsed by looking for the last `Action:` and
   `Action Input:` before `Observation:`. If present, the response choice has
   `finish_reason: function_call` and a `function_call` object. Otherwise the
   code strips a trailing `Final Answer:` marker and returns plain content.

Invalid role order raises HTTP 400. A system message is accepted only as the
first message, and the default OpenAI system prompt text is ignored when it
matches `You are a helpful assistant.`.

## Docker guidance: reference only

The generated skill does not bundle Dockerfiles. If the operator has a build
context containing the official Dockerfiles, the source build notes used these
patterns:

```bash
# Gradio web demo, container exposes 8000.
docker build -t qwen-vl-chat:webdemo --platform linux/amd64 -f Dockerfile.qwendemo .
docker run --gpus device=0 -d --restart always \
  --name qwen-vl-chat -p 8000:8000 --platform linux/amd64 \
  qwen-vl-chat:webdemo

# OpenAI-compatible API, container exposes 8080.
docker build -t qwen-vl-chat:openai --platform linux/amd64 -f Dockerfile.qwenopenai .
docker run --gpus device=0 -d --restart always \
  --name qwen-vl-chat-openai -p 8080:8080 --platform linux/amd64 \
  qwen-vl-chat:openai

# Int4 OpenAI-compatible API; requires compatible optimum/AutoGPTQ wheels.
docker build -t qwen-vl-chat:int4-openai --platform linux/amd64 -f Dockerfile.qwenint4openai .
docker run --gpus device=0 -d --restart always \
  --name qwen-vl-chat-int4 -p 8080:8080 --platform linux/amd64 \
  qwen-vl-chat:int4-openai
```

The source run examples also mounted the host Docker socket. Avoid that mount
for ordinary serving because it gives the container broad host control unless a
separate operational requirement justifies it. The Int4 image path installs
optional quantization packages that were not part of the verified serving smoke;
treat it as a separate deployment variant to validate on the target host.
