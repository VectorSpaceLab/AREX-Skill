# CLI Reference

## Purpose

Use this concise CLI map when deciding which `code-review-graph` command to run. For setup depth, route to `install-and-setup`; for review depth, route to `review-changes`; for optional integrations, route to `integrations-and-extensions`.

## Core lifecycle

| Command | Use |
| --- | --- |
| `code-review-graph install` / `init` | Configure MCP and supported client integrations. |
| `code-review-graph uninstall` | Remove CRG-owned configs/data/hooks/skills; preview with `--dry-run`. |
| `code-review-graph build` | Full graph build. |
| `code-review-graph update` | Incremental update. |
| `code-review-graph postprocess` | Re-run flows, communities, FTS, and optional embedding refresh on an existing graph. |
| `code-review-graph status` | Show graph statistics and freshness metadata. |
| `code-review-graph watch` | Keep one repo updated on file changes. |
| `code-review-graph forget PATH ...` | Remove already-parsed paths from the graph. |

## Review and analysis

| Command | Use |
| --- | --- |
| `code-review-graph detect-changes` | Risk-scored change analysis against the existing graph. |
| `code-review-graph impact` | Blast radius for changed files. |
| `code-review-graph query` | Relationship lookup such as callers/callees/tests/imports. |
| `code-review-graph search` | Keyword/semantic node search. |
| `code-review-graph flows` / `flow` | List or inspect stored execution flows. |
| `code-review-graph communities` / `community` | List or inspect graph communities. |
| `code-review-graph architecture` | Architecture overview from community structure. |
| `code-review-graph large-functions` | Find oversized functions/classes/files. |
| `code-review-graph refactor` | Preview graph-backed refactors such as rename or dead-code analysis. |

## Optional integrations

| Command | Use |
| --- | --- |
| `code-review-graph embed` | Compute embeddings for semantic search. |
| `code-review-graph visualize` | Generate interactive local graph visualization. |
| `code-review-graph wiki` | Generate markdown wiki pages from graph communities. |
| `code-review-graph register` / `unregister` / `repos` | Manage the multi-repo registry. |
| `code-review-graph daemon ...` | Manage the multi-repo watch daemon. |
| `code-review-graph eval` | Run evaluation/benchmark helpers. |
| `code-review-graph serve` / `mcp` | Start the MCP server over stdio or loopback HTTP. |

## Useful flags

- `--repo <path>`: explicitly choose the repository root.
- `--base <ref>`: choose the diff base for update/review commands.
- `--brief`: compact CLI output where available.
- `--json`: script-friendly output where supported.
- `--platform <name>`: target one platform during install.
- `--http --host 127.0.0.1 --port 5555`: serve MCP over loopback Streamable HTTP.