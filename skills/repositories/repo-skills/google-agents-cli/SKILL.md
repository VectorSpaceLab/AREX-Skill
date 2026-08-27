---
name: google-agents-cli
description: "Use this repo skill when a task involves the Google Agents CLI
  (google-agents-cli / agents-cli) lifecycle for ADK agent projects:
  install/setup, requirements planning, scaffolding, ADK code patterns,
  evaluation, deployment, Gemini Enterprise publication, and observability."
metadata:
  disco-role: operating
  author: Google
  license: Apache-2.0
  version: 1.3.1
  requires:
    bins:
      - agents-cli
    install: "uv tool install google-agents-cli"
disable-model-invocation: true
license: Apache 2.0
---

# Google Agents CLI Repo Skill

Use this skill for the `google-agents-cli` package and its `agents-cli` command. It is a router for the repository-specific operating graph; load the narrow sub-skill before acting.

## Start Here

1. Verify the CLI is available: `agents-cli --version` and `agents-cli --help`.
2. If the user is planning a new agent, start with `sub-skills/workflow/SKILL.md` before any scaffold command.
3. If the user names a command family, route directly using the table below.
4. For command discovery without the source checkout, use `scripts/inspect_cli_tree.py` after installing `google-agents-cli`.

## Route by Task

| User need | Read |
| --- | --- |
| End-to-end ADK agent lifecycle, requirements clarification, safe coding-agent workflow, command map, project rules | `sub-skills/workflow/SKILL.md` |
| Create, enhance, or upgrade a project; choose prototype/deployment/session/CI-CD flags | `sub-skills/scaffold/SKILL.md` |
| Write or change Python ADK agent code, tools, callbacks, state, A2A, trigger sources, or clone-and-study recipes | `sub-skills/adk-code/SKILL.md` |
| Generate/grade/analyze/compare/optimize evals, datasets, metrics, LLM-as-judge, user simulation | `sub-skills/eval/SKILL.md` |
| Deploy to Agent Runtime, Cloud Run, or GKE; provision infra; configure CI/CD; test deployed endpoints; troubleshoot deploy failures | `sub-skills/deploy/SKILL.md` |
| Register a deployed agent with Gemini Enterprise, choose ADK vs A2A registration, or manage Agent Registry records | `sub-skills/publish/SKILL.md` |
| Configure/debug traces, logging, prompt-response logging, BigQuery Agent Analytics, or telemetry | `sub-skills/observability/SKILL.md` |

## Common Command Aliases

- `agents-cli create` is an alias for `agents-cli scaffold create`.
- `agents-cli update` reinstalls bundled Agents CLI skills into detected coding-agent targets.
- `agents-cli data-ingestion` is retained only as a removed-command stub; RAG/data ingestion is now a clone-and-study recipe, not a CLI flag family.
- `agents-cli info` is the quickest way to inspect project configuration from inside a scaffolded project.

For a full command tree and representative verification commands, read `references/command-surface.md`.

## Installation and Runtime Checks

Recommended install:

```bash
uv tool install google-agents-cli
agents-cli --version
agents-cli --help
```

If `agents-cli` is unavailable, read `references/troubleshooting.md` and the setup section in `sub-skills/workflow/SKILL.md` before making project changes.

## Operating Rules

- Do not invent removed scaffold flags such as `--datastore` or an `agentic_rag` template; use recipe study through `sub-skills/adk-code/SKILL.md`.
- Do not hand-write the A2A serving surface for scaffolded Python ADK projects; the scaffolded `adk` template already wires A2A into the FastAPI app.
- Do not deploy, publish, create cloud resources, initialize git remotes, or push code without explicit user approval and required credentials.
- Use evaluations (`sub-skills/eval/SKILL.md`) for LLM response quality; do not rely on brittle pytest assertions over model text.
- Treat this repo skill as public operating guidance. It does not require the original source checkout once installed.

## Repo Metadata

- Provenance and evidence baseline: `references/repo-provenance.md`.
- Router import metadata: `references/repo-routing-metadata.json`.
- Cross-cutting install, auth, and workflow failure recovery: `references/troubleshooting.md`.
