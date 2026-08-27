---
name: query-navigation
description: "Query and navigate existing Graphify graphs with CLI commands,
  work-memory lessons, edge-safe interpretation, and optional MCP serving."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Graphify query-navigation

Use this sub-skill when the user already has a Graphify `graphify-out/graph.json` (or gives another `graph.json`) and wants answers, paths, node explanations, blast-radius checks, architectural hub lists, query lessons, or an MCP service layer from that graph.

## Route here for

- Answering repository or corpus questions from an existing graph before raw source browsing.
- `graphify query`, `graphify path`, `graphify explain`, `graphify affected`, and `graphify god-nodes`.
- Interpreting `NODE` and `EDGE` lines: source locations, relation names, `EXTRACTED`/`INFERRED`/`AMBIGUOUS` confidence, edge context, and stored edge direction.
- Handling no-match, no-path, same-endpoint, ambiguous-label, high-degree, and truncated-output cases safely.
- Persisting query outcomes with `graphify save-result` and refreshing lessons with `graphify reflect`.
- Serving the graph to MCP clients over stdio or Streamable HTTP when the optional MCP dependencies are installed.
- Running the bundled tiny-graph query smoke before trusting a new environment.

## Route elsewhere

- Missing, stale, corrupt, or intentionally rebuilt graph artifacts: [graph-building](../graph-building/SKILL.md).
- Export formats, merged graphs, database/Cypher destinations, PR exports, or visualization artifacts: [exports-integrations](../exports-integrations/SKILL.md).
- Assistant skill installation, always-on guidance, hooks, or platform config: [agent-integration](../agent-integration/SKILL.md).
- Source-format support, parser/extractor bugs, node-ID normalization, or wrong extractor output: [extractor-troubleshooting](../extractor-troubleshooting/SKILL.md).
- Broad package orientation: [root graphify skill](../../SKILL.md) when available.

## Read order

1. [references/cli-reference.md](references/cli-reference.md) for command recipes, flags, output interpretation, edge direction, affected/god-node helpers, query logging, and work-memory lessons.
2. [references/mcp-serving.md](references/mcp-serving.md) when exposing a graph through MCP stdio or HTTP.
3. [references/troubleshooting.md](references/troubleshooting.md) for missing/corrupt/oversized graphs, ambiguous nodes, no path, reverse arrows, truncation, lesson overlays, query-log privacy, and MCP failures.
4. [scripts/query_tiny_graph.py](scripts/query_tiny_graph.py) for a safe local smoke that creates a temporary graph and validates query/path/explain direction.

## Graph-first answer flow

1. **Confirm the graph.** Default to `graphify-out/graph.json`; use a user-provided graph only with `--graph PATH`. If the graph is missing, corrupt, too large for the configured cap, not a JSON graph, or stale for the user's question, route to graph-building instead of guessing from source files.
2. **Refresh lessons when present.** At the start of graph work, run `graphify reflect --if-stale` in the project root when `graphify-out/memory/` may exist, then read `graphify-out/reflections/LESSONS.md`. Treat preferred/contested/dead-end lessons as orientation only; re-verify stale or contested claims against graph output.
3. **Pick the smallest read command.** Use `query` for broad context, `query --dfs` for chain-shaped exploration, `path` for an explicit concept-to-concept route, `explain` for one node and direct neighbors, `affected` for reverse impact, and `god-nodes` for high-degree architectural hubs.
4. **Answer only from graph evidence.** Cite `NODE` labels, `EDGE` relations, confidence tags, context tags, and `source_file:source_location` locations. If the graph lacks enough evidence, say that plainly and either narrow the query or route to graph-building/source inspection only after acknowledging the graph gap.
5. **Preserve direction.** Query traversal may walk both callers and callees for context, but rendered edges keep the stored direction. `path` is directed by default; use `--undirected` only when the user asks whether two nodes are connected regardless of dependency/call direction.
6. **Resolve ambiguity explicitly.** If `explain` or MCP neighbor lookup reports multiple same-label nodes in different files, retry with the repo-relative source path or full node ID. Do not present one arbitrary file as fact.
7. **Close the loop.** After a useful answer, dead end, or correction, save it with `graphify save-result --outcome useful|dead_end|corrected`, then run or schedule `graphify reflect --if-stale` so future sessions see the lesson overlay.

## Command quick map

```bash
# Broad graph context; BFS is default. Add --dfs for chain-oriented traversal.
graphify query "show the auth flow" --graph graphify-out/graph.json
graphify query "who calls ChargeCustomerService" --context call --budget 3000

# Explicit paths; directed by default, undirected only for connectivity questions.
graphify path "CallerService" "TargetWorker" --graph graphify-out/graph.json
graphify path "TargetWorker" "CallerService" --undirected --graph graphify-out/graph.json

# Focused node explanation and direct neighbors.
graphify explain "TargetWorker" --graph graphify-out/graph.json

# Reverse impact and hubs.
graphify affected "TargetWorker" --relation calls --depth 2 --graph graphify-out/graph.json
graphify god-nodes --top 10 --graph graphify-out/graph.json

# Work memory.
graphify save-result --question "Q" --answer "A" --nodes TargetWorker CallerService --outcome useful
graphify reflect --if-stale --graph graphify-out/graph.json
```

Use `python -m graphify ...` when the `graphify` console command is not on `PATH` but the Python package imports.

## Hard-case guidance

- **Reverse-arrow path:** `TargetWorker <--calls [EXTRACTED]-- CallerService` means the undirected traversal walked from `TargetWorker` to `CallerService`, but the stored edge still says `CallerService` calls `TargetWorker`. Do not rewrite it as `TargetWorker calls CallerService`; use `affected` or a call-context `query` when the user needs callers.
- **No directed path:** `path` follows stored direction by default. If the user asked for dependency flow, stop at the no-path result. If they asked for connectivity, retry with `--undirected` and explain that the result ignores direction.
- **Ambiguous node label:** Use the full node ID or source path reported by `explain`; never choose one same-label node from a different file without a disambiguating query.
- **Shared HTTP MCP exposure:** Install `graphifyy[mcp]`, keep the default host `127.0.0.1` for local use, and require an API key before binding to `0.0.0.0` or `::`. Prefer `GRAPHIFY_API_KEY` over inline secrets.

## Quick smoke

From the `graphify` repo-skill root directory:

```bash
python sub-skills/query-navigation/scripts/query_tiny_graph.py
# If the package is installed in another interpreter:
python sub-skills/query-navigation/scripts/query_tiny_graph.py --python /path/to/python
```

The helper creates a temporary Graphify node-link graph, runs only local read commands plus the deterministic lesson loop, asserts stored edge direction and reverse-arrow rendering, and deletes the temporary directory unless `--keep-temp` is passed.
