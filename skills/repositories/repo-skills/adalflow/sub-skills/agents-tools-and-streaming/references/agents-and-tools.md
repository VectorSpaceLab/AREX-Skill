# Agents and Tools

This reference covers service-free operating patterns for AdalFlow tools and agents. Provider/model-client setup is intentionally out of scope; use a real provider only after loading the generator/model-client sub-skill.

## Verified API surface

Use these constructor facts as the stable starting point:

```python
FunctionTool(fn, definition=None, require_approval=False, pre_execute_callback=None)
ToolManager(tools=[], additional_context={})
Agent(
    name,
    tools=None,
    context_variables=None,
    add_llm_as_fallback=False,
    model_client=None,
    model_kwargs={},
    model_type=ModelType.LLM,
    template=None,
    role_desc=None,
    cache_path=None,
    use_cache=True,
    answer_data_type=str,
    max_steps=10,
    is_thinking_model=False,
    tool_manager=None,
    planner=None,
    **kwargs,
)
Runner(agent, ctx=None, max_steps=None, permission_manager=None, conversation_memory=None, **kwargs)
ReActAgent(..., model_client, model_kwargs={}, max_steps=10, answer_data_type=str)
```

Important relationships:

- `Agent` contains a planner (`Generator`-like object) and a `ToolManager`.
- `Runner` executes the agent loop and owns runtime state such as `step_history`, token counters, cancellation, permissions, and streaming result queues.
- If you pass `tool_manager` and `planner` to `Agent`, you can test `Runner` mechanics without any model client.
- If you do not pass a planner, `Agent` builds a default `Generator` planner and requires a model client. Route provider configuration elsewhere before doing that.
- `ReActAgent` is an older combined agent component. Prefer `Agent` + `Runner` for new work unless maintaining code that already uses `ReActAgent`.

## FunctionTool patterns

`FunctionTool` wraps a callable and exposes a uniform output contract. It auto-detects four callable kinds:

| Python callable | Use | Returned `FunctionOutput.output` |
|---|---|---|
| `def f(...)` | `tool.call(...)` or `await tool.acall(...)` | function return value |
| `async def f(...)` | prefer `await tool.acall(...)`; sync `call` blocks | awaited return value |
| sync generator `def f(...): yield ...` | `call` or `acall`, then iterate | generator object |
| async generator `async def f(...): yield ...` | `await tool.acall(...)`, then `async for` | async generator object |

Recommended tool definition style:

```python
from adalflow.core.func_tool import FunctionTool
from adalflow.core.types import ToolOutput


def summarize_count(label: str, count: int) -> ToolOutput:
    """Summarize a non-negative count for agent reasoning."""
    if count < 0:
        return ToolOutput(
            output={"label": label, "count": count},
            observation="Count must be non-negative.",
            display="Invalid count",
            status="error",
        )
    return ToolOutput(
        output={"label": label, "count": count},
        observation=f"{label}: {count}",
        display=f"{label} = {count}",
    )

count_tool = FunctionTool(summarize_count)
result = count_tool.call("items", 3)
assert result.error is None
assert isinstance(result.output, ToolOutput)
```

Best practices:

- Give every tool a docstring; it becomes part of the planner-facing description.
- Add precise type hints for parameters and return values. Missing annotations degrade generated tool schemas.
- Validate inputs inside the tool, but return `ToolOutput(status="error", observation=...)` for recoverable user-facing failures.
- Let unexpected exceptions be captured by `FunctionTool`; they appear in `FunctionOutput.error` and let an agent attempt recovery.
- Use `require_approval=True` for destructive, external, or credentialed actions.
- Use `pre_execute_callback` only for fast, side-effect-free confirmation details or validation.
- Do not expose raw `eval`, shell execution, file deletion, network writes, or credential-bearing actions as unapproved tools.

## FunctionDefinition, Function, FunctionExpression, FunctionOutput, ToolOutput

Common data objects:

- `FunctionDefinition(func_name, func_desc=None, func_parameters={})`: schema/description shown to the planner. Override it only when automatic docstring/type-hint extraction is insufficient.
- `Function(name, args=[], kwargs={}, thought=None, _is_answer_final=None, _answer=None)`: structured planned action. `Runner` treats `_is_answer_final=True` as the final response and processes `_answer` through `answer_data_type`.
- `FunctionExpression(action="tool_name(arg=...)", thought=None)`: text expression form that `ToolManager` can parse into `Function` using the tool context.
- `FunctionOutput(name, input, output, error=None)`: wrapper returned by tool execution. The real tool return value is in `.output`.
- `ToolOutput(output, observation=None, display=None, is_streaming=False, metadata=None, status="success")`: richer tool result for agents and frontends. `Runner` uses `.observation` when present as the step observation.

