# Graphify query and navigation CLI reference

## Purpose

Use this reference to answer from an existing Graphify `graph.json` without reopening original source documentation. Every command here is read-only against the graph except `save-result` and `reflect`, which write lesson artifacts under `graphify-out/` or paths you specify.

Package identity:

- Distribution package: `graphifyy`.
- Import package and module command: `graphify` / `python -m graphify`.
- Primary graph path: `graphify-out/graph.json` unless `--graph PATH` is supplied.

Before any answer:

```bash
test -f graphify-out/graph.json || { echo "No graph found; build or update it first." >&2; exit 1; }
graphify reflect --if-stale 2>/dev/null || true
```

If `graphify` is not on `PATH`, use `python -m graphify ...` with the interpreter where `graphifyy` is installed.

## Read-command decision table

| User need | Command | Notes |
|---|---|---|
| Broad context around a question or label | `graphify query "QUESTION"` | BFS traversal by default; returns `NODE` and `EDGE` text. |
| Chain-shaped exploration | `graphify query "QUESTION" --dfs` | DFS is better for “how does A reach B?” when the exact endpoint is not known. |
| Explicit concept-to-concept route | `graphify path "A" "B"` | Directed by default; use `--undirected` only for direction-agnostic connectivity. |
| One node and its direct neighbors | `graphify explain "X"` | Best for disambiguation, source locations, and high-degree summaries. |
| Blast radius of changing a node | `graphify affected "X"` | Reverse traversal over dependency/call/import-like relations. |
| Hubs / architecture centers | `graphify god-nodes` | Lists most-connected non-file entities; use `--json` for machine-readable output. |
| Persist outcome | `graphify save-result ...` then `graphify reflect` | Builds deterministic lessons and an optional read-time overlay. |

## `graphify query`

```bash
graphify query "show the auth flow" --graph graphify-out/graph.json
graphify query "who calls ChargeCustomerService" --context call --budget 3000
graphify query "how does ingest reach report" --dfs --budget 4000
```

Flags:

- `--dfs`: use depth-first traversal instead of the default breadth-first traversal.
- `--context C`: restrict traversal to edges whose `context` equals `C`; may be repeated.
- `--budget N`: approximate token budget for rendered output; default is `2000`.
- `--graph PATH`: graph file; default is `graphify-out/graph.json`.

Context filters and common aliases:

| Canonical context | Common prompts/aliases |
|---|---|
| `call` | calls, called, caller, invoke |
| `import` | imports, imported, module |
| `field` | fields, member, property |
| `parameter_type` | param, parameter, argument |
| `return_type` | return, returns |
| `generic_arg` | generic, template |
| `attribute` | annotation, decorator |
| `export` | exports, exported |

When no explicit `--context` is supplied, obvious phrasing such as “who calls X” or “callers of X” can infer `Context: call (heuristic)` in the output. Explicit filters override heuristics.

Interpretation:

- Header format: `Traversal: BFS depth=2 | Start: [...] | N nodes found` plus optional `Context: ...`.
- `NODE Label [src=... loc=... community=...]` is node evidence. A `learning=preferred`, `learning=tentative`, or `learning=contested:stale` suffix comes from `reflect`; it is an orientation hint, not structural truth.
- `EDGE Source --relation [confidence context=...]--> Target at=file:line` uses the stored edge direction, even if traversal reached the edge from the target side.
- Confidence values indicate source of the edge: `EXTRACTED` is structural/parser-derived, `INFERRED` is weaker semantic inference, and `AMBIGUOUS` needs caution or corroboration.
- `at=file:line` is the edge site, such as the caller/importer line, not necessarily the target definition line.
- If output begins with `[!] TRUNCATED`, raise `--budget`, add `--context`, or switch to `explain`/MCP `get_node`/`get_neighbors`. Do not treat omitted nodes as absent.

Query matching is vocabulary-based over graph labels, IDs, and source paths with stopword removal, source-file scoring, and IDF weighting. It does not prove synonyms that are absent from the graph. If `query` returns `No matching nodes found.`, report that the graph lacks matching vocabulary and try a known label/source path only if one is available from prior graph output.

## `graphify path`

```bash
graphify path "CallerService" "TargetWorker" --graph graphify-out/graph.json
graphify path "TargetWorker" "CallerService" --undirected --graph graphify-out/graph.json
```

Flags:

- `--graph PATH`: graph file.
- `--directed`: explicit directed search. This is the default.
- `--undirected`: ignore edge direction while finding the route; output still renders the true stored relation direction.

Output examples:

```text
Shortest path (1 hops):
  CallerService --calls [EXTRACTED]--> TargetWorker
```

```text
Shortest path (1 hops):
  TargetWorker <--calls [EXTRACTED]-- CallerService
```

Rules:

- Directed search is the safe default because call/import/dependency direction matters.
- A reverse arrow means the route was found by ignoring direction or by traversing a mixed-direction segment; the relation still points the other way.
- If you see `No directed path found ... Re-run with --undirected`, only retry with `--undirected` when the user's question is about connectivity rather than flow.
- If both endpoints resolve to the same node, retry with a more specific label or exact node ID.
- If a warning says the endpoint match was ambiguous, verify with `explain` before using the path as evidence.
- Path output reports the actual stored relation(s) and confidence, not a fabricated `calls` relation. If an edge lacks a relation, it may print `related`.

