---
name: install-and-setup
description: "Install, configure, update, serve, and troubleshoot
  code-review-graph CLI/MCP graph setup across supported coding-agent
  platforms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Install and Setup

Use this sub-skill when the task is to install `code-review-graph`, create or refresh its local graph database, configure MCP clients or hooks, start the server, inspect status, visualize the graph, or diagnose setup failures.

## Start here

1. Confirm Python 3.10+ and install the package:
   ```bash
   pip install code-review-graph
   # or: pipx install code-review-graph
   # or: uvx code-review-graph --help
   ```
2. Configure an AI coding platform from the target repository root:
   ```bash
   code-review-graph install
   ```
3. Build the graph once:
   ```bash
   code-review-graph build
   ```
4. Verify:
   ```bash
   code-review-graph status
   ```
5. If a future session cannot see the MCP server, restart the client/editor and verify the session opened in the same repository root.

Read [references/workflows.md](references/workflows.md) for platform setup, graph lifecycle, server, visualization, uninstall, and environment-check workflows. Read [references/troubleshooting.md](references/troubleshooting.md) when a command is missing, a graph is stale, MCP does not start, HTTP serving is rejected, or Python/package resolution is unclear.

## Route by task

| User task | Do this |
| --- | --- |
| "Install CRG in this repo" | Run `code-review-graph install`, then `code-review-graph build`, then `code-review-graph status`. |
| "Only configure Codex/Cursor/Claude/etc." | Use `code-review-graph install --platform <platform>` with a supported platform name. |
| "The graph is stale" | Run `code-review-graph update --brief`; use `build` for a full rebuild after major branch switches or parser/schema concerns. |
| "Run the MCP server" | Use `code-review-graph serve` for stdio or `code-review-graph serve --http --host 127.0.0.1 --port 5555` for loopback HTTP. |
| "Watch the repo" | Use `code-review-graph watch` for one repo or route multi-repo daemon tasks to `integrations-and-extensions`. |
| "Show graph stats" | Use `code-review-graph status` or `code-review-graph status --json`. |
| "Visualize the graph" | Use `code-review-graph visualize` after a graph exists; open the generated local HTML. |
| "Remove CRG" | Use `code-review-graph uninstall --dry-run` first; add `--yes` only after confirming the preview. |

## Supported setup surfaces

`install`/`init` can configure supported platforms including Codex, Claude Code, CodeBuddy Code, Cursor, Windsurf, Zed, Continue, OpenCode, Antigravity, Gemini CLI, Qwen, Kiro, Qoder, GitHub Copilot, and GitHub Copilot CLI. Platform config paths and generated hook/skill behavior are summarized in [references/workflows.md](references/workflows.md).

The graph database is project-scoped by default under `.code-review-graph/graph.db`. The Python package is user-scoped, while MCP config and hooks are normally project- or client-scoped depending on platform.

## Safe bundled helpers

- Run [scripts/diagnose_pypi_connectivity.py](scripts/diagnose_pypi_connectivity.py) only when installs fail while downloading build dependencies from PyPI.
- From the root skill, [../../scripts/check_crg_install.py](../../scripts/check_crg_install.py) smoke-checks package import, version, CLI discovery, and packaged docs without creating a graph.

## Boundaries

- For reviewing changed code, use `review-changes`.
- For structural exploration, search, architecture, or refactor previews, use `graph-exploration`.
- For embeddings, custom languages, GitHub Action setup, multi-repo registry, daemon, wiki, or eval workflows, use `integrations-and-extensions`.

## Verification anchors

Native tests that ground this sub-skill include install lifecycle tests, CLI build/update/status tests, MCP server wiring tests, HTTP Host/Origin guard tests, and status/stat regressions. Run selected native tests only after the whole repo skill is integrated; do not use them as runtime dependencies.