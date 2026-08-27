---
name: tools-and-integrations
description: "Bind and troubleshoot ADK Python tools, ToolContext, long-running
  and confirmation tools, auth, MCP/OpenAPI/Google API/cloud integrations, A2A
  helpers, and optional extras."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ADK Tools and Integrations

Use this sub-skill when a user asks to add, wrap, authenticate, expose, or debug tools and integration toolsets in an ADK Python agent.

## Route Here

- Bind Python functions with `FunctionTool`, `LongRunningFunctionTool`, `ToolContext`, `request_input`, or explicit `tool_context.request_confirmation()`.
- Build custom `BaseTool` or `BaseToolset` classes, filter/prefix toolsets, or close toolset resources safely.
- Wrap agents as tools with `AgentTool`, delegate with `TransferToAgentTool` or `transfer_to_agent`, or diagnose tool-name routing issues.
- Add auth with `AuthConfig`, `AuthCredential`, `AuthenticatedFunctionTool`, OpenAPI auth helpers, MCP auth, or credential request flows.
- Configure MCP, OpenAPI, API Hub, Google API, Application Integration, BigQuery/Bigtable/Spanner/Pub/Sub/Data Agent/Toolbox/Slack/A2A integrations.
- Diagnose missing optional extras such as `google-adk[mcp]`, `google-adk[extensions]`, `google-adk[gcp]`, `google-adk[tools]`, `google-adk[a2a]`, `google-adk[toolbox]`, or `google-adk[db]`.

## Route Elsewhere

- Agent constructor field placement, `model`, `instruction`, schemas, and callback basics: use `agent-construction`.
- CLI command usage, app discovery, local servers, deployment, and YAML config loading: use `cli-configuration-deployment`.
- `Runner`, `App`, session/memory/artifact persistence, plugins, telemetry, and service lifecycles: use `runtime-services`.
- Workflow graph nodes, `Workflow`, HITL node resume, joins, and dynamic graph routing: use `workflow-orchestration`.
- Modifying ADK repository source, style, tests, docs, or samples: use `repo-development`.

## Quick Start

1. Prefer bare callables for simple tools; wrap with `FunctionTool(func=..., require_confirmation=...)` only when you need confirmation or explicit tool object behavior.
2. Add `tool_context: ToolContext` only when the tool needs state, artifacts, credentials, confirmation, transfer actions, or workflow node helpers; the parameter must be named `tool_context`.
3. Return JSON-serializable dictionaries for structured tool results; return `{"error": "..."}` when the model should see a recoverable tool failure.
4. Use `LongRunningFunctionTool` for work that returns pending status or pauses for external input; do not retry the same long-running call unless the returned event requests it.
5. Treat MCP, cloud, database, and A2A helpers as optional-extra surfaces; first run the bundled inspection script before assuming an import is available.

```python
from google.adk import Agent
from google.adk.tools import FunctionTool, ToolContext


def transfer_funds(amount: float, recipient: str, tool_context: ToolContext):
  """Transfer funds after ADK collects confirmation."""
  return {"status": "scheduled", "amount": amount, "recipient": recipient}


root_agent = Agent(
    name="finance_agent",
    model="gemini-3.5-flash",
    instruction="Use tools for account operations and explain the result.",
    tools=[FunctionTool(func=transfer_funds, require_confirmation=True)],
)
```

## References

- [API reference](references/api-reference.md) — public classes, constructors, auth models, tool context methods, integration toolset families, optional extras, and local validation checks.
- [Workflows](references/workflows.md) — recipes for function tools, confirmation, long-running tools, MCP, OpenAPI, Google API/cloud integrations, A2A exposure, and safe fallback planning.
- [Troubleshooting](references/troubleshooting.md) — fixes for missing extras, credentials, auth config, schema conversion, MCP sessions, cloud clients, confirmation confusion, and swallowed tool errors.
- [Inspection script](scripts/inspect_tooling.py) — no-network diagnostic that prints installed tool signatures and reports optional-extra availability without failing the whole run.

## Tooling Checklist

- Tool names are stable, unique, and derived from clear function/class names; descriptions come from docstrings or explicit `BaseTool` descriptions.
- Function parameters are typed with JSON-schema-friendly types; Pydantic models are accepted for structured arguments but should be validated before side effects.
- `ToolContext` is used for state, credentials, confirmation, memory/artifacts, transfer actions, or node execution; it is not exposed to the model as a normal argument.
- Sensitive operations require either `require_confirmation=True` or explicit `tool_context.request_confirmation()` handling.
- Integration code documents which extra and which credential source are required, and includes a local import/help probe before any network or credential-dependent call.
- Tool exceptions are either intentionally propagated or translated by `on_tool_error_callback`; recoverable domain failures return a function response such as `{"error": "..."}`.
