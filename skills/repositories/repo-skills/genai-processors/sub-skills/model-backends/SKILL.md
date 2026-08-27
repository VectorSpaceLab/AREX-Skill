---
name: model-backends
description: "Use GenAI Processors model wrappers, function calling, MCP, and
  local backends."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Model backends

Use this sub-skill when a task is about model invocation, realtime model loops,
tool/function calling, MCP tools, local backends, or model-selector examples.

## Read when

- The task names `GenaiModel`, `live_model.LiveProcessor`,
  `realtime.LiveProcessor`, `FunctionCalling`, or `ImagePreprocess`.
- The task asks about Gemini API, Gemini Live API, tool calls, async tools,
  `FunctionResponse.scheduling`, or MCP sessions.
- The task asks to use Ollama, Transformers, LangChain, OpenRouter, ADK, or
  example backend selection.
- The task needs to diagnose `GOOGLE_API_KEY`, live model names, Ollama server
  errors, missing PyTorch, or disabled automatic function calling.

## Boundaries

This sub-skill owns model-facing processors and orchestration. It does not own
low-level device/document input; use `../multimodal-i-o/` for audio/video/PDF/
web/Drive/GitHub sources. Use `../examples-and-apps/` for complete CLI/app
wiring.

## Backend selection guide

- Use `core.genai_model.GenaiModel` for turn-based Gemini API calls.
- Use `core.live_model.LiveProcessor` for Gemini Live API bidirectional streams
  with Live-capable model names.
- Use `core.realtime.LiveProcessor` to wrap any turn-based processor into a
  client-side realtime loop with interruption and rolling prompt state.
- Use `core.function_calling.FunctionCalling` when the library, not the model
  client, should execute functions or MCP tools.
- Use `core.ollama_model.OllamaModel` for a running local Ollama server.
- Use `core.transformers_model.TransformersModel` for local HuggingFace
  Transformers; install PyTorch before real model execution.
- Use `contrib.langchain_model.LangChainModel` or
  `contrib.openrouter_model.OpenRouterModel` for contributed wrappers.
- Use `core.adk.ProcessorAgent` for wrapping a processor as an ADK agent.

## References and scripts

- `references/api-reference.md` lists constructors, model wrappers, and support
  helpers.
- `references/workflows.md` shows Gemini, realtime, function-calling, MCP, and
  local-backend patterns.
- `references/troubleshooting.md` covers credentials, service availability,
  PyTorch, Live API model names, and tool-call configuration.
- `scripts/smoke_models.py` imports wrappers and prints key signatures without
  contacting any service.

## Native evidence anchors

Model behavior is grounded by source modules under `genai_processors/core/`,
`genai_processors/contrib/`, `genai_processors/mcp.py`, and tests such as
`genai_model_test.py`, `live_model_test.py`, `realtime_test.py`,
`function_calling_test.py`, `mcp_test.py`, `ollama_model_test.py`,
`transformers_model_test.py`, and `adk_test.py`. Example evidence includes
`examples/models.py`, `examples/smart_model.py`, `examples/chat.py`,
`examples/trip_request_cli.py`, `examples/trip_request_cli_ollama.py`, and
`examples/trip_request_adk/agent.py`.

## Usability checkpoints

A good answer using this sub-skill should:

- State whether the model wrapper buffers full input or streams bidirectionally.
- Identify required credentials or local services before showing runnable code.
- Disable model-side automatic function calling when wrapping with
  `FunctionCalling` and executing tools in the processor loop.
- Keep model selection separate from I/O and full app concerns unless the task
  explicitly spans those areas.
- Treat external API calls, model downloads, and service startup as non-smoke
  operations requiring user-controlled credentials and budget.
