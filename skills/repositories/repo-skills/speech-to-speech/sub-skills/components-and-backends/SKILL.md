---
name: components-and-backends
description: "Choose, configure, and troubleshoot speech-to-speech VAD, STT,
  LLM, and TTS backends, optional extras, language behavior, prompts, tools, and
  benchmark safety."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Components and backends

Use this sub-skill when the task is to choose or debug a VAD, STT, LLM, or TTS
component for `speech-to-speech`, including optional extras, model/device
choices, Qwen3-TTS modes, direct audio-input LLMs, language behavior, prompts,
tool calls, and benchmark planning.

## Route by question

- **Need a supported backend list or install extra:** read
  [Backend catalog](references/backend-catalog.md).
- **Need a concrete model, language, direct-audio, Qwen3, or Apple Silicon
  recipe:** read [Model and language recipes](references/model-and-language-recipes.md).
- **Need LLM prompt or tool-calling behavior:** read
  [Prompting and tools](references/prompting-and-tools.md).
- **Need latency/RTF comparison or a benchmark plan:** read
  [Backend benchmarking](references/backend-benchmarking.md) before running any
  model-heavy measurement.
- **Need optional dependency, CUDA wheel, model cache, language, or voice
  troubleshooting:** read [Troubleshooting](references/troubleshooting.md).
- **Need command shape, `serve`/`local`/`talk`, host/port, VAD flags, or session
  capacity:** route to [cli-and-server](../cli-and-server/SKILL.md).
- **Need Realtime event lifecycle, WebSocket/WebRTC, or client protocol:** route
  to [realtime-api](../realtime-api/SKILL.md).
- **Need the browser demo tools/search/camera/UI:** route to
  [browser-demo](../browser-demo/SKILL.md).

## Safe operating sequence

1. Select one backend per stage with `--stt`, `--llm_backend`, and `--tts`.
   Defaults are `parakeet-tdt`, `responses-api`, and `qwen3`.
2. Install only the optional extra required by the selected backend. Do not
   install every extra just to try one component.
3. Verify parser/config behavior before model inference. Run the bundled safe
   registry inspector:
   [`scripts/inspect_backend_registry.py`](scripts/inspect_backend_registry.py).
4. For local model inference, decide the hardware/backend first: CPU/CUDA,
   Apple Silicon/MPS/MLX, remote OpenAI-compatible endpoint, or direct
   audio-input Chat Completions model.
5. For Qwen3-TTS on Linux, resolve the `qwentts-cpp-python` wheel/runtime match
   before diagnosing model code. For Apple Silicon, use the MLX quantization
   mapping described in the recipes.
6. Treat full STT/TTS benchmarks and live speech loops as optional, expensive
   validation. They may download models, require CUDA/MPS/audio devices, or use
   credentials.

## High-signal rules

- `--stt none` bypasses transcription and forwards the completed VAD audio turn
  to an LLM that supports audio input. In this package that means
  `--llm_backend chat-completions` plus an explicitly audio-capable `--model_name`.
  Do not pair `--stt none` with the default `responses-api` profile.
- `responses-api` and `chat-completions` share the `--responses_api_*` connection
  flags. They call different upstream endpoints.
- Local `transformers` and `mlx-lm` tool calling uses prompt-rendered function
  signatures and parsed `<code>...</code>` calls; remote OpenAI-compatible
  backends pass tools structurally.
- `--mac-optimal-settings` supplies macOS defaults only. Any explicit backend,
  model, global device, or component-device flag wins over the preset.
- Backend registry import/config checks do not prove that a large model can run.
  Record actual model inference separately when a task requires it.
