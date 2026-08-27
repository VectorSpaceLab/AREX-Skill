---
name: sandbox-agents
description: "Configure OpenAI Agents SDK SandboxAgent workspaces, manifests,
  capabilities, clients, snapshots, mounts, and sandbox safety boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sandbox Agents

Use this sub-skill when a task mentions `SandboxAgent`, `Manifest`, `SandboxRunConfig`, `LocalDir`, `GitRepo`, `UnixLocalSandboxClient`, `DockerSandboxClient`, sandbox capabilities, snapshots, mounts, memory, or workspace materialization.

Sandbox agents are beta. Prefer verified local API behavior over stale examples, keep host filesystem access narrow, and separate agent defaults from per-run sandbox session choices.

## Quick Routing

| Need | Use |
| --- | --- |
| Workspace files, manifest entries, permissions, path grants, remote mounts, or safety boundaries | [Manifest and capabilities](references/manifest-and-capabilities.md) |
| Local coding agent setup, Docker/hosted client choice, snapshots, session reuse, skill mounting, shell/apply_patch workflows | [Workflows](references/workflows.md) |
| Optional extras, host path failures, remote mounts, archive errors, permissions, session/snapshot mismatch, beta API drift | [Troubleshooting](references/troubleshooting.md) |
| Validate a small manifest description without starting a sandbox | [`scripts/validate_manifest.py`](scripts/validate_manifest.py) |

## Core Rules

- Keep `SandboxAgent` for agent defaults: `default_manifest`, `instructions`, `base_instructions`, `capabilities`, and `run_as`.
- Put backend/session choices in `RunConfig(sandbox=SandboxRunConfig(...))`: `client`, `options`, `session`, `session_state`, `manifest`, `snapshot`, and limits.
- Treat `Manifest` as the fresh-session workspace contract; reused sessions, serialized session state, or snapshots can override what is live.
- Keep manifest entry keys workspace-relative; never use absolute entry paths or `..` escapes.
- Use `extra_path_grants` only for trusted application-approved absolute host paths, not model output.
- Start local development with `UnixLocalSandboxClient`; move to Docker or hosted providers when isolation, image parity, or managed execution matters.

## Route Elsewhere

- Ordinary shell/function tools, handoffs, and guardrails without sandbox sessions: `../tools-handoffs-guardrails/SKILL.md`.
- General `Runner`, `RunConfig`, sessions, streaming, and model-call behavior: `../core-runtime/SKILL.md`.
- Repository maintainer setup, tests, packaging, and local development commands: `../repo-development/SKILL.md`.
