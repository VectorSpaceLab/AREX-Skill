# Search and Analysis Workflows

## Purpose

Read this when you need to move from a graph snapshot to specific answers about calls, imports, flows, communities, architecture, or refactors.

## Search modes

### Semantic search

Use `semantic_search_nodes_tool` when a natural-language query is best answered by ranking likely nodes first.

Typical uses:
- find a symbol by a rough description,
- find an entry point by intent,
- locate related names when you do not know the exact spelling.

### Structural search

Use `query_graph_tool` when the relationship matters more than the wording.

Common patterns include:
- `callers_of`
- `callees_of`
- `imports_of`
- `importers_of`
- `children_of`
- `tests_for`
- `inheritors_of`
- `file_summary`

### Graph walk

Use `traverse_graph_tool` when you already have a node and want to walk outward from it. Prefer small depths and token budgets.

## Flow analysis

Flows capture execution paths, not just symbol links.

Useful commands:

```bash
code-review-graph flows
code-review-graph flow --id <id>
code-review-graph impact --files a.py b.py
```

Use flow analysis when the user asks about entry points, critical paths, affected routes, or review blast radius.

## Community and architecture analysis

Use community tools when the user asks about higher-level structure:

```bash
code-review-graph communities
code-review-graph community --name parser
code-review-graph architecture
```

Community questions are a good fit for:
- module boundaries,
- cross-community coupling,
- cohesion,
- and architecture overviews.

## Refactor preview workflow

Preview before applying:

```bash
code-review-graph refactor rename --old-name helper --new-name new_helper
code-review-graph refactor dead_code --kind Function
```

Inspect the returned edits, then apply only after confirming the scope:

```bash
code-review-graph refactor ...
code-review-graph apply-refactor <refactor-id>
```

## Large-function and hotspot workflow

Use `find_large_functions_tool` to locate oversized nodes, then combine the result with callers, tests, and community context before refactoring or review.

## When to read architecture and schema

Read [architecture-and-schema.md](architecture-and-schema.md) when the task involves:
- node or edge kinds,
- what a flow or community row contains,
- or how to interpret `tests_for`, `CALLS`, `IMPORTS_FROM`, `TESTED_BY`, and related relationships.

## Troubleshooting cue

If search falls back to keyword matching, if a graph query returns fewer results than expected, or if flow/community data looks sparse, read [troubleshooting.md](troubleshooting.md) before assuming the code is wrong.