# Tool and agent workflows

## 1. Define, inspect, and deliberately invoke a small tool

Keep the callable's inputs typed and bounded. Do not accept a raw shell string,
file path, URL, or expression unless the function itself applies an explicit
policy. Generate the schema once and inspect it before registration.

```python
from mellea.backends import tool
from mellea.backends.tools import validate_tool_arguments

@tool
def add(a: int, b: int) -> int:
    """Add two bounded integers."""
    return a + b

request_args = validate_tool_arguments(add, {"a": "2", "b": 3}, strict=True)
value = add.run(**request_args)
```

Use a deterministic wrapper for risky functionality. For example, expose
`read_report(report_id: str)` rather than `read_file(path: str)`, and expose a
fixed operation rather than an `eval(expression)` tool. If a tool must take a
path, resolve it against an approved root and reject traversal before opening
it.

## 2. Manual generation → approval → execution loop

Use the low-level loop when an application needs to inspect or transform every
request. Generation and execution are separate:

```python
from mellea.backends import ModelOption
from mellea.stdlib.functional import acall_tools

result, context = await mfuncs.aact(
    action=instruction,
    context=context,
    backend=backend,
    model_options={ModelOption.TOOLS: [add]},
    tool_calls=True,
    await_result=True,
)

validated_calls = []
for call in result.tool_calls or []:
    if call.name not in {"add"}:
        raise RuntimeError(f"unapproved tool: {call.name}")
    args = validate_tool_arguments(call.func, call.args, strict=True)
    validated_calls.append(dataclasses.replace(call, args=args))
result.tool_calls = validated_calls
# Prefer the normal acall_tools path after policy hooks are installed.
messages = await acall_tools(result, backend)
for message in messages:
    context = context.add(message)
```

The sketch assumes `mfuncs`, `instruction`, `context`, `backend`, and
`dataclasses` are supplied by the application. In production, do not validate a
copy and then execute the original call: replace the call or reject it. A
pre-invoke hook is the stronger centralization point when several loops share a
policy. Add `ToolMessage` observations to context yourself; `call_tools()` does
not do it.

Use `uses_tool("name")` when generation must call a named tool and
`tool_arg_validator(...)` when a requirement should reject/repair generated
arguments. These requirements guide the generation/retry layer; they do not
replace a final execution-time policy check.

## 3. ReAct with bounded tools

```python
import asyncio
from mellea.stdlib.context import ChatContext
from mellea.stdlib.frameworks.react import react

async def run_agent(backend, search_tool):
    result, context = await react(
        goal="Find the answer using only the approved search operation.",
        context=ChatContext(),
        backend=backend,
        tools=[search_tool],
        loop_budget=6,
    )
    return result, context

answer, _ = asyncio.run(run_agent(backend, approved_search_tool))
```

Treat entry into `react()` as authorization for every tool in `tools` and any
tool merged from `model_options`. Keep `loop_budget` finite. A tool exception
is observed as a failed tool result, but a plugin block can abort the loop;
handle both at the application boundary. The framework adds an internal
`final_answer` tool and overrides a user tool with that name, so do not use
that name for a business tool. A final-answer call must be the only tool call
in its turn.

For structured output, pass a Pydantic model as `format=`. This causes another
model generation after `final_answer`; it does not make arbitrary tool output
safe or validate side effects. Use a fake/scripted backend for deterministic
loop tests and real model tests only for provider-specific function-calling
compatibility.

## 4. Safe Python and shell execution

Choose the execution tier before exposing the tool:

- Use `static` to parse/check syntax and imports without running code.
- Use `local_unsafe` only for explicitly trusted development code.
- Use `local` when host execution is required and declared timeout/output
  limits are sufficient; do not describe its policy booleans as enforced.
- Use `docker` when untrusted code needs process isolation, and verify Docker
  and `llm-sandbox` before constructing a persistent artifact-export tool.

For local Python artifacts, use a temporary or dedicated approved directory,
set `artifact_dir`, and inspect `success` before consuming artifacts. For Docker,
put container paths in `CapabilityPolicy.artifact_export_paths`; a host
`artifact_dir` by itself cannot export a file. Keep package installation lists
fixed and trusted; the tool can install packages before execution.

For shell, prefer one argv-friendly command without pipes, redirects, command
substitution, shell wrappers, or code-execution flags. Compose operations in
Python if needed. Always pass a workspace `working_dir` and explicit
`allowed_paths` for writes. A successful static check means only that the
current denylist did not find a known pattern; it is not approval for a
credentialed or networked command.

## 5. MCP discovery and admission

```python
from mellea.stdlib.tools.mcp import discover_mcp_tools, http_connection

connection = http_connection(
    "https://trusted.example/mcp",
    api_key=token_from_secret_store,
)
specs = await discover_mcp_tools(connection)
approved_names = {"search_public_docs"}
tools = [
    spec.as_mellea_tool()
    for spec in specs
    if spec.name in approved_names and spec.input_schema.get("type") == "object"
]
```

Install `mellea[tools]` first. For streamable HTTP/SSE, verify the URL, TLS,
headers, timeouts, server identity, and outbound network approval. For stdio,
verify the executable and fixed args, construct a minimal environment mapping,
and remember that each invocation starts a new subprocess. Inspect schemas for
required fields, unexpected additional properties, unconstrained paths/URLs,
and malformed unions before admission. A remote MCP server can return prompt
injection in its description or result; keep its output data, not instructions.

## 6. LangChain and smolagents bridges

```python
from mellea.backends.tools import MelleaTool

mellea_search = MelleaTool.from_langchain(langchain_base_tool)
mellea_hf_tool = MelleaTool.from_smolagents(smolagents_tool)
```

Install `mellea[tools]` (or the specific foreign package) and verify the
object is the expected `BaseTool`/smolagents `Tool`. The adapters copy schema
metadata and forward calls; they do not remove network, filesystem, browser,
Python-interpreter, or credential side effects. Wrap or reject a foreign tool
when the original capability exceeds the task's approval boundary. For
LangChain message history, convert messages to a neutral chat representation
and add them to `ChatContext`; history conversion is separate from tool
execution.

## 7. Context compaction in an agent loop

For cheap per-append truncation:

```python
from mellea.stdlib.components.react import pin_react_initiator
from mellea.stdlib.context import ChatContext, WindowCompactor

context = ChatContext(
    compactor=WindowCompactor(size=8, pin_predicate=pin_react_initiator)
)
```

The pinned prefix contains the ReAct goal and tool registration. The window
counts only unpinned body components. For token-gated behavior, wrap an inner
compactor in `ThresholdCompactor`; it relies on the latest generation usage and
may lag behind a large tool response. For backend summaries, pass
`LLMSummarizeCompactor` to `react(compactor=...)` or gate it with a threshold.
Do not attach it directly to `ChatContext`, because `ChatContext.add()` has no
backend argument and would otherwise attempt a backend call on every append.

Summarization may drop attachments and flatten tool-call details. Keep a recent
verbatim window, pin policy/system/goal components, and ensure the summarizer's
prompt preserves tool names, outputs, decisions, URLs, and unresolved work.
