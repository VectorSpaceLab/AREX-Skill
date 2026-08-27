# Tools and agents API reference

This reference targets the installed package version **Mellea 0.8.0.dev0**.
The public tool API uses OpenAI-compatible dictionaries of the form:

```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "...",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}
```

## Define and adapt tools

```python
from mellea.backends import ModelOption, tool
from mellea.backends.tools import MelleaTool

@tool(name="lookup_weather")
def lookup_weather(city: str, days: int = 1) -> dict:
    """Return a weather forecast for a city.

    Args:
        city: City name.
        days: Number of forecast days.
    """
    return {"city": city, "days": days}

def double(value: int) -> int:
    """Double an integer."""
    return value * 2

plain = MelleaTool.from_callable(double)
print(lookup_weather.name, lookup_weather.as_json_tool)
answer = lookup_weather.run(city="Boston", days=2)
```

`@tool` replaces the decorated function with a `MelleaTool`; invoke it with
`.run()`, not by calling the object as a normal function. `from_callable()`
uses annotations and the docstring to build a schema, supports sync and async
callables, and accepts `name=`. `MelleaTool.run(*args, **kwargs)` forwards to
the wrapped callable. `as_json_tool` returns a copy of the stored schema.

`MelleaTool.from_langchain(tool)` requires a LangChain `BaseTool`, converts its
schema with LangChain's OpenAI converter, and calls it through
`tool.run(tool_input={...})`; normal model calls therefore use keyword
arguments. `MelleaTool.from_smolagents(tool)` requires a smolagents `Tool`,
uses smolagents' own JSON-schema converter, and calls `tool.forward(**kwargs)`.
Both adapters raise an actionable `ImportError` when their optional dependency
is missing and `ValueError` for the wrong object type. These adapters preserve
the foreign tool's side effects; wrapping is not sandboxing.

## Register tools for generation

```python
from mellea import start_session

with start_session() as session:
    result = session.instruct(
        "Use lookup_weather if it is needed.",
        model_options={ModelOption.TOOLS: [lookup_weather]},
        tool_calls=True,
    )
```

`ModelOption.TOOLS` accepts an iterable of `AbstractMelleaTool` instances or a
mapping from names to tools. `ModelOption.TOOL_CHOICE` is passed through to the
backend (`"none"`, `"auto"`, or a provider-supported specific choice). A model
may decline to call a supplied tool. `tool_calls=True` makes generated calls
available on the output thunk; it does not run them.

`add_tools_from_model_options()` and `add_tools_from_context_actions()` are
internal assembly helpers used when a custom component loop must merge model
options and component-declared tools. Duplicate names are last-writer-wins.
`convert_tools_to_json()` creates a list of schemas for a backend.

## Parse and validate model output

`parse_tools(text)` scans JSON-like model text and returns
`list[tuple[str, Mapping]]`. It searches for objects containing a `name` and a
mapping under `arguments`, `args`, or `parameters`; it ignores surrounding
non-JSON text and is intentionally only a lightweight JSON parser. It does not
prove that a tool exists or that arguments are safe.

```python
from mellea.backends.tools import validate_tool_arguments

safe_args = validate_tool_arguments(
    lookup_weather,
    {"city": "Boston", "days": "2"},
    coerce_types=True,
    strict=True,
)
```

`validate_tool_arguments(tool, args, coerce_types=True, strict=False)` builds a
Pydantic validator from the tool's JSON schema. It handles primitive, array,
nested-object, optional, and discriminated-union schemas when representable.
With coercion enabled, common values such as string `"2"` become integers.
`strict=True` forbids extra fields and raises Pydantic `ValidationError` on
failure. `strict=False` logs a warning and returns the original mapping on a
validation failure, so use strict mode at a security boundary. Validation is
not automatically inserted into `call_tools()`.

## Execute generated calls

```python
from mellea.stdlib.functional import acall_tools, call_tools

# result is a ModelOutputThunk produced with tool_calls=True.
messages = call_tools(result, session.backend)       # sync boundary
# or: messages = await acall_tools(result, session.backend)
for message in messages:
    print(message.name, message.arguments, message.content)
```

`call_tools()`/`acall_tools()` execute each requested call, return one
`ToolMessage` per call, and leave context management to the caller. Calls are
executed sequentially. A tool exception is captured in the message as a failed
execution (`tool_output` is the exception and `error` is present in the post
hook payload); a pre-invoke policy violation can instead raise
`PluginViolationError`. Add each returned message to a context before the next
generation if the model must observe it.

## Python execution tools

Import from `mellea.stdlib.tools`:

```python
from pathlib import Path
from mellea.stdlib.tools import CapabilityPolicy, make_execution_environment, python_tool

tool = python_tool(
    tier="docker",  # choose explicitly
    allowed_imports=["math"],
    policy=CapabilityPolicy(timeout=20),
    artifact_dir=Path("artifacts"),
)
result = tool.run(code="import math; print(math.sqrt(4))")
```

