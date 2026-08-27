---
name: headroom
description: "Use Headroom to compress LLM context, run a local proxy, wrap
  coding agents, manage memory and MCP retrieval, and integrate the Python or
  TypeScript SDK."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Headroom repo skill

Use this skill when a task involves Headroom / `headroom-ai`: context compression, local proxy routing, coding-agent wrappers, MCP/CCR retrieval, persistent memory, savings analytics, or Python/TypeScript SDK integration.

## Start with the route

- **Install, update, deploy, diagnose, report, or run evals:** read `sub-skills/ops/SKILL.md`.
- **Start a proxy, route a provider, wrap/unwrap an agent, or debug base URLs:** read `sub-skills/proxy-wrap/SKILL.md`.
- **Use memory, MCP, CCR retrieval, `learn`, or Codex recovery:** read `sub-skills/memory/SKILL.md`.
- **Call `compress`, use `HeadroomClient`, `SharedContext`, images/relevance/spreadsheets, or the TypeScript SDK:** read `sub-skills/sdk/SKILL.md`.

For a broad task that crosses routes, read `references/workflow-map.md` first and then load the smallest combination of sub-skills.

## Install and inspect

The public distribution is `headroom-ai`; the Python import is `headroom` and the CLI is `headroom`. The npm package is also named `headroom-ai`, but it is the TypeScript SDK and does **not** provide the Python CLI.

Common CLI install:

```bash
uv tool install --python 3.13 "headroom-ai[proxy,memory]"
# or
pip install "headroom-ai[proxy,memory]"
```

Add optional extras only for the requested surface: `code`, `relevance`, `image`, `spreadsheet`, `html`, `reports`, `otel`, or `evals`. Read `references/configuration-and-extras.md` before choosing a broad extra set.

Minimal import/CLI check:

```bash
python -c "import headroom; print(headroom.__version__)"
headroom --version
python scripts/check_headroom_environment.py --check-cli
```

## Core operating facts

- Headroom is local-first: the proxy runs on the user's machine or an explicitly chosen deployment host.
- A running proxy does not prove that an agent is routed through it; use `headroom doctor`, `perf`, and `savings` to correlate liveness, routing, and traffic.
- CCR is reversible compression: compressed content can carry hashes that are retrieved through `headroom_retrieve` or the proxy retrieval endpoints.
- Keep user-owned config and state scoped. Canonical state roots are `~/.headroom/config` and `~/.headroom`, with environment overrides.
- Cloud backends, MCP registration, durable wrappers, persistent deployments, model downloads, and external LLM evals are side-effectful or credentialed; do not perform them as an unrequested smoke test.

## Shared references

- `references/api-reference.md` summarizes verified Python and TypeScript entry points.
- `references/cli-reference.md` maps the top-level CLI to the owning sub-skill.
- `references/configuration-and-extras.md` covers extras, env vars, paths, and optional backends.
- `references/workflow-map.md` routes cross-surface tasks.
- `references/troubleshooting.md` covers package-wide failures.
- `references/repo-provenance.md` records the source snapshot; read it before deciding whether a refresh is required.
- `references/repo-routing-metadata.json` is structured metadata for managed router import.

## Safety boundaries

- Do not import this repo skill for a task that only needs generic LLM compression without Headroom-specific APIs, commands, config, or behavior.
- Do not run `headroom wrap`, `headroom init`, `headroom deploy`, `headroom install apply/remove`, `headroom update`, `headroom mcp install`, or destructive memory commands without explicit user intent.
- Never put API keys, OAuth tokens, cloud profiles, private paths, or temporary inspection-environment details into generated code or user-facing examples.
- Prefer loopback health checks and `--help` before starting a proxy, changing user config, downloading model assets, or contacting a provider.
