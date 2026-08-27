---
name: remote-runtime
description: "Routes OpenHands agent-server startup, REST/WebSocket routes,
  remote conversations, and Docker/Apptainer/API/cloud workspace workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Remote Runtime

Use this sub-skill for the server/runtime layer: `python -m openhands.agent_server`, REST and WebSocket APIs, remote conversations, `RemoteWorkspace`, Docker and Apptainer workspaces, runtime API and cloud workspaces, deferred init, auth, and custom tool import paths.

## What this route owns

- Agent-server CLI flags, startup, and local server helpers.
- `/alive`, `/health`, `/ready`, `/server_info`, `/api/init`, `/api/conversations`, and workspace routes.
- Session API keys, bootstrap init keys, and warm-pool/deferred init flows.
- `DockerWorkspace`, `DockerDevWorkspace`, `ApptainerWorkspace`, `APIRemoteWorkspace`, and `OpenHandsCloudWorkspace`.
- `ManagedAPIServer`-style helpers for local examples.

## Start here

Read [`references/agent-server-cli.md`](references/agent-server-cli.md) for CLI flags and startup behavior. Read [`references/workspaces-and-remote-conversations.md`](references/workspaces-and-remote-conversations.md) for workspace classes and remote conversation flow. Read [`references/troubleshooting.md`](references/troubleshooting.md) for auth, deferred init, browser, tmux, and workspace failures.

Run [`scripts/managed_api_server.py`](scripts/managed_api_server.py) when you need a local helper that starts the agent-server subprocess and waits for `/health`.

## Typical triggers

- "Start the OpenHands agent-server locally."
- "Why does `/api/init` return 503?"
- "How do I authenticate remote conversations?"
- "How do I run a Docker or Apptainer workspace?"
- "How do I import a custom tool module into the server?"

## Cross-links

- For local `Conversation` construction, go to [`../agent-core/SKILL.md`](../agent-core/SKILL.md).
- For tool registration and default tools, go to [`../built-in-tools/SKILL.md`](../built-in-tools/SKILL.md).
- For GitHub Actions examples that launch a server, go to [`../github-automation/SKILL.md`](../github-automation/SKILL.md).
