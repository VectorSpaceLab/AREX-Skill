---
name: graph-exploration
description: "Explore code relationships, search, flows, communities,
  architecture, and refactor previews with code-review-graph."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graph Exploration

Use this sub-skill when the task is to understand code structure after a graph exists: find callers or callees, search by keyword or embedding, inspect flows or communities, identify large functions, or preview safe refactors.

## Start here

1. Ensure the graph exists and is current.
2. Ask the smallest useful query first.
3. Escalate from search to graph traversal to flow/community/refactor analysis only as needed.

Read [references/search-and-analysis.md](references/search-and-analysis.md) for search, traversal, flow, community, architecture, and refactor workflows. Read [references/architecture-and-schema.md](references/architecture-and-schema.md) for graph-node and edge semantics, flow/community storage, and supported query shapes. Read [references/troubleshooting.md](references/troubleshooting.md) when search falls back, flows miss entry points, communities are sparse, or a refactor preview looks incomplete.

## Route by task

| User task | Do this |
| --- | --- |
| "Who calls this function?" | `query_graph_tool(pattern="callers_of", target=...)` |
| "What does this function call?" | `query_graph_tool(pattern="callees_of", target=...)` |
| "Find tests for this symbol" | `query_graph_tool(pattern="tests_for", target=...)` |
| "Search for login/auth code" | `semantic_search_nodes_tool` or `query_graph_tool` depending on whether the answer is semantic or structural. |
| "Show execution paths" | `list_flows_tool`, then `get_flow_tool` or `get_affected_flows_tool`. |
| "Show architecture" | `get_architecture_overview_tool` and, if needed, `list_communities_tool`. |
| "Find large functions" | `find_large_functions_tool`. |
| "Preview a rename" | `refactor_tool(mode="rename")`. |
| "Find dead code" | `refactor_tool(mode="dead_code")`. |

## Use search vs graph traversal correctly

- Use `semantic_search_nodes` for natural-language or fuzzy discovery.
- Use `query_graph_tool` when the question is about exact structural relationships.
- Use `traverse_graph_tool` when you already have a promising node and want to walk outward.
- Use `get_minimal_context_tool` first if you are unsure where to start.

## Flows and communities

Flows represent execution paths, usually rooted in entry points or decorators. Communities represent structural clusters and help with architecture-level reasoning. A good exploration answer usually explains both the local symbol and the surrounding flow/community context when relevant.

## Refactor previews

The safe refactor path is preview first, apply second:

1. `refactor_tool(mode="rename", ...)` or `refactor_tool(mode="dead_code", ...)`
2. Inspect the returned edits and affected locations.
3. Only then run `apply_refactor_tool` if the change is intentional.

## Boundaries

- For install/setup, use `install-and-setup`.
- For diff review and PR comments, use `review-changes`.
- For embeddings, custom languages, registry/daemon, wiki, and eval workflows, use `integrations-and-extensions`.

## Verification anchors

Native tests that ground this route include search tests, flow tests, community tests, integration tests, refactor tests, visualization tests, and status/regression tests. These are validation anchors only; do not rely on them as runtime instructions.