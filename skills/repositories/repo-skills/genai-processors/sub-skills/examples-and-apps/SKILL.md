---
name: examples-and-apps
description: "Run and adapt GenAI Processors CLI demos, research agents, and AI
  Studio applets."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Examples and apps

Use this sub-skill when the task asks how to run, adapt, explain, or debug a
complete GenAI Processors example application.

## Read when

- The task mentions `examples/chat.py`, `trip_request_cli.py`,
  `trip_request_cli_ollama.py`, `live_simple_cli.py`, `realtime_simple_cli.py`,
  `speech_to_text_cli.py`, `text_to_speech_cli.py`, `vad_cli.py`, or `pdf_cli.py`.
- The task asks about the research agent, trip-request ADK example, MCP demo
  server, live commentator, live illustrator, widgets, or AI Studio applets.
- The task needs to choose which demo to adapt for a new app.
- The task needs websocket server/app UI protocol details.

## Boundaries

This sub-skill owns application-level wiring. Route lower-level questions to:

- `../core-composition/` for processor/content/stream mechanics.
- `../model-backends/` for model wrappers, function calling, MCP, and backend
  selection.
- `../multimodal-i-o/` for audio/video/PDF/web/speech connectors.

## Example families

- Text and document chat: `chat.py`, URL extraction, PDF extraction, optional
  MCP tools, terminal I/O, and tracing.
- Structured and multi-step text workflows: trip request CLIs, ADK trip request,
  research agent, critic/reviser/researcher helpers.
- Realtime audio/video CLIs: `live_simple_cli.py`, `realtime_simple_cli.py`,
  `speech_to_text_cli.py`, `text_to_speech_cli.py`, and `vad_cli.py`.
- AI Studio applets: live commentator, live illustrator, dynamic widgets, and
  their WebSocket backends via `dev.live_server`.

## Application workflow

1. Identify the closest example family rather than starting from scratch.
2. Read the relevant workflow reference and sibling sub-skills for lower-level
   APIs.
3. List credentials, local services, devices, and browser permissions before
   running anything.
4. Import-check packages and environment variables with `scripts/check_example_env.py`.
5. Run only safe `--help` or import checks first; run real app/model/audio flows
   only with user-provided credentials and device approval.
6. When adapting, preserve the processor pipeline shape and replace only the
   app-specific model, prompts, tools, sources, or renderer.

## References and scripts

- `references/workflows.md` maps each example to its purpose, key modules, and
  adaptation notes.
- `references/ai-studio-applet.md` explains the WebSocket/ProcessorPart protocol
  used by the browser applets.
- `references/troubleshooting.md` covers common app/demo failures.
- `scripts/check_example_env.py` prints non-secret readiness signals and imports
  app-support modules without running examples.

## Native evidence anchors

Evidence comes from the `examples/` tree, documentation under
`documentation/docs/examples/` and `documentation/docs/rapid-prototyping/`, and
source modules `genai_processors/dev/live_server.py` and
`genai_processors/examples/__init__.py`.

## Usability checkpoints

A good answer using this sub-skill should:

- Name the closest example and explain why it is the right starting point.
- Separate package/import checks from API calls, device opens, model downloads,
  or WebSocket server startup.
- Preserve secret safety: never print keys or embed them in generated code.
- Include how to stop long-running CLIs/servers and how to inspect traces.
- Cross-link to sibling sub-skills for detailed APIs rather than copying their
  content into application guidance.
