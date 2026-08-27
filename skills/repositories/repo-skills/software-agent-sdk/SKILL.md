---
name: software-agent-sdk
description: "Router for using and maintaining the OpenHands Software Agent SDK,
  including local agents, tools, AgentSkills, agent-server runtimes, GitHub
  automation, and repository development workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenHands Software Agent SDK

Use this repo skill when a task involves the OpenHands `software-agent-sdk` packages or source repository: building code agents, selecting built-in tools, loading AgentSkills/plugins/hooks/MCP, running local or remote conversations, using the agent-server and workspace backends, automating GitHub workflows, or maintaining this monorepo.

The runtime packages are:

- `openhands-sdk`: core agent, LLM, conversation, settings, skills, MCP, hooks, plugins, and workspace interfaces.
- `openhands-tools`: built-in tool implementations and default presets.
- `openhands-workspace`: Docker, Apptainer, cloud, and runtime-API remote workspace implementations.
- `openhands-agent-server`: FastAPI REST/WebSocket server for remote conversations, workspace routes, deferred init, and local/hosted runtimes.

## First checks

For an installed package environment:

```bash
python -m pip install openhands-sdk openhands-tools openhands-workspace openhands-agent-server
python - <<'PY'
import openhands.sdk, openhands.tools, openhands.workspace, openhands.agent_server
print("OpenHands SDK packages import successfully")
PY
python -m openhands.agent_server --help
```

For a source checkout, run `make build` before package tests. Use `uv run pytest ...` and `uv run pre-commit run --files <changed-file>` for focused validation.

Run [`scripts/check_env.py`](scripts/check_env.py) for a safe import/tool/server capability report.

## Route map

### `agent-core`
Use [`sub-skills/agent-core/SKILL.md`](sub-skills/agent-core/SKILL.md) for local SDK agent construction, LLM configuration, `Agent`, `Conversation`, `LocalConversation`, `RemoteConversation`, callbacks, async/sync execution, persistence, interruption, condensation, settings, security analyzers, and title generation.

Read it when the request mentions `LLM`, `Agent`, `Conversation`, `AgentContext` as prompt context rather than skill loading mechanics, local runs, remote conversation factory routing, events, metrics, cancellation, or model/provider behavior.

### `extensions`
Use [`sub-skills/extensions/SKILL.md`](sub-skills/extensions/SKILL.md) for AgentSkills, project/user/public skill loading, plugins and marketplaces, hooks, MCP server maps, memory, secrets, prompt suffixes, and other extension points.

Read it when the request mentions `SKILL.md`, `.agents/skills`, `.openhands/skills`, `AGENTS.md`, `load_project_skills`, `registered_marketplaces`, `.mcp.json`, `HookConfig`, `LookupSecret`, or plugin lazy loading.

### `built-in-tools`
Use [`sub-skills/built-in-tools/SKILL.md`](sub-skills/built-in-tools/SKILL.md) for `openhands-tools`, default tool presets, tool registration, usable-tool filtering, terminal/file-editor/browser/task/workflow/grep/glob/planning/delegate/TOM tools, custom tool classes, and sub-agent tool wiring.

Read it when the request asks which tool names to use, how to register or resolve tools, how browser availability is detected, how workflow scripts work, or why a tool is missing from `/server_info`.

### `remote-runtime`
Use [`sub-skills/remote-runtime/SKILL.md`](sub-skills/remote-runtime/SKILL.md) for `openhands-agent-server`, REST/WebSocket routes, `RemoteWorkspace`, `Workspace(host=...)`, Docker/Apptainer/API/cloud workspaces, deferred init, session API keys, custom tool import modules, and local server helpers.

Read it when the request mentions `python -m openhands.agent_server`, `/api/conversations`, `/api/init`, `X-Session-API-Key`, WebSockets, Docker workspace images, `OH_EXTRA_PYTHON_PATH`, or warm-pool/dormant server behavior.

### `github-automation`
Use [`sub-skills/github-automation/SKILL.md`](sub-skills/github-automation/SKILL.md) for SDK-powered GitHub Actions examples, prompt-driven task runners, TODO scanning, examples-report rendering, and automation scripts that run agents from CI.

Read it when the request involves GitHub workflow YAML, `PROMPT_STRING`, prompt files/URLs, `LLM_API_KEY`, automated TODO management, routine maintenance actions, PR automation, or example-run summaries.

### `repo-development`
Use [`sub-skills/repo-development/SKILL.md`](sub-skills/repo-development/SKILL.md) for maintaining this monorepo: package boundaries, import rules, tool registration linting, settings compatibility, SDK/REST API deprecation policy, test selection, examples runner, release PR checks, pre-commit, and CI workflows.

Read it when editing source code, tests, examples, settings models, public APIs, REST routes, tools, workspace backends, Docker image publishing, or repository automation.

## Cross-cutting references

- [`references/package-overview.md`](references/package-overview.md): package surfaces, versions, public imports, and capability ownership.
- [`references/troubleshooting.md`](references/troubleshooting.md): install/import, credentials, optional browser/runtime, server, workspace, and maintenance failure patterns.
- [`references/repo-provenance.md`](references/repo-provenance.md): source snapshot and evidence paths used to create this skill; read before deciding whether a skill refresh is needed.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): structured metadata consumed by the managed repo-skills-router import flow.

## Boundary rules for future agents

- Use this skill as operating guidance; do not import it into live router state unless a user explicitly approves managed import.
- Runtime guidance is self-contained in this skill tree. Do not require access to the original generation checkout to use it.
- When maintaining a fresh checkout of `software-agent-sdk`, confirm current code and nearby `AGENTS.md` files before editing because repo policies may have changed after the provenance snapshot.
- Use generated scripts from this skill tree for diagnostics and helper workflows; when editing a live checkout, run that checkout's native tests and scripts from its repository root.