`python_tool(tier, packages, artifact_dir, policy, allowed_imports, name,
suppress_agg)` returns a `MelleaTool` whose callable is
`run_python(code: str) -> ExecutionResult`. Valid tiers are:

| Tier | Executes? | Boundary and purpose |
|---|---:|---|
| `static` | no | Parses AST and checks top-level imports; returns skipped result. |
| `local_unsafe` | yes | Direct host subprocess; no policy or container isolation. |
| `local` | yes | Host subprocess with declared policy; selected limits are enforced. |
| `docker_unsafe` | yes | Docker/llm-sandbox execution without declared policy. |
| `docker` | yes | Docker/llm-sandbox with declared policy and enforced runtime limits. |

`make_execution_environment()` creates the corresponding environment directly.
`ExecutionResult` reports `success`, `stdout`, `stderr`, `skipped`,
`skip_message`, `exit_code`, `timed_out`, `artifacts`, `execution_mode`, and
`working_directory`. `Artifact` reports a path, byte size, and content type.
Local `artifact_dir` is scanned only after successful execution. Docker
artifacts require policy `artifact_export_paths`; an `artifact_dir` alone does
not copy files out. Package installation is cached per `python_tool` instance;
package strings are passed to `uv pip install` or pip, so only use trusted
specifiers. The default/omitted tier decision is intentionally unsafe and
warns; always choose a tier explicitly.

`code_interpreter()` and `local_code_interpreter()` are deprecated compatibility
wrappers. Use `python_tool()` instead.

## Shell execution

```python
from mellea.stdlib.tools.shell import bash_executor

result = bash_executor(
    "find . -maxdepth 1 -type f",
    working_dir="/approved/workspace",
    allowed_paths=["/approved/workspace"],
)
```

`bash_executor(command, working_dir=None, allowed_paths=None)` runs a local
subprocess after tokenization and conservative denylist checks. It returns the
same `ExecutionResult` shape as Python execution. `StaticBashEnvironment`
performs parsing and checks without executing; `BashEnvironment` is the abstract
base. The guardrails reject privilege escalation, interactive/code-execution
indirection, destructive Git/RM forms, shell operators and unsafe system-path
writes. They are a denylist, not a complete sandbox: trusted script files can
still execute arbitrary code, and host credentials/network access remain host
concerns. Use application-level isolation for untrusted commands.

## MCP client tools

MCP client support is optional and loaded by `mellea.stdlib.tools.mcp`; install
the tools extra (`mellea[tools]`) before importing it. The module exposes:

- `http_connection(url, api_key=None, headers=None, connect_timeout=30.0, read_timeout=300.0)` for streamable HTTP.
- `sse_connection(...)` for SSE.
- `stdio_connection(command, args=None, env=None, timeout=300.0)` for a local server process.
- `await discover_mcp_tools(connection)` returning `MCPToolSpec` values.
- `MCPToolSpec.as_mellea_tool()` returning a fresh-session-per-call `MelleaTool`.

The API key becomes an `Authorization: Bearer ...` header and extra headers are
merged after it. `None` keyword arguments are removed before an MCP call. MCP
content is flattened to text; image/audio/blob content is represented as a
binary marker, resource links may be resolved, and server errors become a
`[tool error] ...` string. Discovery is not approval: filter specs before
wrapping, and do not put secrets in model-visible descriptions.

This module is the MCP **client** bridge. To expose a Mellea-backed function as
an MCP **server** tool, use upstream `mcp.server.fastmcp.FastMCP` and
`@server.tool()`. That requires `mcp[cli]` plus whichever Mellea backend
extra/service the function uses. The wrapper does not change session, model,
credential, concurrency, or data-isolation requirements. Reuse a deliberately
scoped `MelleaSession` only when its context and backend client are safe to
share across calls.

## ReAct and compaction

`await react(goal, context, backend, *, format=None, model_options=None,
tools, loop_budget=10, compactor=None)` requires `ChatContext`. It adds a
`ReactInitiator`, repeatedly generates `ReactThought`, executes tool calls, and
stops only when the internal `final_answer` tool is called. It raises
`RuntimeError` when the loop budget ends without a final answer. A supplied
`format` causes an additional generation after finalization. Tools in
`model_options[ModelOption.TOOLS]` are merged with explicit tools.

`ChatContext` can use `WindowCompactor`, `ThresholdCompactor`, or a custom
`InlineCompactor`. `LLMSummarizeCompactor` calls a backend and must be used via
`react(compactor=...)`, a threshold wrapper, or a manual call rather than as a
per-`add()` compactor. `pin_react_initiator` and `react_summary_prompt` preserve
the ReAct goal/tool registration and produce a summary template with a
`{conversation}` placeholder. Compaction is lossy for multimodal and complex
tool payloads; keep recent tool turns verbatim when fidelity matters.
