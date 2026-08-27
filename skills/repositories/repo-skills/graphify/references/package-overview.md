# Graphify Package Overview

## Purpose

Read this for a compact orientation to Graphify's public package, graph artifacts, and workflow boundaries before choosing a focused sub-skill.

## Identity

| Surface | Name |
|---|---|
| Public PyPI distribution | `graphifyy` |
| Python import package | `graphify` |
| Main CLI | `graphify` |
| MCP server entry point | `graphify-mcp` or `python -m graphify.serve` |
| Default output directory | `graphify-out/` |
| Primary graph artifact | `graphify-out/graph.json` |

The package requires Python `>=3.10`. The base install is enough for local code/AST graph construction and CLI graph reads. Optional extras are installed only for selected surfaces such as provider-backed semantic extraction, PDF/Office/video media handling, watch mode, MCP serving, database clients, SVG export, or optional language parsers.

## What Graphify does

Graphify turns a folder of code, docs, papers, images, video/audio transcripts, or fetched URL material into a persistent knowledge graph. The graph is not a vector index: it stores nodes, edges, confidence labels, source locations, communities, god nodes, surprising connections, and optional hyperedges. Agents can query it repeatedly without rereading the whole repository.

The core pipeline is:

```text
detect -> extract -> build/merge graph -> cluster -> analyze -> report -> export/query
```

Important outputs:

| Artifact | Role |
|---|---|
| `graphify-out/graph.json` | NetworkX node-link graph consumed by query/path/explain/export/MCP. |
| `graphify-out/GRAPH_REPORT.md` | Human-readable community report, hubs, surprises, confidence audit, and suggested questions. |
| `graphify-out/graph.html` | Browser visualization when generated and not skipped. |
| `graphify-out/manifest.json` | Portable change-detection baseline for update/watch/hook flows. |
| `graphify-out/cache/` | AST and semantic cache. Optional to preserve for speed. |
| `graphify-out/wiki/`, `obsidian/`, `graph.graphml`, `cypher.txt`, `GRAPH_TREE.html`, callflow HTML | Export outputs owned by the exports route. |
| `graphify-out/memory/` and `graphify-out/reflections/LESSONS.md` | Optional query-result memory and deterministic lessons. |

## Confidence and evidence

Edges carry confidence labels:

- `EXTRACTED`: directly observed from source, e.g. imports, calls, citations, links, manifests.
- `INFERRED`: derived by resolver or semantic extraction; useful but weaker than direct evidence.
- `AMBIGUOUS`: uncertain; preserve uncertainty in answers.

When answering from a graph, cite the graph output's labels, relations, confidence tags, and source locations. If the graph lacks evidence, say so and route to graph-building or targeted source inspection rather than inventing missing edges.

## Primary workflow families

- **Build/update graphs:** local AST extraction, semantic extraction, update/watch/add/cluster-only, cache/manifest validation. See [graph-building](../sub-skills/graph-building/SKILL.md).
- **Query/navigate graphs:** `query`, `path`, `explain`, `affected`, `god-nodes`, lessons, MCP serving. See [query-navigation](../sub-skills/query-navigation/SKILL.md).
- **Assistant integrations:** packaged Graphify skills, always-on guidance, PreToolUse/BeforeTool hooks, Git hooks, strict mode, platform installs. See [agent-integration](../sub-skills/agent-integration/SKILL.md).
- **Exports/integrations:** local export formats, multi-repo merge, database push boundaries, PR helpers. See [exports-integrations](../sub-skills/exports-integrations/SKILL.md).
- **Extractor troubleshooting:** file-format support, optional parser extras, language resolver/node-id issues, maintainer extractor tests. See [extractor-troubleshooting](../sub-skills/extractor-troubleshooting/SKILL.md).

## Optional-surface policy

The generated skill's verified base environment covered the CPU base package and code-only graph/query smoke checks. Optional surfaces are public and documented, but they require focused setup before live claims:

- Provider backends need the relevant SDK extra and credentials/service.
- PDF/Office/Google/video inputs need their extras and sometimes external auth, model downloads, or network budget.
- MCP serving needs `graphifyy[mcp]`.
- Neo4j/FalkorDB/PostgreSQL workflows need clients plus live services/credentials for pushes/introspection.
- SVG needs the `svg` extra.
- Optional parser extras such as `sql`, `terraform`, `dm`, and `pascal` affect specific source formats.

Install the smallest extra set matching the user request. Avoid `graphifyy[all]` unless the user explicitly wants broad optional coverage and accepts the dependency cost.
