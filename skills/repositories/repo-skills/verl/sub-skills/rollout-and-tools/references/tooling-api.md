# Tooling API

## Choose FunctionTool Or BaseTool

Use `@function_tool` when the tool is stateless, can be called as `fn(**parameters)`, and does not need create/release lifecycle hooks. Use a native `BaseTool` declared in a tool config file when the tool needs per-trajectory resources, sandbox VMs, scratch files, multimodal state, `tools_kwargs`, or cleanup.

Function and native tools can coexist. verl loads native tools from `tool_config_path`, function tools from `function_tool_path`, and rejects duplicate tool names across both sources.

## Function Tool Contract

A function tool is registered by importing a Python file containing decorated functions:

```python
from verl.tools.function_tool import function_tool

@function_tool("calculator")
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression.

    Args:
        expression: Arithmetic expression to evaluate.
    """
    return "42"
```

Required for schema inference:

- A docstring with a concise summary.
- A Google-style `Args:` block.
- A type hint for every parameter.
- A description in `Args:` for every parameter.
- No `*args` or `**kwargs`; use explicit parameters or `list[T]` instead.

The decorator can be bare (`@function_tool`, name is the function name) or named (`@function_tool("name")`). A custom OpenAI-compatible schema can be passed with `schema=`, but prefer fixing annotations and docs so schema inference remains transparent.

## Supported Type And Return Shapes

Schema inference is delegated to `transformers.utils.get_json_schema`. Primitive annotations, `list[T]`, `dict[K, V]`, optional/union types, and `Literal[...]` are supported by that path.

Function tool returns are normalized as follows:

- `str` becomes `ToolResponse(text=value)`.
- `dict` is JSON-serialized into `ToolResponse.text`.
- `ToolResponse` passes through.
- `(response,)`, `(response, reward)`, or `(response, reward, metrics)` tuples are accepted.
- `None` reward/metrics become `0.0` and `{}`; a real `0` or `False` reward is preserved as a numeric zero.
- Tuples with length `0` or `>=4` are errors.

Sync functions run through `asyncio.to_thread`; async functions are awaited directly.

## ToolAgentLoop Dispatch

`ToolAgentLoop._call_tool` handles common model-output failures without crashing rollout:

- Unknown tool names return a text response listing available tools.
- Invalid JSON arguments return a text response describing the JSON error.
- Tool execution exceptions return a text response with the exception message.
- Long text responses are truncated according to `max_tool_response_length` and `tool_response_truncate_side` (`left`, `right`, or middle/default).

Function tools ignore `tools_kwargs` by design. Native tools receive lifecycle calls: `create(create_kwargs=...)`, `execute(instance_id, tool_args, agent_data=...)`, then `release(instance_id)`.

## Multimodal Tool Responses

Native or function tools may return `ToolResponse` with text and image/video fields. Images are appended to the agent data and the next prompt is processed through the configured processor. If a text-only model has no processor but a tool returns multimedia, rollout raises a clear error. Video tool responses are currently not supported in `ToolAgentLoop` and raise `NotImplementedError`.

For multimodal dataset/tool integrations, keep dataset `return_multi_modal_inputs` and rollout processing aligned so the rollout path, processor kwargs, and training path see the same multimodal inputs.

## Dataset And Prompt Filtering

`RLHFDataset` uses the same tool loading path as `AgentLoopWorker` so prompt-length filtering sees the same schemas that rollout sees. If a prompt appears over length only in rollout, check whether the dataset and worker are reading different `tool_config_path` or `function_tool_path` values.

Per-sample `extra_info.tool_selection` can restrict active tools for a trajectory. Ensure selected names exactly match loaded tool names.

## Bundled Validation Helper

Use `scripts/validate_function_tool.py` before wiring a file into `function_tool_path`. It imports the file through verl's loader, captures schema errors, and emits JSON for automated checks. Because importing executes the user file, run it only on trusted local tool modules.
