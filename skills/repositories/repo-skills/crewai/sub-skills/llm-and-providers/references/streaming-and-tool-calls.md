# Streaming and Tool Calls

This reference covers LLM-level streaming, direct `LLM.call()`/`acall()` behavior, tool-call provider requirements, `function_calling_llm` compatibility concerns, and structured response pitfalls. For Crew/Agent object placement, use [../../core-runtime/SKILL.md](../../core-runtime/SKILL.md). For event listener implementation and observability, use [../../observability-and-hooks/SKILL.md](../../observability-and-hooks/SKILL.md).

## Streaming Basics

Enable provider streaming with `stream=True` on an `LLM` object:

```python
from crewai import LLM

llm = LLM(
    model="openai/gpt-4o-mini",
    temperature=0,
    stream=True,
)

text = llm.call("Write one sentence about CrewAI streaming.")
```

For direct LLM calls, CrewAI still returns the final text or tool-call result. During the call it emits stream chunk events with text chunks, caller context, response IDs when available, and call IDs.

## Crew and Flow Streaming Outputs

`Crew(stream=True)` and `Flow(stream=True)` change kickoff behavior: the kickoff returns a streaming output wrapper that must be iterated before the final result is available.

```python
streaming = crew.kickoff(inputs={"topic": "LLM config"})
for chunk in streaming:
    print(chunk.content, end="")

final_output = streaming.result
```

The streaming output stores chunks, exposes completion/cancellation state, and keeps tool-call chunks separate from text chunks. Accessing `.result` before iteration completes raises a runtime error.

## Async Calls

Built-in providers expose `acall()` for asynchronous calls. If `stream=True`, the provider may still aggregate and return the final result while emitting chunk events. For custom LLMs, implement `acall()` only if the backend is truly async-safe; otherwise raise `NotImplementedError` with a clear message.

```python
response = await llm.acall([
    {"role": "user", "content": "Return compact JSON with one key."}
])
```

## Tool Calls

CrewAI passes tool schemas and `available_functions` into `LLM.call()`:

```python
schema = {
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": "Get the current temperature for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}

result = llm.call(
    messages=[{"role": "user", "content": "Temperature in Paris?"}],
    tools=[schema],
    available_functions={"get_temperature": lambda city: "22 C"},
)
```

Provider requirements:

- `supports_function_calling()` must be true for reliable tool use.
- Tool names may be sanitized for provider compatibility; avoid spaces and punctuation in names.
- Streaming tool calls emit tool-call chunks as arguments accumulate; do not assume every stream event contains text.
- Some reasoning or older provider models have limited or no function-calling support. Use a simpler `function_calling_llm` or a model family known to support tools when tool calls are central.

## `function_calling_llm`

CrewAI allows a separate function-calling model at agent or crew scope. This is useful when the main model is strong for reasoning/writing but weak, expensive, or unsupported for tools.

Guidance:

- Use a tool-capable, low-latency model for `function_calling_llm`.
- Keep the main `llm` and `function_calling_llm` provider credentials both configured.
- If the tool-calling model does not support stop sequences or streaming tool deltas, disable streaming for that part or choose a compatible fallback.
- Placement details belong in [../../core-runtime/SKILL.md](../../core-runtime/SKILL.md); provider support checks belong here.

## Structured Responses

CrewAI supports structured LLM calls by using `response_format` on `LLM(...)` and/or response models supplied during direct calls. Built-in provider behavior varies:

- OpenAI supports JSON object formats and Pydantic schemas in supported model/API combinations.
- OpenAI Responses API (`api="responses"`) has additional stateful and built-in-tool options such as `store`, `previous_response_id`, `builtin_tools`, `auto_chain`, and `parse_tool_outputs`.
- Anthropic native structured output support is model-family dependent; older models may require a tool-based fallback.
- Gemini and Bedrock can convert Pydantic schemas into provider-specific tool/schema formats, but model support differs.
- Azure response-format support differs between Azure AI Inference endpoints, Azure OpenAI endpoints, and Responses API delegation.

Example:

```python
from pydantic import BaseModel
from crewai import LLM

class Summary(BaseModel):
    title: str
    risk: str

llm = LLM(model="openai/gpt-4o-mini", response_format=Summary)
summary = llm.call("Summarize the rollout risk in two fields.")
```

If output validation fails, first check whether the selected model/API supports native schema output. Then simplify the schema, lower temperature, or move schema validation to task-level output handling.

## Streaming Compatibility Matrix

| Scenario | Safer choice | Common failure |
| --- | --- | --- |
| Text-only live UX | `stream=True` on a native provider with simple prompts | Empty chunks or delayed final output from provider-specific streaming behavior. |
| Tool calls with streaming | OpenAI/Gemini/Bedrock/Anthropic model known to emit tool deltas | Tool arguments arrive across multiple events; consumers assume complete JSON per chunk. |
| Local OpenAI-compatible server | Start with `stream=False`, then enable streaming after basic calls work | Server implements Chat Completions but not streaming/tool-call deltas. |
| Structured output + streaming | Prefer non-streaming unless provider explicitly supports both together | Partial JSON chunks cannot be parsed until final completion. |
| Multimodal + tools | Pick a provider/model that supports both the file modality and function calling | Model supports images but not tools, or tools but not file content blocks. |

## Multimodal Interactions

LLM provider selection affects multimodal support, but file payload construction belongs in [../../files-and-multimodal/SKILL.md](../../files-and-multimodal/SKILL.md). At this layer, check:

- Does the selected model support the modality: image, PDF, audio, video, or text only?
- Does the provider support files inline, uploaded, or only by provider file ID?
- Does the same model support tool calling and streaming, or do you need a text/tool fallback model?
- Is `prefer_upload` appropriate for the provider, or should files be sent inline by the files sub-skill's guidance?

## Event and Hook Routing

Streaming emits LLM stream chunk events. Transport interceptors are supported for OpenAI and Anthropic providers, but event listeners, tracing, and observability integrations are outside this sub-skill. Route those tasks to [../../observability-and-hooks/SKILL.md](../../observability-and-hooks/SKILL.md).

## Debug Checklist

When streaming or tool calls fail:

1. Reproduce with `stream=False` and no tools.
2. Add `tools` and `available_functions` with `stream=False`.
3. Enable `stream=True` only after non-streaming tool calls work.
4. Confirm the model family supports function calling.
5. Confirm credentials for both main LLM and `function_calling_llm`.
6. Avoid structured output streaming unless the provider supports the combination.
7. For local OpenAI-compatible servers, test `/v1/chat/completions` compatibility outside CrewAI before relying on tool-call deltas.

## Reference Notes

This reference bundles behavior from CrewAI streaming docs, LLM implementations, and focused streaming/tool-call tests. It does not require future agents to open source tests or docs.
