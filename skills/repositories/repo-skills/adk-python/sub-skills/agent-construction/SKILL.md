---
name: agent-construction
description: "Build and troubleshoot ADK Python Agent/LlmAgent definitions,
  model settings, modes, callbacks, schemas, and multi-agent delegation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ADK Python Agent Construction

Use this sub-skill when a user asks to define, revise, or debug Python ADK agents built with `google.adk.Agent` or `google.adk.agents.LlmAgent`.

## Route Here

- Create a minimal `root_agent`, add `model`, `instruction`, `description`, tools, callbacks, or schemas.
- Choose between `mode="chat"`, `mode="task"`, and `mode="single_turn"` for LLM agents and sub-agents.
- Build hierarchical multi-agent systems with `sub_agents`, delegation descriptions, `task` agents, or `single_turn` helper agents.
- Add structured input/output with Pydantic schemas, `output_schema`, `input_schema`, and `output_key`.
- Diagnose constructor validation errors, missing model credentials, callback ordering, schema/tool interactions, and sub-agent context isolation.

## Route Elsewhere

- Workflow graph nodes, `Workflow`, `BaseNode`, graph edges, dynamic nodes, joins, and workflow HITL: use `workflow-orchestration`.
- ADK CLI commands, YAML app loading, `adk run`, `adk web`, deployment, and config schema generation: use `cli-configuration-deployment`.
- Tool internals, toolsets, MCP/OpenAPI/Google API tools, auth flows, and optional integration extras: use `tools-and-integrations`.
- Runner services, sessions, memory, artifacts, plugins, telemetry, and code executors: use `runtime-services`.
- Modifying the ADK source repository itself, style, focused tests, docs, or samples: use `repo-development`.

## Quick Start

1. Import from the public package: `from google.adk import Agent` or `from google.adk.agents import LlmAgent, RunConfig`.
2. Name agents with valid Python identifiers; never use `user` as an agent name.
3. Put model behavior in `instruction`, static generation options in `generate_content_config`, tools in `tools`, and final response schemas in `output_schema`.
4. Expose a Python app by defining `root_agent = Agent(...)` in an importable module.
5. Use a `Runner` only after selecting runtime services and creating or auto-creating sessions; this sub-skill focuses on the agent definitions.

```python
from google.adk import Agent


def get_weather(city: str) -> str:
  """Return a simple weather summary."""
  return f"Weather for {city}: sunny."


root_agent = Agent(
    name="weather_agent",
    model="gemini-3.5-flash",
    instruction="Answer weather questions and call tools when needed.",
    tools=[get_weather],
)
```

## References

- [API reference](references/api-reference.md) — constructor fields, imports, validation rules, callbacks, schemas, `RunConfig`, and `Runner.run` invocation shape.
- [Workflows](references/workflows.md) — recipes for minimal agents, sample app layout, callbacks, structured output, `task` and `single_turn` sub-agents, and multi-agent delegation.
- [Troubleshooting](references/troubleshooting.md) — fixes for generation config errors, schema/tool behavior, model credentials, branch isolation, callback order, and tool error callbacks.
- [Inspection script](scripts/inspect_agent_api.py) — safe local diagnostic that prints installed ADK signatures and constructs a no-network minimal agent.

## Agent-Construction Checklist

- Agent tree has unique, identifier-safe names and clear one-line `description` strings for delegatable sub-agents.
- Root `LlmAgent` runs in chat mode; `task` and `single_turn` are usually child agents exposed to the parent as tools.
- `output_schema` is used for final structured responses; `generate_content_config.response_schema` is not used on `LlmAgent`.
- Tool callables have docstrings and typed parameters; deeper toolset/auth issues route to `tools-and-integrations`.
- Callback functions return `None` to continue, or the documented override shape to short-circuit or replace model/tool behavior.
- Model/provider credentials and optional extras are treated as deployment assumptions, not as requirements for constructing an in-memory agent object.
