# Example and app workflows

Source file names below are provenance labels for the distilled patterns in this
reference. Do not require the original checkout to run or read those files when
using this generated skill.

## Chat CLI

`examples/chat.py` is a turn-by-turn terminal chat that can fetch URLs/PDFs and
optionally connect to MCP tools. It demonstrates:

- `text.terminal_input` / `text.terminal_output` for async CLI I/O.
- `text.UrlExtractor`, an example URL fetcher, and `pdf.PDFExtract` for
  multimodal document input.
- `models.turn_based_model` for backend selection.
- `function_calling.FunctionCalling` with optional MCP sessions.
- `trace_file.SyncFileTrace` via a `--trace_dir` flag.

Adapt it when building a text/document agent. Route model details to
`../model-backends/` and URL/PDF details to `../multimodal-i-o/`.

## Trip request CLIs and ADK example

`examples/trip_request_cli.py` and `examples/trip_request_cli_ollama.py` show a
structured-output-first pattern:

1. normalize free-form user text into a `TripRequest` dataclass,
2. route validation errors to an `error` substream,
3. pass valid structured content to a second planning model,
4. hide slow model latency with an acknowledgment branch.

`examples/trip_request_adk/agent.py` wraps the same idea as an ADK agent.
Use this family when the target app needs schema validation, prompt-injection
narrowing, or fast acknowledge + slower synthesis.

## Research agent

`examples/research/` decomposes a query into topics, researches each topic, then
synthesizes the result. It uses custom dataclass parts, PartProcessors,
`JinjaTemplate` verbalization, Google Search tool configuration, and a final
synthesis model. It is the right evidence source for multi-step research-style
pipelines.

## Model selector and smart model helpers

`examples/models.py` is a flag-based helper for the examples only. It selects
Gemini, Ollama, LangChain, or Transformers and can wrap Gemini with
`smart_model.CriticReviser` or `smart_model.Researcher` when the model name has
`critic:` or `research:` prefixes. Do not treat it as a general library API;
copy the selection pattern only when writing a demo.

## Realtime CLI examples

- `live_simple_cli.py`: microphone + camera/screen input into Gemini Live API,
  then speaker output.
- `realtime_simple_cli.py`: microphone -> Google Speech-to-Text -> client-side
  `realtime.LiveProcessor` -> Text-to-Speech -> rate-limited speaker output.
- `speech_to_text_cli.py`: direct STT inspection.
- `text_to_speech_cli.py`: direct TTS playback.
- `vad_cli.py`: local VAD with audio-to-WAV and a Gemini turn processor.
- `pdf_cli.py`: local PDF extraction and part printing.

These examples require credentials and/or devices. Use them as blueprints, not
as automated smoke tests.

## MCP demo server

`examples/mcp_server.py` provides demo/local/remote MCP sessions:

- demo in-memory server with arithmetic and weather-style tools,
- local stdio server from a shell command,
- remote streamable-HTTP server with optional headers.

Treat local MCP commands as trusted executable inputs and remote headers as
secret-bearing configuration.

## Live commentator

`examples/live_commentator/` builds an agent that actively comments on video and
audio, uses Gemini Live API, event detection, async non-blocking tools, and
`RateLimitAudio`. It is a reference for interruptible live agents that drive the
conversation rather than only responding to the user.

## Live illustrator

`examples/live_illustrator/` listens to narration and generates concept art and
illustrations asynchronously. It demonstrates non-blocking image tools, concept
art reuse, status substreams, and avoiding blocking the listener model while
images are generated.

## Widgets applet

`examples/widgets/` demonstrates async tools that stream UI widgets to a browser
via a reserved UI substream while the model continues producing text. Use it for
tasks that need side-channel UI rendering, HTML/SVG widgets, or image results
without polluting model context.
