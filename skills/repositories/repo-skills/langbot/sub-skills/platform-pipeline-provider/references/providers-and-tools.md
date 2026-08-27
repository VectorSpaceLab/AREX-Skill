# Providers, Runners, and Tools

## Provider Layer

Provider code manages model providers, LLM/embedding/rerank model objects,
requesters, sessions, runners, and tool access. It should be changed when tasks
involve model request shapes, provider-specific fields, local agent behavior,
function/tool calling, streaming, reasoning controls, or external workflow
runners.

Common checks:

```bash
uv run pytest tests/unit_tests/provider/test_model_manager.py -q --tb=short
uv run pytest tests/unit_tests/provider/test_tool_manager.py -q --tb=short
uv run pytest tests/unit_tests/provider/runners -q --tb=short
```

## Tool Sources

LangBot tools can come from native tools, plugin tools, external MCP servers,
MCP stdio servers, and skills. The `ToolManager` aggregates these sources for
runners.

Route boundaries:

- Provider/tool selection and runner integration: this sub-skill.
- Plugin Runtime protocol and plugin tool component details: `plugin-box-skills`.
- External MCP server CRUD/API routes: `api-mcp-web`.
- Box native execution and skill storage: `plugin-box-skills`.

## Real Provider Keys

Most provider wiring can be tested with fakes. Do not require OpenAI,
Anthropic, DashScope, Ollama, or other provider credentials unless the task is
specifically a live provider integration. Preserve secret redaction in service
and controller outputs.

## Local Agent Runner

Local agent and sandbox-backed runners commonly depend on Box and skill tool
surfaces. If a local agent issue includes missing sandbox tools, stale skill
packages, or MCP stdio execution failures, switch to `plugin-box-skills` after
confirming the runner selected the expected tool source.