Use `ToolOutput` when the tool has separate needs for agent reasoning, user display, and structured machine data. Use a plain return value only for simple tools where the same value is adequate everywhere.

## ToolManager workflows

Create a manager from `FunctionTool` instances or plain callables:

```python
from adalflow.core.tool_manager import ToolManager
from adalflow.core.types import Function, FunctionExpression

manager = ToolManager(tools=[count_tool], additional_context={"project": "demo"})

# Direct structured execution.
out = manager.execute_func(Function(name="summarize_count", kwargs={"label": "items", "count": 3}))
assert out.output.observation == "items: 3"

# Parse then execute an expression.
expr = FunctionExpression(action="summarize_count(label='items', count=4)")
parsed = manager.call(expr_or_fun=expr, step="parse")
out = manager.call(expr_or_fun=parsed, step="execute")
```

Manager details:

- `manager.context` combines tools by `FunctionTool.definition.func_name` plus `additional_context`.
- `manager.yaml_definitions`, `manager.json_definitions`, and `manager.function_definitions` are planner-facing tool descriptions.
- `execute_func_async(Function(...))` handles sync and async tools from async code.
- `execute_func_expr_via_eval` and sandbox helpers exist, but avoid them for untrusted model output. Prefer parsed `Function` objects and a curated `ToolManager.context`.
- Bound methods are named with the class prefix, for example `Calculator_multiply`; use the generated `definition.func_name` rather than guessing names.

## Agent construction

For real agents, after provider setup is known:

```python
agent = Agent(
    name="SupportAgent",
    tools=[count_tool],
    model_client=model_client,
    model_kwargs={"model": "provider-model", "temperature": 0.2},
    max_steps=5,
    answer_data_type=str,
)
runner = Runner(agent=agent)
result = runner.call(prompt_kwargs={"input_str": "Summarize item count 3"})
```

For service-free tests, inject fakes:

```python
from adalflow.core.types import GeneratorOutput, Function

class FakePlanner:
    def __init__(self, actions):
        self.actions = list(actions)

    def call(self, *, prompt_kwargs, model_kwargs=None, use_cache=None, id=None):
        return GeneratorOutput(data=self.actions.pop(0))

    async def acall(self, *, prompt_kwargs, model_kwargs=None, use_cache=None, id=None):
        return self.call(prompt_kwargs=prompt_kwargs, model_kwargs=model_kwargs, use_cache=use_cache, id=id)

    def get_prompt(self, **kwargs):
        return "fake prompt"

manager = ToolManager(tools=[count_tool])
planner = FakePlanner([
    Function(name="summarize_count", kwargs={"label": "items", "count": 3}),
    Function(name="finish", _is_answer_final=True, _answer="items: 3"),
])
agent = Agent(name="fake", tool_manager=manager, planner=planner, max_steps=3)
runner = Runner(agent=agent)
assert runner.call(prompt_kwargs={"input_str": "test"}).answer == "items: 3"
```

This pattern is the preferred way to test agent-loop behavior without credentials or live LLM calls.

## Runner entry points

- `Runner.call(prompt_kwargs, model_kwargs=None, use_cache=None, id=None) -> RunnerResult`: synchronous loop.
- `await Runner.acall(...) -> RunnerResult`: async loop.
- `Runner.astream(...) -> RunnerStreamingResult`: starts an async task on the current event loop and returns an object whose `stream_events()` async iterator yields events.

Always provide `prompt_kwargs` with the prompt keys expected by the planner template. Default agent templates expect at least `input_str`; custom planners may accept anything.

## Final answers and answer_data_type

`Runner` finalizes when the planner output is a `Function` with `_is_answer_final=True`. It processes `_answer` according to `agent.answer_data_type`:

- Built-in types such as `str`, `int`, `dict` are cast directly.
- Pydantic models expect a dict or JSON string representing a dict.
- AdalFlow dataclasses expect a dict or JSON string and use `from_dict`.

If the planner never emits a final `Function`, `Runner` returns a `RunnerResult` with an answer such as `No output generated after ...` and includes the step history it did execute.

## ReActAgent notes

`ReActAgent` combines planner, tool manager, finish tool, and step loop in one component. It is useful for existing ReAct code, but new code should prefer `Agent` + `Runner` because that path has clearer sync/async/streaming, permission, and final-result behavior.

When maintaining `ReActAgent`:

- Provide `model_client` and `model_kwargs`; it constructs its own planner.
- Pass tools as callables or `FunctionTool` instances.
- Use `max_steps` to bound the loop.
- Use `answer_data_type` when the finish answer must be structured.
