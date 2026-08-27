---
name: pydantic-ai
description: "Routes agents working with Pydantic AI, pydantic-graph,
  pydantic-evals, clai, examples, and repository maintenance across focused
  workflow sub-skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pydantic AI Repo Skill

Use this repo skill when a task mentions Pydantic AI, imports `pydantic_ai`, edits the Pydantic AI monorepo, uses `pydantic-graph`, `pydantic-evals`, `clai`, or asks about agents, tools, models, providers, MCP, evals, graph workflows, CLI apps, tests, docs, cassettes, or maintainer workflows for this ecosystem.

## Start Here

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout or whether `refresh-repo-skill` is needed.
- Read [references/installation-and-extras.md](references/installation-and-extras.md) for package names, Python version support, extras, and minimal import checks.
- Read [references/capability-map.md](references/capability-map.md) when choosing the best sub-skill or checking coverage boundaries.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/provider/CLI/configuration problems.
- Run [scripts/check_environment.py](scripts/check_environment.py) for a safe no-network diagnostic of installed Pydantic AI packages, optional extras, and CLI help.

## Route by Task

| User task | Read |
| --- | --- |
| Build, configure, run, stream, test, or compose `Agent` instances; use deps, instructions, message history, usage limits, `AgentSpec`, or `TestModel` | [sub-skills/agent-core/SKILL.md](sub-skills/agent-core/SKILL.md) |
| Define function tools, validate schemas, use `RunContext`, `ModelRetry`, approvals, deferred tools, tool search, or reusable toolsets | [sub-skills/tools-and-toolsets/SKILL.md](sub-skills/tools-and-toolsets/SKILL.md) |
| Design structured outputs, output functions, `ToolOutput`, `NativeOutput`, multimodal inputs, message parts, or history serialization | [sub-skills/outputs-and-messages/SKILL.md](sub-skills/outputs-and-messages/SKILL.md) |
| Choose model strings, provider classes, optional extras, profiles, native tools, embeddings, fallback, concurrency, or provider troubleshooting | [sub-skills/models-and-providers/SKILL.md](sub-skills/models-and-providers/SKILL.md) |
| Connect MCP/FastMCP, capabilities, hooks, Logfire, A2A, durable execution, AG-UI, Vercel AI, or web integration surfaces | [sub-skills/mcp-and-integrations/SKILL.md](sub-skills/mcp-and-integrations/SKILL.md) |
| Build Pydantic Evals datasets/evaluators/reports or pydantic-graph `GraphBuilder` workflows | [sub-skills/evals-and-graph/SKILL.md](sub-skills/evals-and-graph/SKILL.md) |
| Use `clai`, `pai`, `clai web`, `Agent.to_cli`, `Agent.to_web`, custom agent loading, or app/example scaffolds | [sub-skills/cli-and-apps/SKILL.md](sub-skills/cli-and-apps/SKILL.md) |
| Edit this repository, choose targeted tests, record cassettes, update docs/examples, follow contribution rules, or refresh generated skills | [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md) |

## Install Baseline

Pydantic AI targets Python 3.10+ and is distributed as several related packages:

```bash
pip install pydantic-ai
pip install pydantic-ai-slim
pip install pydantic-graph pydantic-evals clai
```

Use `pydantic-ai-slim[...]` extras for optional providers and integrations. Do not install every extra by default; choose only the extras needed for the selected workflow.

Minimal import check:

```python
import pydantic_ai
import pydantic_graph
import pydantic_evals
import clai
```

For deterministic code examples and tests, prefer `pydantic_ai.models.test.TestModel` or `pydantic_ai.models.function.FunctionModel` before making live provider requests.

## Working Rules

- Use provider-prefixed model strings such as `openai:gpt-5.2`, `anthropic:claude-opus-4-6`, and `google:gemini-3-pro-preview` when examples intentionally call real providers.
- Treat provider SDKs, credentials, native tools, MCP servers, durable backends, UI servers, and cloud resources as optional surfaces that need explicit install/config checks.
- Do not run live model requests, record cassettes, start durable services, upload files, or mutate cloud resources unless the user explicitly asks and provides credentials/configuration.
- For repository edits, follow the scoped `AGENTS.md` and `agent_docs/` guidance summarized in [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md).
- Keep generated skill usage self-contained: use these bundled references and scripts instead of depending on the original source docs, examples, tests, or scripts unless the task is explicitly about maintaining a Pydantic AI checkout.
