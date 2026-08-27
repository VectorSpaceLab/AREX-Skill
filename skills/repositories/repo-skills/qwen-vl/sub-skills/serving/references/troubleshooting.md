# Qwen-VL serving troubleshooting

Use this when preparing commands or debugging a requested launch of the bundled
Gradio or OpenAI-compatible service. Prefer `--help`, import probes, and config
inspection before starting a listener.

## Fast non-listener checks

```bash
python scripts/web_demo_mm.py --help
python scripts/openai_api.py --help
python - <<'PY'
import gradio, modelscope, fastapi, uvicorn, pydantic, sse_starlette
print('serving imports ok')
PY
```

These checks do not load checkpoints or bind ports. If they fail, fix the
installation before attempting service startup.

## Dependency and import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: gradio` or `modelscope` | Web demo extras not installed. | Install the Gradio demo extra packages listed in [service reference](service-reference.md#dependency-groups). |
| `ModuleNotFoundError: fastapi`, `uvicorn`, `openai`, `pydantic`, or `sse_starlette` | OpenAI API extras not installed. | Install the OpenAI API extra packages listed in [service reference](service-reference.md#dependency-groups). |
| `transformers_stream_generator`, `tiktoken`, or `accelerate` missing during model load | Base Qwen-VL requirements missing. | Install the base requirements before service extras. |
| Version or schema errors from Pydantic/FastAPI | Environment differs from the verified construction environment or resolver upgraded packages. | Recreate a clean environment from the repo requirement groups, then rerun `--help` and import probes. |

## Checkpoint and model-loading failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `qwen.tiktoken` missing | The checkpoint was cloned without Git LFS or downloaded incompletely. | Re-download the checkpoint with all tokenizer files and weight shards. |
| Missing shard or safetensors/bin files | Partial checkpoint directory. | Verify every shard listed by the checkpoint index is present before launching. |
| Model responds like a base model or ignores instructions | Loaded `Qwen-VL` instead of `Qwen-VL-Chat`, or inherited the OpenAI API script's text-chat default. | Pass an explicit chat checkpoint via `-c` / `--checkpoint-path`. |
| Startup triggers unexpected network download | Checkpoint id was used instead of a local path, or cache is empty. | Use a local checkpoint directory if offline or bandwidth-limited; otherwise warn the user before download. |
| CUDA out of memory at startup | Model too large for selected GPU placement. | Use a suitable GPU, reduce other GPU load, try the Int4 deployment variant only after validating quantization dependencies, or use `--cpu-only` for a slow functional path. |
| CPU launch appears hung | CPU-only model loading/inference is very slow. | Treat CPU as functional but performance-limited; do not use it as proof of practical service readiness. |

## Binding, networking, and CORS

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Address already in use` | Port occupied. | Pick another `--server-port` or stop the conflicting process. |
| Browser cannot reach the service from another machine | Bound to `127.0.0.1` or blocked by firewall. | Only if exposure is intended, use `--server-name 0.0.0.0`, open the firewall/proxy path, and add authentication outside the script. |
| Service is reachable too broadly | Bound to `0.0.0.0`, Gradio `--share` was used, or proxy is public. | Return to `127.0.0.1`, remove `--share`, or put the service behind a controlled proxy. |
| Browser CORS errors are absent but security review fails | API script allows all origins, credentials, methods, and headers. | For production, restrict CORS in a fork/wrapper or terminate through a proxy that enforces allowed origins. |

## OpenAI-compatible API issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `GET /v1/models` reports `gpt-3.5-turbo` | The endpoint returns a static compatibility model card. | Treat it as a shim; the actual checkpoint is selected only by server startup `--checkpoint-path`. |
| `stream: true` returns HTTP 400 | Streaming is intentionally disabled in the current request handler. | Set `stream` to `false` or omit it. Do not rely on SSE. |
| Function calling with stream fails | Function calling is not implemented for stream mode. | Use non-streaming requests for function-call experiments. |
| `Invalid request: Expecting at least one user message` | `messages` lacks a user role. | Include at least one `{"role": "user", "content": ...}` message. |
| `Expecting role assistant before role function` | A `function` role message is not immediately following an assistant turn. | Maintain user/assistant/function order accepted by the parser. |
| Function call is returned as plain text | Model did not emit the expected `Action:` and `Action Input:` markers. | Tighten the function description and parameters; remember this adapter parses ReAct text rather than native OpenAI tool JSON. |
| `max_length` appears ignored | The schema accepts it, but the non-streaming chat path does not pass it to `model.chat`. | Control generation with supported generation config, `temperature`, `top_p`, and checkpoint settings instead. |

## Gradio demo issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--share` fails or never returns a public URL | Gradio share service or outbound network unavailable. | Remove `--share` for local use, or retry on a network that allows the share tunnel. |
| Uploaded image disappears or rendered box image cannot be written | Temporary directory is not writable or was cleaned. | Set a writable `GRADIO_TEMP_DIR` before launch, or use a host/container temp path with enough space. |
| Grounding boxes are absent | Model response did not contain usable `<ref>` / `<box>` markup, or the latest picture could not be resolved. | Route prompt/markup questions to [inference](../../inference/SKILL.md) and ensure the image was uploaded in the same conversation. |
| CJK text or box-rendered output has font issues in a container | Container lacks suitable fonts. | Install a font that covers the required language; the source Dockerfiles added a CJK font for this reason. |

## Docker deployment issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Docker build cannot find a Dockerfile | This generated sub-skill does not bundle Dockerfiles. | Use Docker only with a user-provided build context containing the expected Dockerfile, or serve directly with the bundled Python scripts. |
| Build fails while cloning/downloading checkpoints | Network, Git LFS, or offline-mode mismatch. | Pre-provide the checkpoint in the build context or allow the required network/LFS access. |
| Int4 image build fails on `auto-gptq` or CUDA wheels | Quantization packages are host/CUDA/Python specific and were not part of the verified serving smoke. | Treat Int4 as an optional deployment variant; select compatible wheels and validate separately. |
| Container starts but remote clients cannot connect | Port mapping or bind address mismatch. | Ensure the container command binds `0.0.0.0` inside the container and maps host port to container port. |
| Security review rejects the container command | Public bind, permissive CORS, Gradio share, or Docker socket mount. | Remove public exposure where possible, enforce auth/proxy controls, and avoid mounting the host Docker socket for ordinary serving. |
