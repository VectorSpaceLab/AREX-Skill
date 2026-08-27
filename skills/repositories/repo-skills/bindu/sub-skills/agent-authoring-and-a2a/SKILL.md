---
name: agent-authoring-and-a2a
description: "Author, run, and troubleshoot Python Bindu agents, A2A task flow,
  skill advertising, and negotiation surfaces."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Agent Authoring and A2A

Use this sub-skill when a task is about writing a Python Bindu agent, calling `bindufy()`, validating handler/config shape, advertising skills, reading agent cards, sending A2A JSON-RPC messages, polling tasks, or debugging the task lifecycle.

## Route here for

- Creating a minimal Python agent with `bindu.penguin.bindufy.bindufy(config, handler)`.
- Understanding handler return values: plain completion text, `input-required`, and `auth-required` structured responses.
- Building or validating Bindu config dictionaries: `author`, `name`, `deployment.url`, `skills`, `private_skills`, `storage`, `scheduler`, `execution_cost`, and telemetry/debug fields.
- Understanding `AgentManifest`, `BinduApplication`, `TaskManager`, `ManifestWorker`, and A2A JSON-RPC methods.
- Loading `skill.yaml` or `SKILL.md` skill bundles and exposing `/agent/skills` documentation.
- Interpreting `/agent/negotiation` skill-match results.

## Route elsewhere

- DID signatures, Hydra bearer auth, private catalog authorization, mTLS, and x402 internals → `../security-identity-and-payments/`.
- TypeScript SDK, proto changes, gRPC registration, callback ports, and heartbeats → `../grpc-and-language-sdks/`.
- `bindu serve`, `bindu deploy`, boxd runtime, source packaging, storage/scheduler operations, and observability → `../deployment-runtime-and-operations/`.
- Gateway planner and Inbox operator workflows → `../gateway-inbox-and-orchestration/`.

## References and helper

- `references/api-reference.md` — Python API surface, config keys, handler contract, app routes, and skills loader.
- `references/a2a-task-lifecycle.md` — JSON-RPC message/send, tasks/get, states, ownership, artifacts, and polling.
- `references/skills-and-negotiation.md` — skill formats, endpoints, private/public distinction, and negotiation scoring.
- `references/troubleshooting.md` — handler/config/skill/UUID/task-state troubleshooting.
- `scripts/inspect_bindu_agent_surface.py` — safe package-surface inspection without starting a server.

## Minimal pattern

```python
from bindu.penguin.bindufy import bindufy

def handler(messages):
    latest = messages[-1].get("content", "") if messages else ""
    if not latest:
        return {"state": "input-required", "prompt": "Send a message."}
    return f"Echo: {latest}"

bindufy({
    "author": "you@example.com",
    "name": "echo-agent",
    "description": "A small Bindu echo agent.",
    "deployment": {"url": "http://localhost:3773", "expose": False},
    "skills": [],
    "storage": {"type": "memory"},
    "scheduler": {"type": "memory"},
}, handler)
```

## Operating reminders

- The handler must be callable and must accept exactly one parameter named `messages` for local Python agents.
- `deployment.url` is required and must be HTTP or HTTPS.
- `message/send` returns a submitted task; poll `tasks/get` or stream status for the final answer.
- Terminal tasks are immutable. Continue with a new task id in the same context.
- Skills describe capabilities for discovery/routing; the handler still implements behavior.
