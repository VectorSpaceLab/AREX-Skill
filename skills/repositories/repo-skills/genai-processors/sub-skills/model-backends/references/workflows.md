# Model backend workflows

## Simple Gemini processor

```python
import asyncio
import os
from genai_processors.core import genai_model

async def main():
    model = genai_model.GenaiModel(
        api_key=os.environ["GOOGLE_API_KEY"],
        model_name="gemini-2.5-flash",
    )
    print(await model("Hello, GenAI!").text())

asyncio.run(main())
```

Pass full conversation history each time if you need memory; `GenaiModel` is a
turn processor, not a stateful chat session.

## Structured output before a second model

The trip-request examples use this pattern:

1. Add current-date context with `preamble.Suffix`.
2. Call a fast model with `response_schema=TripRequest` and
   `response_mime_type='application/json'`.
3. Use a part processor to emit either an error substream or normalized trip
   text.
4. Route valid output to a second model with `switch.Switch` and
   `processor.parallel_concat`.

This is a useful defense against prompt injection: the first model has a narrow
schema and no tools, while the second model sees normalized structured data.

## Function calling loop

```python
from google.genai import types as genai_types
from genai_processors.core import function_calling, genai_model

def get_weather(city: str) -> str:
    """Returns the weather for a city."""
    return f"Weather in {city}: sunny"

tools = [get_weather]
model = genai_model.GenaiModel(
    api_key=api_key,
    model_name="gemini-2.5-flash",
    generate_content_config=genai_types.GenerateContentConfig(
        tools=tools,
        automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
    ),
)
agent = function_calling.FunctionCalling(model=model, fns=tools)
```

For realtime or async tools, set `is_bidi_model=True` and choose whether tool
results should be `SILENT`, `WHEN_IDLE`, or `INTERRUPT`.

## MCP tools

- Demo/local/remote MCP sessions are shown in the chat example.
- Pass an MCP session in both model tools and `FunctionCalling(fns=[session])`.
- For remote sessions, do not hard-code headers or API keys in generated code.
- For local sessions, treat the MCP server command as executable code; verify it
  is trusted before launching it.

## Live API versus client-side realtime

Use `live_model.LiveProcessor` when the backend is a Gemini Live-capable model
and the model should maintain bidirectional streaming state server-side.

Use `realtime.LiveProcessor(turn_processor=...)` when you want to wrap any
turn-based processor, use a rolling prompt, customize turn triggers, or run a
hackable client-side conversation loop.

## Local backends

- `OllamaModel`: start `ollama serve`, pull a model, then construct the wrapper.
- `TransformersModel`: install `transformers` and PyTorch; avoid model download
  in smoke tests unless the user explicitly approves it.
- `LangChainModel`: supply a LangChain `BaseChatModel` and optional system
  instruction or prompt template.
- `OpenRouterModel`: supply an OpenRouter API key and model name; keep site
  metadata optional.

## Validate without spending tokens

```bash
python sub-skills/model-backends/scripts/smoke_models.py
```

This checks wrapper imports and signatures only. It does not call Gemini,
OpenRouter, Ollama, MCP servers, LangChain providers, or HuggingFace downloads.
