# MCP Tools Reference

## Purpose

Use this when an MCP-capable agent is connected to a repository with `code-review-graph` and needs the right graph tool instead of broad file scanning.

## Recommended entry point

Start with:

```text
get_minimal_context_tool(task="<your task>")
```

Then escalate to the narrow tool that answers the next question.

## Core tools

| Tool | Use |
| --- | --- |
| `build_or_update_graph_tool` | Build or incrementally update the graph. |
| `run_postprocess_tool` | Re-run flows, communities, FTS, and optional embedding refresh. |
| `list_graph_stats_tool` | Inspect graph stats. |
| `get_docs_section_tool` | Load token-optimized CRG docs sections. |
| `get_review_context_tool` | Build review context from changed files. |
| `detect_changes_tool` | Risk-scored diff analysis. |
| `get_impact_radius_tool` | Blast radius around changed files. |
| `get_affected_flows_tool` | Flows touched by changed files. |
| `query_graph_tool` | Relationship queries: callers, callees, imports, tests, inheritors, children, file summary. |
| `semantic_search_nodes_tool` | Keyword/vector search for nodes. |
| `traverse_graph_tool` | BFS/DFS walk from a best-matching node. |
| `find_large_functions_tool` | Oversized node search. |

## Flow/community/architecture tools

| Tool | Use |
| --- | --- |
| `list_flows_tool` / `get_flow_tool` | Stored execution paths. |
| `list_communities_tool` / `get_community_tool` | Structural clusters. |
| `get_architecture_overview_tool` | Compact architecture overview. |
| `get_hub_nodes_tool` | Most connected nodes. |
| `get_bridge_nodes_tool` | Betweenness-style chokepoints. |
| `get_knowledge_gaps_tool` | Isolated/thin/untested structural weaknesses. |
| `get_surprising_connections_tool` | Unexpected coupling. |
| `get_suggested_questions_tool` | Auto-generated review questions. |

## Optional tools

| Tool | Use |
| --- | --- |
| `embed_graph_tool` | Compute embeddings for semantic search. |
| `generate_wiki_tool` / `get_wiki_page_tool` | Generate or inspect wiki pages. |
| `list_repos_tool` / `cross_repo_search_tool` | Multi-repo registry search. |
| `refactor_tool` / `apply_refactor_tool` | Preview and optionally apply graph-backed refactors. |

## Token discipline

- Prefer `detail_level="minimal"` unless the next step truly needs full detail.
- Use graph tools before grep/read for structural questions.
- Fall back to file reads only when the graph result is missing, stale, or too abstract.