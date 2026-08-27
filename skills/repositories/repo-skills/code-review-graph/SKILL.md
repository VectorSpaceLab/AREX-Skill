---
name: code-review-graph
description: "Use code-review-graph for local-first CLI/MCP code knowledge
  graphs, graph-backed code review, structural search, and repository-analysis
  integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# code-review-graph

Use this repo skill when a task names `code-review-graph`, CRG, graph-backed code review, local MCP graph tools, blast-radius analysis, structural code search, risk-scored PR review, custom language parsing, or multi-repo code graph operations.

`code-review-graph` is a Python package and CLI/MCP server that builds a local SQLite code knowledge graph from Tree-sitter parses, updates it incrementally, and exposes token-efficient review/search workflows to coding agents.

## Fast route

1. For first-time setup, read [references/start-here.md](references/start-here.md), then route to `install-and-setup`.
2. For changed-code review or PR review, route to `review-changes`.
3. For graph queries, architecture, flows, communities, or refactors, route to `graph-exploration`.
4. For optional custom languages, embeddings, wiki, registry/daemon, GitHub Action, or eval, route to `integrations-and-extensions`.

## Minimal install and smoke check

```bash
pip install code-review-graph
code-review-graph install
code-review-graph build
code-review-graph status
```

For an existing install, the bundled [scripts/check_crg_install.py](scripts/check_crg_install.py) verifies import, package version, CLI discovery, and packaged docs without creating or updating a graph.

## Sub-skill routes

| Sub-skill | Read when |
| --- | --- |
| [install-and-setup](sub-skills/install-and-setup/SKILL.md) | Installing CRG, configuring MCP clients, building/updating the graph, checking status, running the MCP server, visualizing, watching, or uninstalling. |
| [review-changes](sub-skills/review-changes/SKILL.md) | Reviewing a diff or PR, computing blast radius, risk scoring, test gaps, token savings, affected flows, or rendering a PR review comment. |
| [graph-exploration](sub-skills/graph-exploration/SKILL.md) | Finding callers/callees/tests/imports, searching graph nodes, inspecting flows/communities/architecture, finding large functions, or previewing refactors. |
| [integrations-and-extensions](sub-skills/integrations-and-extensions/SKILL.md) | Custom languages, embeddings/providers, wiki generation, multi-repo registry, daemon watch workflows, GitHub Action setup, or eval/benchmark reproduction. |

## Shared references

- [references/cli-reference.md](references/cli-reference.md) maps common CLI commands and flags.
- [references/mcp-tools.md](references/mcp-tools.md) maps MCP tools and token-discipline rules.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install, graph freshness, optional dependency, provider, and SQLite issues.
- [references/architecture-and-schema.md](references/architecture-and-schema.md) summarizes graph node/edge semantics.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot used to create this skill and when to refresh it.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for managed repo-skill routing.

## Operating principles

- Prefer graph tools over broad file reads when the user asks a structural question.
- Start with compact context (`get_minimal_context_tool`) when an MCP session is available.
- Use `detail_level="minimal"` unless the next step requires source snippets or full graph details.
- Keep optional extras optional; do not install embeddings, communities, wiki, eval, enrichment, or `all` unless the task needs them.
- Treat cloud embeddings and external services as opt-in because code-derived text may leave the machine.
- Rebuild or update the graph before trusting review/search answers after a branch switch, rebase, or large edit.

## Boundaries and non-fits

Do not use this skill as a general-purpose LSP replacement, full source-code reading strategy, or benchmark runner unless the user explicitly asks for CRG workflows. This skill covers the Python CLI/MCP package and public integrations, not detailed development of the separate VS Code extension package.

## Verification expectations

This runtime skill is grounded by package metadata, public docs, installed-package inspection, existing repo-local CRG skills, and native test candidates spanning install, CLI, MCP, review, search, flows, communities, refactor, optional integrations, and CI workflow safety. Final verification artifacts live outside this runtime skill under the review/test artifact directory.