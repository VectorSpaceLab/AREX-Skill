---
name: gptme
description: "Operate the gptme terminal AI agent, provider configuration,
  tools, server/Web UI, protocols, evals, and repository-maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# gptme Repo Skill

Use this skill when a task names `gptme`, `gptme-server`, `gptme-agent`, `gptme-acp`, `gptme-eval`, gptme tools/plugins/hooks/MCP, gptme provider configuration, gptme Web UI/API, or maintenance of the `gptme` repository.

`gptme` is a terminal-first local AI agent package with a chat CLI, persistent conversations, tool execution, provider-agnostic LLM routing, browser/computer/MCP/extensibility surfaces, a REST/SSE server plus Web UI, ACP/TUI interfaces, benchmark/eval tooling, and a Python/Web UI source repository.

## First checks

For installed-package tasks, verify the target runtime before making claims:

```bash
python scripts/check_gptme_environment.py --check-server-app
python scripts/run_gptme_help_matrix.py
```

These generated helpers only perform import, entrypoint, help, and route-registration checks. They do not start a chat, server, browser, Docker container, eval run, or model call.

For maintainer tasks, first identify the target `gptme` checkout and read `sub-skills/repo-development/SKILL.md`. Checkout-maintainer commands are scoped to that checkout; generated helper scripts live in this skill tree and accept explicit target paths where needed.

## Install and runtime orientation

Read [references/installation-and-entrypoints.md](references/installation-and-entrypoints.md) when the task asks how to install `gptme`, choose extras, or locate an entry point. Core facts:

- Distribution/import root: `gptme`.
- Verified version baseline: `0.32.1`.
- Python metadata: `>=3.10`.
- Common isolated installs: `pipx install gptme` or `uv tool install gptme`.
- Use focused extras: `[server]`, `[browser]`, `[acp]`, `[tui]`, `[telemetry]`, or `[eval]` only when that workflow needs them.
- Do not install `[all]`, browser binaries, Node dependencies, Docker images, or system services unless the task explicitly requires them.

Read [references/package-architecture.md](references/package-architecture.md) when you need source/module ownership, verified public signatures, or routing by package area. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/optional-extra/provider/server/eval failures before drilling into a sub-skill.

Read [references/repo-provenance.md](references/repo-provenance.md) before trusting exact signatures or maintainer commands in a different checkout. If commit, metadata, entry points, major docs, server API, tool APIs, eval schemas, or maintainer policy changed, run `refresh-repo-skill`.

## Route by task

| Task signal | Read |
| --- | --- |
| Run `gptme` from terminal, build a command, manage named/resumed/forked conversations, inspect logs, use slash commands, queue prompts, automate non-interactively, or use `gptme-agent`. | [sub-skills/cli-and-conversations/SKILL.md](sub-skills/cli-and-conversations/SKILL.md) |
| Configure global/project/chat files, API keys, `/account`, `gptme-auth`, default model priority, provider prefixes, local/Ollama models, OpenRouter privacy/routing, or custom provider plugins. | [sub-skills/configuration-and-providers/SKILL.md](sub-skills/configuration-and-providers/SKILL.md) |
| Choose built-in tools, debug tool allowlists/formats, create custom `ToolSpec` tools, package plugins, register hooks/commands, configure MCP, or decide between plugins, skills, and lessons. | [sub-skills/tools-and-extensibility/SKILL.md](sub-skills/tools-and-extensibility/SKILL.md) |
| Start or deploy `gptme-server`, operate the Web UI, call REST/SSE APIs, handle tokens/CORS/Host validation, use ACP/TUI, or troubleshoot hosted/local Web UI connectivity. | [sub-skills/server-webui-and-protocols/SKILL.md](sub-skills/server-webui-and-protocols/SKILL.md) |
| Build `gptme-eval` commands, list suites, run or avoid model-costly benchmarks, summarize `eval_results.csv`, process leaderboard/trends, or use SWE-bench/T-bench integrations. | [sub-skills/evals-and-benchmarks/SKILL.md](sub-skills/evals-and-benchmarks/SKILL.md) |
| Modify the `gptme` source repo, select focused pytest/Web UI commands, follow branch/commit/staging policy, update docs, validate packages, or handle release/Web UI development. | [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md) |

## Safety boundaries

- Do not make live LLM calls, OAuth/browser auth attempts, eval runs, Docker builds, or browser/computer actions unless the task explicitly asks for them and credentials/runtime are available.
- Do not print raw API keys, OAuth tokens, server bearer tokens, local credential file contents, or private paths.
- Treat browser, computer-use, Docker, Node/Web UI, provider API, and full eval workflows as optional/external runtime surfaces.
- For server deployment beyond loopback, require an explicit auth, CORS/Host, TLS/proxy, and exposure plan.
- For repository maintenance, never push directly to `master`, stage files explicitly, and keep the change/test scope narrow.

## Router metadata

`references/repo-routing-metadata.json` contains structured scenario metadata for managed repo-skill import. This creation run was requested with **not import**, so no managed import has been attempted.
