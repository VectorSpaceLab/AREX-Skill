# Repo-Level Architecture and Schema Summary

For detailed instructions, use `sub-skills/graph-exploration/references/architecture-and-schema.md`.

CRG stores files, classes, functions, tests, and related nodes in SQLite with structural edges such as `CALLS`, `IMPORTS_FROM`, `INHERITS`, `CONTAINS`, and `TESTED_BY`. Flows and communities provide higher-level execution and architecture context. Use these semantics when explaining why graph answers differ from grep or LSP results.