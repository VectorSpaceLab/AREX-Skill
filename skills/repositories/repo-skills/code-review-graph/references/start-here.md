# Start Here

## Purpose

Read this when a task names `code-review-graph` or asks for local-first code review graph setup, graph-backed code review, MCP graph tools, structural search, custom language support, or optional integrations.

## What code-review-graph does

`code-review-graph` builds a persistent local SQLite knowledge graph for a repository. It parses source code with Tree-sitter, stores nodes and relationships, and exposes graph-aware review/search workflows through a CLI and MCP server.

Core user value:

- build or update a graph once and reuse it across sessions;
- review diffs using changed nodes, impact radius, affected flows, and test gaps;
- query structural relationships such as callers, callees, imports, inheritors, and tests;
- optionally add semantic embeddings, custom languages, wiki pages, multi-repo search, and CI PR comments.

## Minimal setup

```bash
pip install code-review-graph
code-review-graph install
code-review-graph build
code-review-graph status
```

For an already installed package, smoke-check without touching any graph database:

```bash
python scripts/check_crg_install.py
```

## Route map

- Use `sub-skills/install-and-setup/` for installing, configuring, building/updating, serving, visualizing, or uninstalling CRG.
- Use `sub-skills/review-changes/` for diff/PR review, risk scoring, token savings, test gaps, affected flows, and PR comment rendering.
- Use `sub-skills/graph-exploration/` for search, graph queries, flows, communities, architecture, large functions, and refactor previews.
- Use `sub-skills/integrations-and-extensions/` for custom languages, embeddings, wiki, registry/daemon, GitHub Action, and eval workflows.

## What not to use this skill for

- General code review unrelated to CRG unless the user wants to use CRG as the review substrate.
- LSP-precise symbol editing when a language server is the better tool.
- Full benchmark reproduction without explicit permission for network/time-heavy work.
- VS Code extension development details; the generated skill covers the Python CLI/MCP package and public integrations, not the separate extension package internals.