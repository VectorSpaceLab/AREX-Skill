# Troubleshooting

Use this reference when the serving or runtime surface fails after the package is installed.

## Fast triage

- `funasr-server --help` and `funasr-realtime-server --help` should work before any model download.
- The bundled HTTP smoke helper can verify health and model listing without transcription input.
- The bundled MCP helper must keep stdout reserved for JSON-RPC only.
- If the issue is model-family choice or vLLM compatibility, route to `llm-asr-and-vllm` instead of debugging the serving layer.

## Failure matrix

| Surface | Likely signal | Common cause | Recovery |
|---|---|---|---|
| HTTP API startup | Import error mentioning server dependencies | Missing `fastapi`, `uvicorn`, or `python-multipart` | Install the HTTP extras, then rerun the server help and startup check. |
| HTTP API startup | Server starts, but the first model load fails | Base ASR runtime missing `torch` or the selected model cannot load | Install the core runtime dependencies first, then retry with a simple model alias such as `sensevoice`. |
| HTTP API request | 400 response or a custom model does not load | Bad `model`, `model-path`, or hub selection | Recheck the alias, use `--model-path` only when you really have a local model, and confirm the hub matches the artifact location. |
| Browser / HTTP access | CORS rejection or port busy error | Port conflict or missing trusted origin | Pick another port and repeat `--cors-origin` with the browser origin you actually need. |
| OpenAI verbose JSON | Missing speaker labels or unexpected language | `spk=true` was omitted, the speaker model was not configured, or the language hint overrode detection | Request `spk=true`, provide a speaker model, and remember that an explicit language hint wins over backend detection. |
| Realtime output | Only partials appear, or the final transcript is delayed | Wrong endpoint mode, too-small chunks, missing `START` / `STOP` / `COMMIT`, or a sample-rate mismatch | Use 16 kHz mono PCM, match the client window to the server mode, and verify the final control message arrives. |
| Realtime output | The connection closes before final text arrives | Keepalive or timeout values are too aggressive | Increase the ping timeout or disable keepalive for the test. |
| MCP handshake | Client hangs, reports protocol failure, or cannot parse output | Extra logging is leaking to stdout, or the file path is not visible to the helper | Keep logs on stderr, mount or expose the audio file, and only use local file paths. |
| MCP tool call | `file not found` or `unsupported language` | The path is not mounted or the tool was called with an unsupported language code | Mount the file where the helper can see it and use one of the supported language values. |
| Runtime SDK / edge | Build or launch failure | Wrong backend, missing compile dependency, or unsupported model layout | Follow the backend-specific runtime reference and rebuild on the target hardware. |
| ONNXRuntime | Missing timestamps or empty `stamp_sents` | The model does not provide those fields or the mode lacks the supporting model | Use a timestamp-capable model and confirm that `2pass` also has VAD plus online punctuation. |
| GGUF / Triton | Backend flag or engine build rejected | The binary was not built for that backend, or the plan is not portable to the current GPU | Rebuild for the target backend or architecture and avoid reusing a plan on unsupported hardware. |

## Specific recovery hints

### HTTP API

- If startup prints that extra packages are missing, install the HTTP server dependencies first.
- If the server can start but cannot load the requested model, switch to a simpler alias and verify the hub or local path.
- If the smoke helper only prints health and model listing, that is expected when you do not provide `--audio-path`.

### Realtime WebSocket

- Start with `START` in client mode.
- Use `COMMIT` only when `--endpoint-mode client` is active.
- Use `STOP` when the session is finished.
- Tune `partial-window-sec` downward if long segments are being re-decoded too often.
- Tune the chunk size upward a little if the server is thrashing on very small windows.

### MCP

- The helper is intentionally local-file only.
- The helper should not emit non-JSON lines to stdout.
- If you need a mount point for a containerized helper, expose the audio directory and pass the mounted path into the tool call.

### Runtime / edge

- ONNXRuntime two-pass inference needs both VAD and online punctuation.
- TensorRT plans are not portable across arbitrary GPU architectures or TensorRT versions.
- GPU backend selection only works when the binary was built with that backend support.
- Prefer reference docs for edge/runtime build steps; do not treat them as default one-command smoke paths.

## Boundary notes

- Do not use this reference to troubleshoot batch transcription, subtitle writing, or punctuation cleanup.
- Do not use this reference for Nano / GLM / Qwen3 model-family selection; that belongs in `llm-asr-and-vllm`.
