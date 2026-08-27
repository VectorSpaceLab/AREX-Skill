# Package Overview

## Purpose

This reference summarizes the user-facing package surfaces and ownership boundaries in the OpenHands Software Agent SDK monorepo. Use it after the root router to decide which sub-skill has the detailed workflow.

## Packages

| Distribution | Import namespace | Main responsibility | Read next |
| --- | --- | --- | --- |
| `openhands-sdk` | `openhands.sdk` | Core SDK: LLMs, agents, conversations, events, settings, AgentSkills, MCP, hooks, plugins, secrets, tool specs, workspace interfaces. | `../sub-skills/agent-core/SKILL.md`, `../sub-skills/extensions/SKILL.md` |
| `openhands-tools` | `openhands.tools` | Runtime tool implementations, default presets, browser/terminal/file/task/workflow tools, sub-agent tool set. | `../sub-skills/built-in-tools/SKILL.md` |
| `openhands-workspace` | `openhands.workspace` | Remote workspace implementations for Docker, Apptainer, runtime API, and OpenHands Cloud. | `../sub-skills/remote-runtime/SKILL.md` |
| `openhands-agent-server` | `openhands.agent_server` | FastAPI REST/WebSocket server, conversation/event services, workspace routes, deferred init, Docker image build helpers. | `../sub-skills/remote-runtime/SKILL.md` |

All four distributions were inspected at version `1.41.0`.

## Core public imports

`openhands.sdk` exports the primary user API. Common imports include:

```python
from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.sdk import AgentContext, LocalWorkspace, RemoteWorkspace, Workspace
from openhands.sdk import ConversationExecutionStatus, Message, TextContent
```

`openhands.tools` re-exports common tool classes and presets:

```python
from openhands.tools import TerminalTool, FileEditorTool, TaskTrackerTool
from openhands.tools import TaskToolSet, WorkflowToolSet, get_default_agent
from openhands.tools.preset.default import get_default_tools
```

Browser tools are intentionally imported from their submodule because they have heavier optional runtime requirements:

```python
from openhands.tools.browser_use import BrowserToolSet
```

`openhands.workspace` exports remote workspace classes:

```python
from openhands.workspace import DockerWorkspace, ApptainerWorkspace
from openhands.workspace import APIRemoteWorkspace, OpenHandsCloudWorkspace
```

## Local agent path

A minimal local agent uses `LLM`, `Agent`, `Tool`, and `Conversation`:

```python
import os
from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool

llm = LLM(model=os.getenv("LLM_MODEL", "gpt-5.5"), api_key=os.getenv("LLM_API_KEY"))
agent = Agent(llm=llm, tools=[Tool(name=TerminalTool.name), Tool(name=FileEditorTool.name)])
conversation = Conversation(agent=agent, workspace=os.getcwd())
conversation.send_message("Inspect this project and summarize it.")
conversation.run()
```

For lifecycle, callbacks, async parity, interruption, persistence, condensation, and settings, read `../sub-skills/agent-core/SKILL.md`.

## Extension path

Use `AgentContext` and related models when changing what an agent knows or can load:

- `AgentContext(skills=[...])` for explicitly supplied skills.
- `AgentContext(load_project_skills=True)` for project `AGENTS.md`, `.agents/skills`, and `.openhands/skills`.
- `AgentContext(load_public_skills=True)` for public marketplace skills.
- `registered_marketplaces=[MarketplaceRegistration(...)]` for local or remote plugin/skill marketplaces.
- `mcp_config={"name": MCPServer(...)}` on `Agent` or settings variants for MCP tools.
- `HookConfig(...)` on `Conversation` for hook execution.

For precedence, `.mcp.json`, plugin lazy loading, and secrets, read `../sub-skills/extensions/SKILL.md`.

## Tool path

The SDK stores tool specs as `Tool(name=..., params={...})`; implementations are registered through the tool registry. Default execution tools are `terminal`, `file_editor`, and `task_tracker`. `browser_tool_set` and `task_tool_set` are opt-in or environment gated.

For names, registry APIs, custom tools, workflow scripts, and browser availability, read `../sub-skills/built-in-tools/SKILL.md`.

## Remote runtime path

Remote conversations and workspaces use the agent-server HTTP API. Start with:

```bash
python -m openhands.agent_server --host 127.0.0.1 --port 8000
```

Then use `Workspace(host="http://127.0.0.1:8000", working_dir="...")` or a remote workspace implementation. Read `../sub-skills/remote-runtime/SKILL.md` for server CLI flags, auth, deferred init, custom tool import modules, Docker/Apptainer/API/cloud workspace classes, and WebSocket caveats.

## Repository-maintenance path

For source edits, package boundaries matter:

- `openhands-sdk` must not import from `openhands.tools`, `openhands.workspace`, or `openhands.agent_server`.
- `openhands-tools` can import `openhands.sdk` but not `openhands.workspace` or `openhands.agent_server`.
- `openhands-workspace` can import SDK/tools and exposes lightweight imports.
- `openhands-agent-server` can import SDK/tools but not workspace implementations.

Read `../sub-skills/repo-development/SKILL.md` before making repository changes.
