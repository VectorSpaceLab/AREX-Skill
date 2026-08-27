---
name: genai-processors
description: "Route GenAI Processors tasks to the right workflow guide."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# GenAI Processors

GenAI Processors is a composable Python library for building AI pipelines with
shared content types, async processor composition, model wrappers, and
multimodal I/O.

Use this repo skill when the task mentions any of the following:

- `Processor`, `PartProcessor`, `ProcessorPart`, `ProcessorContent`, or
  `ContentStream`.
- Model wrappers such as `GenaiModel`, `LiveProcessor`, `OllamaModel`,
  `TransformersModel`, `FunctionCalling`, `LangChainModel`, `OpenRouterModel`,
  or the ADK bridge.
- Audio/video/PDF/web/file connectors, speech-to-text, text-to-speech, VAD,
  realtime streams, or live agent pipelines.
- CLI demos, research agents, live commentator / illustrator / widgets applets,
  or AI Studio WebSocket backends.

## Read this first

- `references/install.md` for install variants and the minimal smoke check.
- `references/repo-provenance.md` for the source snapshot used to build this skill.
- `references/repo-routing-metadata.json` for import routing metadata.
- `references/troubleshooting.md` for cross-cutting setup and runtime failures.

## Route map

### `sub-skills/core-composition/`
Use for processor composition, content types, stream utilities, caching,
routing, tracing, and text/templating helpers.

Typical prompts:
- "How do I build a custom processor?"
- "How do `ContentStream` and `ProcessorPart` work?"
- "How do I cache or trace a processor pipeline?"
- "How do I branch a stream with `Switch` or `parallel`?"

### `sub-skills/model-backends/`
Use for Gemini, Live API, realtime conversation loops, function calling, MCP,
Ollama, Transformers, LangChain, OpenRouter, ADK, and the example backends.

Typical prompts:
- "Which model wrapper should I use?"
- "How do I wire tool calls or MCP sessions?"
- "How do I switch between Gemini, Ollama, and local Transformers?"
- "How do I build a realtime or function-calling agent?"

### `sub-skills/multimodal-i-o/`
Use for audio/video/PDF/web/file connectors, speech and TTS, VAD, rate-limited
audio, event detection, windowing, timestamps, and document fetchers.

Typical prompts:
- "How do I capture microphone or camera input?"
- "How do I transcribe audio or synthesize speech?"
- "How do I extract content from PDFs, URLs, GitHub, or Drive?"
- "How do I manage realtime audio or video streams?"

### `sub-skills/examples-and-apps/`
Use for the CLI demos, research agent, trip request workflow, live commentator,
live illustrator, widgets, AI Studio applets, and websocket server helpers.

Typical prompts:
- "How do I run or adapt one of the example CLIs?"
- "How does the research agent fit together?"
- "How do the AI Studio applets talk to the backend?"
- "How do I build a full end-to-end demo around these processors?"

## Quick install

For the core library:

```bash
pip install genai-processors
```

Add `genai-processors[contrib]` when you need the bundled LangChain/OpenRouter
helpers. The more specialized example stacks may also need extra runtime
packages such as `pyaudio`, `av`, `google-adk`, `transformers`, or the Google
Cloud Speech/Text-to-Speech clients. See `references/install.md`.

## Minimal smoke check

```bash
python -c "import genai_processors; print(genai_processors.__version__)"
```

For a slightly stronger check, run the bundled smoke script:

```bash
python scripts/check_install.py
```

## How to choose a route

- Start with `core-composition` if the task is about processor mechanics,
  content typing, stream manipulation, or reusable wrappers.
- Start with `model-backends` if the task is about model choice, tool calls,
  local backends, or multi-agent orchestration.
- Start with `multimodal-i-o` if the task is about the inputs and outputs the
  processors consume or emit.
- Start with `examples-and-apps` if the task is about running or adapting a
  complete demo, CLI, or applet.

If a task touches more than one route, read the owning sub-skill first and then
follow its cross-links instead of duplicating guidance here.
