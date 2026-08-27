# Repo-Level Custom Language Summary

For detailed instructions, use `sub-skills/integrations-and-extensions/references/custom-languages.md`.

Create `.code-review-graph/languages.toml` in the target repo, map extensions to a grammar shipped by `tree_sitter_language_pack`, provide node types, then rebuild the graph.

Built-ins cannot be overridden. Invalid TOML, bad grammar names, missing dot-prefix extensions, and entries with no node types are skipped conservatively.