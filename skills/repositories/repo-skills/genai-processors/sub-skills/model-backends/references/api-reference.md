# Model backend API reference

## Turn-based Gemini

`genai_processors.core.genai_model.GenaiModel` wraps the Gemini API as a
`Processor`.

Constructor verified from the installed package:

```python
GenaiModel(
    api_key: str,
    model_name: str,
    generate_content_config=None,
    debug_config=None,
    http_options=None,
    stream_json: bool = False,
)
```

Important behavior:

- Buffers input before calling the API.
- Does not maintain conversation state; pass conversation history yourself or
  use a realtime/window processor.
- Streams Gemini responses as `ProcessorPart`s and attaches response metadata.
- When a response schema is present and `stream_json=False`, structured JSON is
  parsed via `StructuredOutputParser`.

`ImagePreprocess` can upload images to the Gemini File API before model calls
when repeated image tokenization should be avoided.

## Gemini Live API

`genai_processors.core.live_model.LiveProcessor` connects to Gemini Live API.
It consumes default-substream content via client content and `realtime`
substream media/text via realtime input.

Use only Live-capable model names. Live responses may contain audio/text parts,
transcriptions, tool calls, cancellations, usage metadata, go-away messages, or
session resumption metadata.

## Client-side realtime wrapper

`genai_processors.core.realtime.LiveProcessor` wraps any turn-based processor:

```python
realtime.LiveProcessor(
    turn_processor,
    duration_prompt_sec=600,
    trigger_model_mode=realtime.AudioTriggerMode.FINAL_TRANSCRIPTION,
    debug_latency=False,
)
```

It maintains a rolling prompt, reacts to `StartOfSpeech`, `EndOfSpeech`, and
`END_OF_TURN`, supports interruption, and can use `window.RollingPrompt` or
custom history compression.

## Function calling and MCP

`FunctionCalling` constructor:

```python
FunctionCalling(
    model,
    *,
    is_bidi_model=False,
    substream_name='function_call',
    pre_processor=None,
    fns=None,
    max_function_calls=None,
)
```

Rules:

- Put the same tools in the model config and in `FunctionCalling(fns=...)`.
- Disable model automatic function calling when GenAI Processors will execute
  the tools.
- Async functions or `is_bidi_model=True` run tools in the background.
- Tool results may use `SILENT`, `WHEN_IDLE`, or `INTERRUPT` scheduling.
- MCP client sessions can be passed directly in `fns`; `mcp.mcp_tools_to_callables`
  converts MCP tools when lower-level control is needed.

## Local and contributed model wrappers

| Wrapper | Constructor highlights | Notes |
| --- | --- | --- |
| `OllamaModel` | `model_name=''`, `host=None`, `generate_content_config=None`, `keep_alive=None`, `stream_json=False` | Requires running Ollama and pulled model. |
| `TransformersModel` | `model_name=''`, `generate_content_config=None`, `log_chat_template=False`, `tool_response_format='string'` | Requires `transformers`; real model execution also needs PyTorch. |
| `LangChainModel` | `model`, `system_instruction=()`, `prompt_template=None` | Wraps a LangChain `BaseChatModel`; tool translation is intentionally limited. |
| `OpenRouterModel` | `api_key`, `model_name`, `base_url=None`, `site_url=None`, `site_name=None`, `generate_content_config=None` | Uses OpenRouter-compatible HTTP API and maps content to/from `ProcessorPart`. |

## ADK and example model helpers

- `core.adk.ProcessorAgent` adapts a processor factory into an ADK agent.
- `examples/models.py` provides a flag-based model selector for examples only;
  it is not a general-purpose public selector.
- `examples/smart_model.py` demonstrates `CriticReviser` and a recursive
  `Researcher` built from `GenaiModel` plus `FunctionCalling`.
