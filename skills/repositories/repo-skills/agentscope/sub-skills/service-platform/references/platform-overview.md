# Platform Overview

## Purpose

Read this first when you need to bootstrap the AgentScope service with the verified `create_app` surface.

## Verified bootstrap contract

`create_app` has the signature:

`create_app(storage, message_bus, workspace_manager, knowledge_base_manager=None, knowledge_parsers=None, knowledge_chunker=None, blob_store=None, enable_index_worker=True, mcp_hubs=None, skill_hubs=None, *, extra_credentials=None, extra_middlewares=None, extra_agent_middlewares=None, extra_agent_tools=None, custom_subagent_templates=None, custom_agent_cls=None, resource_access_policy=None, channels=None, download_secret=None, title='AgentScope', version='2.0.6')`

## What the extra hooks do

- `extra_credentials` exposes extra credential classes to the UI / service layer.
- `extra_middlewares` adds FastAPI middleware wrappers.
- `extra_agent_middlewares` installs per-agent middleware factories.
- `extra_agent_tools` installs extra per-agent tools.
- `custom_subagent_templates` adds agent templates for the service UI and team flows.
- `custom_agent_cls` swaps the agent implementation used by the service.
- `resource_access_policy` controls access to service-managed resources.
- `channels` registers the external channel backends that the service can expose.

## Minimal mental model

1. Pick a storage backend.
2. Pick a message bus.
3. Pick a workspace manager.
4. Add knowledge-base, channel, and hub wiring only if the service needs them.
5. Use `uvicorn` or the project entrypoint to serve the FastAPI app.

## Common bootstrap pattern

```python
from agentscope.app import create_app
from agentscope.app.message_bus import InMemoryMessageBus
from agentscope.app.storage import AsyncSQLAlchemyStorage
from agentscope.app.workspace_manager import LocalWorkspaceManager

app = create_app(
    storage=AsyncSQLAlchemyStorage("sqlite+aiosqlite:///:memory:"),
    message_bus=InMemoryMessageBus(),
    workspace_manager=LocalWorkspaceManager(basedir="/tmp/agentscope-workspaces"),
)
```

## When to use this reference

- Before wiring a new service deployment.
- When you need to know which layer is responsible for a startup failure.
- When the app bootstraps but a service feature is missing and you need the right hook.
