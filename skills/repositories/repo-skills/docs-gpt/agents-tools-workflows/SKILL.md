---
name: agents-tools-workflows
description: "Use for DocsGPT agents, built-in and custom tools, workflows, MCP,
  schedules, artifacts, webhooks, and sandboxed code execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agents, tools, and workflows skill

Use this subskill for anything involving agent definitions, tool configuration, workflow nodes, MCP, schedules, artifacts, webhooks, or code-execution/sandbox behavior.

## Primary surfaces

- Agents: `/api/agents`, `/api/agents/<id>`, template/pinned/shared/import-export endpoints.
- Tools: `/api/tools`, `/api/available_tools`, `/api/tools/<...>`.
- Workflows: `/api/workflows`, `/api/workflows/<id>`.
- Schedules: `/api/schedules/...` and `/api/agents/<agent_id>/schedules`.
- Artifacts: `/api/artifacts/...`.
- Webhooks: agent webhook routes under `/api/agents/webhooks/...`.
- MCP/tool bridging: the MCP tool namespace and the ASGI `/mcp` mount.

## Agent types to keep straight

- **Classic** — prefetch retrieval and standard tool use.
- **Agentic** — retrieval is exposed as an internal search tool and the model decides when to search.
- **Research** — multi-phase clarified/planned/researched/synthesized runs with budgets.
- **Workflow** — graph-based execution over nodes with shared state.

## Tool model

DocsGPT tools are Python classes under `application/agents/tools/` that inherit from the base `Tool` class and implement:

- `__init__(config)`
- `execute_action(action_name, **kwargs)`
- `get_actions_metadata()`
- `get_config_requirements()`

The tool manager auto-discovers tools from the directory. Built-in tools include API, browser/webpage reading, memory, notes, todo list, PostgreSQL, remote device, MCP, and others documented in `docs/content/Tools/basics.mdx`.

## Workflow model

Workflows use shared state and nodes such as:

- AI Agent node
- Set State node
- Condition node
- Code node

Remember the syntax split:

- template fields use `{{variable}}`
- expression fields use bare CEL names like `variable`

## What to look at in source

- `application/agents/default_tools.py`
- `application/agents/workflow_agent.py`
- `application/agents/tools/tool_manager.py`
- `application/api/user/agents/routes.py`
- `application/api/user/tools/routes.py`
- `application/api/user/workflows/routes.py`
- `application/api/user/schedules/routes.py`
- `application/api/user/artifacts/routes.py`
- `application/api/user/agents/webhooks.py`

## Common implementation questions

- Does the change affect discovery or runtime execution?
- Does it need a new tool class or only a config/metadata update?
- Is the workflow node contract consistent with the shared state semantics?
- Does a new tool need safe secrets handling in `get_config_requirements()`?
- Does any public route require admin/owner/team grants?

## Safe checks and scripts

```bash
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api/tools
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api/workflows
python skills/disco/docs-gpt/scripts/check_local_config.py --repo .
python -m pytest tests/agents/test_workflow_engine.py tests/services/test_mcp_server.py
```

If you touch tools or workflows, add or update tests that prove tool discovery, config shape, and runtime behavior. If you touch MCP or sandbox behavior, verify against the ASGI app rather than Flask-only startup.

## Useful references

- `../references/repo-map.md`
- `../references/dev-environment.md`
- `../references/verification-matrix.md`
- `docs/content/Agents/basics.mdx`
- `docs/content/Agents/nodes.mdx`
- `docs/content/Tools/basics.mdx`
- `docs/content/Tools/creating-a-tool.mdx`
- `docs/content/Tools/artifacts-and-code-execution.mdx`
