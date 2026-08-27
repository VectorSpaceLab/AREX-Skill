# Cross-cutting troubleshooting

Use this root troubleshooting page for package-wide failures. For workflow
specifics, route to the nearest sub-skill troubleshooting page.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `speech-to-speech` command not found | Package not installed in the active environment or scripts path not active | Reinstall into the active Python environment and run `python -m pip show speech-to-speech`; then reopen the shell if needed. |
| Import succeeds but CLI help fails | Optional runtime import side effect or dependency conflict | Run `speech-to-speech --help` with `OPENAI_API_KEY=''` and inspect the first import error; avoid installing all extras together. |
| Optional backend says install an extra | Selected backend has a registered `required_extra` | Install the named extra only, for example `speech-to-speech[faster-whisper]` or `speech-to-speech[webrtc]`. |
| DeepFilterNet/NumPy conflict | Optional audio enhancement constraints conflict with Pocket TTS or other packages | Keep DeepFilterNet in a separate environment or leave enhancement disabled when using Pocket TTS. |

## CLI/API misuse

- Use exactly one command: `serve`, `talk`, or `local`.
- `talk` needs a full Realtime URL and does not accept backend or server flags.
- `serve` owns host/port/backend selection and does not accept local audio
  flags.
- `local` runs loopback server plus packaged audio client and rejects `--host`.
- Removed legacy modes such as `socket` or raw websocket modes should not be
  resurrected; migrate to the command family.

## Network and exposure

- `serve` defaults to loopback for a reason. Use `--host 0.0.0.0` only on a
  trusted network or behind a gateway.
- The optional LLM proxy performs no package-level authentication.
- Browser demo WebSocket URLs are opened by the browser, while WebRTC SDP proxy
  requests are opened by the demo server. Docker hostnames can differ.
- Browsers require HTTPS or localhost for microphone/camera access.

## Model/runtime problems

| Area | Key checks |
| --- | --- |
| Qwen3-TTS Linux | Match `qwentts-cpp-python` wheel to CUDA runtime, or use CPU wheel; distinguish GGML and torch backend modes. |
| Apple Silicon | Use `--mac-optimal-settings` as defaults only; verify MLX/MPS on actual macOS hardware. |
| Direct audio input | Use `--stt none --llm_backend chat-completions` with an explicitly audio-capable model. |
| Offline | Warm exact selected assets before setting offline flags; remote Responses API still needs network. |
| Benchmarks | Separate cold-load from warm inference and ask before downloads/long runs. |

## Session and conversation issues

- `session_limit_reached`: every pipeline unit is busy; increase
  `--num_pipelines` or reduce concurrency.
- `conversation_already_has_active_response`: wait for `response.done` before
  the next `response.create`.
- Choppy or premature turns: tune VAD minimum silence/speech and Smart Turn
  thresholds together.
- Missing live transcript: verify live transcription is enabled and selected
  STT supports useful partial updates.
- Tool result never spoken: send `conversation.item.create` with the tool output,
  then one follow-up `response.create` if a spoken answer is needed.

## Where to go next

- Command/parser/session-pool issues:
  [cli-and-server troubleshooting](../sub-skills/cli-and-server/references/troubleshooting.md).
- Realtime event/client/WebRTC/LLM-proxy issues:
  [realtime-api troubleshooting](../sub-skills/realtime-api/references/troubleshooting.md).
- Backend/model/language/Qwen/tool-prompt issues:
  [components-and-backends troubleshooting](../sub-skills/components-and-backends/references/troubleshooting.md).
- Browser demo/search/camera/OAuth/UI issues:
  [browser-demo troubleshooting](../sub-skills/browser-demo/references/troubleshooting.md).