## `graphify explain`

```bash
graphify explain "TargetWorker" --graph graphify-out/graph.json
graphify explain "app/api/example/route.ts" --graph graphify-out/graph.json
```

What it returns:

- Node label, ID, source file/location, file type, community, degree, and optional `Lesson:` line.
- Up to 20 direct connections sorted by neighbor degree.
- Connection arrows by true direction:
  - `--> Neighbor [relation] [confidence] file:line`: queried node has an outgoing edge to neighbor.
  - `<-- Neighbor [relation] [confidence] file:line`: neighbor has an incoming edge to the queried node.
- For high-degree nodes, a `... and N more` section with grouped counts by direction and file, so callers/importers beyond the first 20 are not silently lost.

Disambiguation behavior:

- Exact source-file path matches prefer the file-level node (`source_location` like `L1`) when multiple members share that source file.
- Same labels across different files produce an `Ambiguous:` result with candidate source paths and IDs. Retry with the repo-relative path or full node ID.
- Same-label matches within one source file can still resolve normally; do not over-disambiguate when `explain` gave a concrete node.

## `graphify affected`

```bash
graphify affected "TargetWorker" --graph graphify-out/graph.json
graphify affected "TargetWorker" --relation calls --depth 2 --graph graphify-out/graph.json
```

Purpose: find nodes impacted by a change to `X` by walking incoming edges in reverse.

Defaults:

- Depth: `2`.
- Relations: `calls`, `indirect_call`, `references`, `imports`, `imports_from`, `dynamic_import`, `re_exports`, `inherits`, `extends`, `implements`, `uses`, `mixes_in`, `embeds`, and `requires`.

Behavior:

- Seed resolution accepts exact node IDs, exact labels, bare function names without `()`, unique source-file paths, and unambiguous contains matches.
- If several candidates tie and no file-level node is unique, it returns `No unique node match for X`; do not guess.
- Results include the relation and the edge site when available, e.g. `- CallerService [calls] src/caller.py:L12`.
- For edge-location gaps, it honestly falls back to the affected node's definition/source location.

Use `affected` instead of a backwards `path` when the user asks “who would break if this changes?” or “who calls/imports this?”

## `graphify god-nodes`

```bash
graphify god-nodes --graph graphify-out/graph.json
graphify god-nodes --top 5 --json --graph graphify-out/graph.json
# underscore spelling is also accepted:
graphify god_nodes --graph graphify-out/graph.json
```

Text output starts with `God nodes (most connected):`. JSON output is a list of objects with at least `id`, `label`, and `degree`. File-level nodes are excluded from the ranking so the list focuses on load-bearing entities rather than filenames.

Use god nodes for orientation and architecture review, not as proof that a specific edge exists. Follow up with `explain` or `path` for evidence.

## Work memory: `save-result` and `reflect`

```bash
graphify save-result \
  --question "who calls TargetWorker?" \
  --answer "CallerService calls TargetWorker via src/caller.py:L12." \
  --type query \
  --nodes TargetWorker CallerService \
  --outcome useful

graphify reflect --if-stale --graph graphify-out/graph.json
```

`save-result` flags:

- `--question Q`: original user question.
- `--answer A` or `--answer-file FILE`: answer body.
- `--type query|path_query|explain`: query category; default `query`.
- `--nodes N1 N2 ...`: cited node labels or IDs.
- `--outcome useful|dead_end|corrected`: work-memory signal.
- `--correction TEXT`: required context when marking `corrected`.
- `--memory-dir DIR`: default `graphify-out/memory`.

`reflect` flags:

- `--memory-dir DIR`: input memory docs.
- `--out FILE`: default `graphify-out/reflections/LESSONS.md`.
- `--graph PATH`: groups lessons by graph community and writes `.graphify_learning.json` next to the graph.
- `--analysis PATH`, `--labels PATH`: optional community sidecars.
- `--if-stale`: skip if the lessons file is newer than memory/graph inputs.
- `--half-life-days N`, `--min-corroboration N`: scoring controls.

Lesson semantics:

- `useful` citations become tentative or preferred sources after scoring and corroboration.
- `dead_end` records paths/questions not to repeat blindly.
- `corrected` records wrong answers and the replacement truth.
- When a graph is provided, stale or ambiguous cited nodes are dropped from the overlay rather than being attached to the wrong node.
- `explain` and `query` can display overlay hints, but graph edges remain the source of truth.

## Query logging privacy

Graphify query/path/explain logging is off by default. It writes plaintext only when explicitly enabled:

- `GRAPHIFY_QUERY_LOG=/path/to/log.jsonl`: write to this path.
- `GRAPHIFY_QUERY_LOG_ENABLE=1`: write to a default cache log.
- `GRAPHIFY_QUERY_LOG_RESPONSES=1`: also record full rendered responses.
- `GRAPHIFY_QUERY_LOG_DISABLE=1`: force logging off and wins over enable variables.

Keep logging off for proprietary questions unless the user explicitly opts in.

## Graph file safety

Read commands reject missing graphs, non-`.json` paths, corrupt JSON, and graph files above the configured size cap before parsing. The default graph size cap is 512 MiB and can be raised with `GRAPHIFY_MAX_GRAPH_BYTES`, for example `GRAPHIFY_MAX_GRAPH_BYTES=700MB`. Raise it only after confirming the graph is expected to be that large and the machine has memory headroom.
