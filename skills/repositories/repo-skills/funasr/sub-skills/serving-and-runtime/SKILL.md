---
name: serving-and-runtime
description: "Own FunASR serving, realtime, MCP, client, and edge-runtime
  guidance without mixing in core ASR or vLLM family selection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# FunASR serving and runtime

Use this sub-skill when the user wants to expose FunASR over HTTP, WebSocket, MCP, browser or desktop clients, or runtime SDK / ONNX / GGUF / Triton deployment guidance. Keep it separate from core ASR inference, model choice, text normalization, training/export, and LLM-family routing.

## Fast route selection

- OpenAI-compatible HTTP API, health checks, `/v1/models`, `/v1/audio/transcriptions`, or the native `/asr` route → [`references/openai-api.md`](references/openai-api.md)
- Realtime WebSocket serving, chunk sizing, endpoint mode, hotwords, or final session flushes → [`references/realtime-websocket.md`](references/realtime-websocket.md)
- MCP server, browser/client integrations, LangChain, Dify, or voice-input workflows → [`references/mcp-and-client-integrations.md`](references/mcp-and-client-integrations.md)
- ONNXRuntime, libtorch, GGUF/llama.cpp, Triton, or other edge/runtime guidance → [`references/runtime-sdk-and-edge.md`](references/runtime-sdk-and-edge.md)
- Missing packages, CORS, port conflicts, empty realtime output, MCP path problems, or build/backend caveats → [`references/troubleshooting.md`](references/troubleshooting.md)
- Nano / GLM / Qwen3 / vLLM family choice or acceleration caveats → route to `llm-asr-and-vllm`
- Plain batch transcription, subtitles, audio decoding, or local model selection → route to `python-asr-pipelines`

## Minimum facts to collect

1. Which surface is needed: HTTP API, realtime WebSocket, MCP, browser/client integration, or runtime/edge deployment?
2. Does the user want a packaged CLI smoke, a small helper script, or a deployment reference?
3. What runtime target matters: CPU, CUDA, MPS, ONNXRuntime, GGUF, Triton, or a service wrapper around a local model?
4. Does the user need `verbose_json`, speaker labels, endpoint mode control, or deterministic hotword post-processing?
5. Is the integration local-only, mounted-file MCP access, or a remote service URL?

## Operating workflow

1. Prefer the packaged CLIs (`funasr-server`, `funasr-realtime-server`) for service guidance and smoke checks.
2. Use [`scripts/openai_api_smoke_test.py`](scripts/openai_api_smoke_test.py) for a safe HTTP client that can stop after health/model checks when no audio file is supplied.
3. Use [`scripts/funasr_mcp_server.py`](scripts/funasr_mcp_server.py) for a small stdio tool when the caller needs agent-style local file transcription.
4. Keep Docker images, system-service launchers, and native runtime build instructions in the reference docs rather than as default runnable helpers.
5. Cross-check the native candidates listed in the integration plan before claiming this sub-skill is ready.

## Safety and boundary notes

- Do not drift into generic Python ASR, punctuation cleanup, training/export, or vLLM family choice.
- The bundled helpers must remain self-contained, cross-platform where practical, and safe by default.
- Reference docs may show command shapes and caveats, but they should not imply that the original source-tree examples must be run verbatim.
- Do not claim the edge/runtime paths are production-ready until the referenced backend and build requirements are met.
