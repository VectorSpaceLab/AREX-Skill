---
name: mcp-agent
description: "Build, compose, serve, operate, and troubleshoot mcp-agent
  applications, workflows, MCP servers, Temporal workers, CLI/cloud deployments,
  and observability integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# mcp-agent

Use this repo skill when a task involves the `mcp-agent` Python package or its CLIs: building MCP-enabled agents, composing effective workflow patterns, exposing applications as MCP servers, operating MCP Agent Cloud, using Temporal durability, or configuring logging/tracing/integrations.

## First Checks

1. Confirm the package is available with `python -c "import mcp_agent; print(mcp_agent.__name__)"` or install it with `pip install "mcp-agent"` / `uv add "mcp-agent"`.
2. Add optional extras only for the selected workflow: `mcp-agent[openai]`, `[anthropic]`, `[google]`, `[azure]`, `[bedrock]`, `[cohere]`, `[temporal]`, `[langchain]`, `[crewai]`, or `[redis]`.
3. Keep secrets in `mcp_agent.secrets.yaml`, environment variables, or deployment secret handles; keep reusable defaults in `mcp_agent.config.yaml` or a `Settings` object.
4. Read `references/repo-provenance.md` before deciding whether this skill matches a checkout or whether `refresh-repo-skill` is needed.
5. Read `references/troubleshooting.md` for cross-cutting install, import, config, optional dependency, CLI, and service failures.

## Route by Task

- **Core SDK and app code:** use `sub-skills/core-sdk/SKILL.md` for `MCPApp`, `Agent`, `AgentSpec`, `AugmentedLLM`, `RequestParams`, settings, secrets, local function tools, decorators, and factory basics.
- **Workflow composition:** use `sub-skills/workflow-patterns/SKILL.md` for routers, intent classifiers, parallel fan-out/fan-in, orchestrators, deep orchestrators, evaluator-optimizer loops, swarms, and structured outputs.
- **MCP server integration:** use `sub-skills/mcp-server-integration/SKILL.md` for upstream MCP server config, transports, roots, sampling, elicitation, OAuth/auth, `create_mcp_server_for_app`, and app-as-server validation.
- **CLI and Cloud operations:** use `sub-skills/cli-cloud-operations/SKILL.md` for `mcp-agent`, `mcp-cloud`, `mcpc`, project scaffolding, diagnostics, local dev commands, deploy, logs, env/secrets, workflows, and client install.
- **Durable execution:** use `sub-skills/durable-execution/SKILL.md` when workflows need Temporal workers, long-running tools, pause/resume, signals, retry policies, activity registration, or service-backed durability.
- **Observability and integrations:** use `sub-skills/observability-integrations/SKILL.md` for logger transports, OpenTelemetry, token accounting, progress/streaming, provider extras, LM Studio/local endpoints, LangChain, and CrewAI adapters.

## Common Decision Points

- Start with `core-sdk` when the user asks to create or debug Python application code; route to `workflow-patterns` only after the app/agent basics are clear.
- Route to `mcp-server-integration` when the words are about MCP transports, server config, app-as-server behavior, OAuth, resources, prompts, sampling, roots, elicitation, or client/server tool surfaces.
- Route to `cli-cloud-operations` when the task is command syntax, scaffolding, config checks, deployments, logs, hosted app state, environment secrets, or installing a server into Claude Code/Cursor/VS Code/ChatGPT clients.
- Route to `durable-execution` when the user already has or wants a workflow that must survive restarts, pause for human input, receive signals, or run in a Temporal worker.
- Route to `observability-integrations` when failures involve provider wrapper imports, OpenTelemetry exporters, token counters, JSONL event logs, streaming events, local model endpoints, or LangChain/CrewAI adapters.

## Safe Validation Helpers

- `sub-skills/core-sdk/scripts/check_core_sdk.py` checks imports, signatures, local tools, decorators, `AgentSpec`, and `RequestParams` without credentials or network.
- `sub-skills/workflow-patterns/scripts/check_workflow_imports.py` verifies canonical workflow imports and class names such as `LLMRouter`.
- `sub-skills/mcp-server-integration/scripts/validate_server_config.py` checks MCP server config shape and optional executable availability.
- `sub-skills/cli-cloud-operations/scripts/collect_cli_help.py` collects safe `--help` snapshots without deploy/login/install side effects.
- `sub-skills/durable-execution/scripts/check_temporal_config.py` validates Temporal config statically without starting a worker.
- `sub-skills/observability-integrations/scripts/check_observability_config.py` and `sub-skills/observability-integrations/scripts/summarize_event_log.py` inspect logger/OTEL config and JSONL event logs safely.

## Safety Notes

- Do not run Cloud deployment, client install writes, env secret mutation, workflow resume/cancel, or public server transports unless the user explicitly intends mutation.
- Do not assume optional provider SDKs, Temporal, Redis, LangChain, CrewAI, or cloud credentials are present in a base install; install and validate the smallest extra needed.
- Do not paste API keys or secret handles into generated code, logs, support transcripts, or client snippets.
- Prefer read-only `--help`, config validation, bundled checker scripts, import checks, and dry-run/static modes before starting services or calling external providers.
