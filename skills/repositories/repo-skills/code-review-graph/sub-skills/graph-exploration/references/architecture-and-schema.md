# Architecture and Schema Notes

## Purpose

Read this when you need the graph’s object model, node/edge kinds, flow/community storage, or the meaning of the main review and exploration fields.

## Verified graph model

The package stores a persistent SQLite graph with:

- **nodes** for files, classes, functions, tests, and specialized framework nodes,
- **edges** for calls, imports, inheritance, containment, tested-by, and specialized relationships,
- **flows** for execution paths,
- **communities** for clusters of related code,
- **metadata** for last build and schema information,
- **FTS/search** support for keyword lookup,
- and optional embedding rows in a separate embedding store.

## Important node kinds

- `File`
- `Class`
- `Function`
- `Test`
- `Type`
- plus framework-enriched node kinds such as endpoint/scheduler/config-related nodes where supported.

## Important edge kinds

- `CALLS`
- `IMPORTS_FROM`
- `INHERITS`
- `IMPLEMENTS`
- `CONTAINS`
- `TESTED_BY`
- `REFERENCES`
- `DEPENDS_ON`
- `HANDLES`
- `TRIGGERS`
- `PUBLISHES`

## Qualified names

The graph uses qualified names to identify nodes. Files are stored by absolute path. Functions and methods attach to the file path with `::` separators.

Examples:

- `/repo/src/auth.py`
- `/repo/src/auth.py::login`
- `/repo/src/auth.py::AuthService.login`

## Flow and community interpretation

- Flows are stored execution paths with criticality, depth, and member ordering.
- Communities are clusters with cohesion, size, dominant language, and optional descriptions.
- Architecture overviews are built from community structure and cross-community edge analysis.

## Search and review implications

- `tests_for` is a structural relationship, not a heuristic text match.
- `get_impact_radius_tool` and review tools depend on graph paths and edge kinds rather than raw grep results.
- If a query seems to miss a symbol, check whether the file is ignored, the language is unsupported, or the graph is stale.

## When this matters most

Read this file before exploring a repo that has many languages, decorators, framework-enriched nodes, or multiple levels of structural relationships. It helps explain why the graph answers differ from plain text search.
