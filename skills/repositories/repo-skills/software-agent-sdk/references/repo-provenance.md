# Repository Provenance

Schema: `disco.repo-provenance.v1`

This repo skill was generated for the OpenHands Software Agent SDK. It records the source snapshot and evidence paths so future agents can decide whether the skill should be refreshed.

## Source Snapshot

| Field | Value |
| --- | --- |
| repository | OpenHands Software Agent SDK |
| canonical skill id | `software-agent-sdk` |
| package distributions | `openhands-sdk`, `openhands-tools`, `openhands-workspace`, `openhands-agent-server` |
| package versions inspected | `1.41.0` for all four distributions |
| Python requirement | `>=3.12` |
| repository URL | `https://github.com/OpenHands/software-agent-sdk.git` |
| git commit | `281843c78094b179d570a48e3cac1857e259b1d7` |
| git branch | `main` |
| exact tag | none recorded |
| dirty state at initial evidence capture | source tree clean; generated `skills/` artifacts were added during skill production |
| required backend for verification | CPU-only and mocked in-process coverage |
| optional backends observed | Docker CLI available; Apptainer unavailable; browser binary not required for mandatory verification |

## Evidence Paths

Primary evidence used to create this skill:

- `README.md`
- `DEVELOPMENT.md`
- `AGENTS.md`
- `pyproject.toml`
- `openhands-sdk/pyproject.toml`
- `openhands-tools/pyproject.toml`
- `openhands-workspace/pyproject.toml`
- `openhands-agent-server/pyproject.toml`
- `openhands-sdk/openhands/sdk/`
- `openhands-tools/openhands/tools/`
- `openhands-workspace/openhands/workspace/`
- `openhands-agent-server/openhands/agent_server/`
- `examples/01_standalone_sdk/`
- `examples/02_remote_agent_server/`
- `examples/03_github_workflows/`
- `examples/05_skills_and_plugins/`
- `scripts/check_import_rules.py`
- `scripts/check_tool_registration.py`
- `scripts/render_examples_report.py`
- `tests/sdk/`
- `tests/tools/`
- `tests/workspace/`
- `tests/agent_server/`
- `tests/cross/`
- `tests/examples/test_examples.py`
- `.github/workflows/tests.yml`
- `.github/workflows/integration-runner.yml`
- `.github/workflows/run-examples.yml`
- `.github/workflows/server.yml`

## Installed Package Inspection

Live inspection verified these public facts:

- `openhands.sdk`, `openhands.tools`, `openhands.workspace`, and `openhands.agent_server` import successfully after editable workspace installation.
- `python -m openhands.agent_server --help` exposes `--host`, `--port`, `--reload`, `--check-browser`, `--import-modules`, and `--extra-python-path`.
- Core constructor signatures were checked for `LLM`, `Agent`, `Conversation`, `AgentContext`, `Tool`, `Workspace`, `LocalWorkspace`, `RemoteWorkspace`, `ConversationSettings`, `OpenHandsAgentSettings`, `ACPAgentSettings`, `HookConfig`, `HookDefinition`, `HookMatcher`, `MCPServer`, `DockerWorkspace`, `ApptainerWorkspace`, `APIRemoteWorkspace`, and `OpenHandsCloudWorkspace`.
- Default tool names and registry behavior were checked from the installed packages.
- `pip check` passed in the private inspection environment used during generation.

Private environment paths, activation commands, local Python executables, and package installation locations are intentionally omitted from this public provenance file.

## Refresh Signals

Refresh this skill when any of these change materially:

- Public imports or constructor signatures in `openhands.sdk.__all__`, `openhands.tools.__all__`, or `openhands.workspace.__all__`.
- `LLM`, `Agent`, `Conversation`, `AgentContext`, settings, hooks, MCP, skills, plugin, or secret models.
- Tool names, tool registration behavior, browser usability filtering, default tool presets, workflow tool methods, or sub-agent tool wiring.
- Agent-server CLI flags, deferred-init flow, auth headers, REST/WebSocket routes, `/server_info` fields, Docker image tags, PyInstaller packaging, or workspace implementations.
- Project skill loading precedence, AgentSkills `SKILL.md` conventions, `.mcp.json` handling, or plugin marketplace behavior.
- Repository development policies, API/REST deprecation rules, settings migration versions, CI workflows, examples-runner requirements, or package boundaries.
