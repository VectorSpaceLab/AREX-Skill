# Repo-Level Search and Analysis Summary

For detailed graph exploration instructions, use `sub-skills/graph-exploration/`.

## Choose the right tool

- Structural relationship: `query_graph_tool`.
- Natural language or fuzzy node discovery: `semantic_search_nodes_tool`.
- Execution path: `list_flows_tool` and `get_flow_tool`.
- Architecture overview: `get_architecture_overview_tool` and community tools.
- Refactor planning: `refactor_tool`, then `apply_refactor_tool` only after preview review.

## Minimal token workflow

1. Start with `get_minimal_context_tool(task="...")`.
2. Query one relationship at a time.
3. Use `detail_level="minimal"` where available.
4. Read source files only when the graph result identifies the exact file/symbol to inspect.