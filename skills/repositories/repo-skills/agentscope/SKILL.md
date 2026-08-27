---
name: agentscope
description: "AgentScope repo skill for building agents, provider connectors,
  RAG and memory workflows, service deployments, and local or sandboxed
  workspaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgentScope

Use this skill for AgentScope agent workflows, provider setup, retrieval and memory, FastAPI service deployment, or workspace/sandbox execution.

## Quick start

- Install the broad runtime set with `uv pip install "agentscope[full]"` or install only the extras needed for one sub-skill.
- Target Python 3.11 or newer.
- After install, run `python scripts/check_env.py --show-backends` from the skill tree to confirm imports and local backend availability.
- Read `references/repo-provenance.md` when you need to check whether this skill matches the current checkout.
- Read `references/troubleshooting.md` when install or import behavior is off.

## Route map

### `sub-skills/agent-core/`
Use for Agent, Toolkit, built-in tools, permissions, message/event handling, task tools, MCP tool wiring, and local skill loading.

Typical triggers:
- "How do I build an AgentScope agent?"
- "Why is this tool blocked or inactive?"
- "How do local skills load into a toolkit?"

### `sub-skills/provider-connectors/`
Use for chat, embedding, formatter, and TTS provider classes, provider credentials, and provider-specific extras or environment variables.

Typical triggers:
- "Which extra do I need for Gemini/Ollama/XAI?"
- "How do I configure embeddings or TTS?"
- "Why does a provider import fail?"

### `sub-skills/rag-memory/`
Use for `KnowledgeBase`, RAG middleware, vector stores, filesystem memory, mem0, ReMe, and the RAG or memory examples.

Typical triggers:
- "How do I index documents and search them?"
- "How do I attach RAG to an agent?"
- "How do mem0 or ReMe memory modes work?"

### `sub-skills/service-platform/`
Use for `create_app`, storage, message buses, channels, hubs, MCP, schedules, knowledge-base service, and service bootstrap/deployment.

Typical triggers:
- "How do I start the AgentScope service?"
- "How do I wire Redis or SQLite storage?"
- "How do channels, hubs, or MCP fit into the service?"

### `sub-skills/workspace-sandboxes/`
Use for local workspaces and sandboxed backends such as Docker, Bubblewrap, Apple Container, E2B, Daytona, K8s, and OpenSandbox.

Typical triggers:
- "How do I create a workspace?"
- "Which backend do I need for this sandbox?"
- "Why did archive import or backend initialization fail?"

## How to choose

- If the task is about agent orchestration, start with `agent-core`.
- If the task is about provider credentials or model classes, start with `provider-connectors`.
- If the task is about retrieval or long-term memory, start with `rag-memory`.
- If the task is about HTTP service deployment or platform routes, start with `service-platform`.
- If the task is about the execution sandbox or workspace backend, start with `workspace-sandboxes`.

If a task spans more than one area, read the most operationally specific sub-skill first, then cross-link to the others.

## Shared reference and diagnostics

- `references/repo-provenance.md` — current repo snapshot and refresh baseline.
- `references/repo-routing-metadata.json` — machine-readable routing metadata for repo-skill discovery.
- `references/troubleshooting.md` — cross-cutting install/import and package-selection problems.
- `scripts/check_env.py` — import and backend availability check for this skill tree.

## Minimal import check

After installation, a quick check should succeed:

```bash
python -c "import agentscope; from agentscope.agent import Agent; from agentscope.tool import Toolkit"
```

If that import fails, fix the environment before using any sub-skill.
