# Query-navigation troubleshooting

## Fast symptom table

| Symptom | Likely cause | Recovery |
|---|---|---|
| `graphify: command not found` | Console script is not on `PATH`. | Use `python -m graphify ...` with the installed interpreter; fix the user's tool/PATH setup later. |
| `No graph found` or `graph file not found` | `graphify-out/graph.json` is missing or `--graph` points elsewhere. | Route to graph-building to create/update the graph, or pass the correct `--graph PATH`. |
| `graph file must be a .json file` | A directory, report, or export file was passed as the graph. | Use the actual `graph.json`; do not query `GRAPH_REPORT.md`, `graph.html`, or wiki files as graphs. |
| `graph.json is corrupted` or JSON load error | Broken/partial graph artifact or merge conflict. | Rebuild/update the graph; if the file has conflict markers, resolve via the graph merge workflow first. |
| `exceeds ... byte cap` | Graph is larger than the default graph-file safety cap. | Confirm size is expected and memory is available; set `GRAPHIFY_MAX_GRAPH_BYTES=700MB` or similar only after confirmation. |
| `No matching nodes found.` | Query terms do not appear in graph labels/IDs/source paths. | Try known labels from `god-nodes`/`explain`, source paths, or narrower graph vocabulary; do not invent synonym evidence. |
| `Ambiguous: ... matches N nodes in different files` | Same label exists in multiple files/workspaces. | Retry with repo-relative source path or full node ID from the ambiguity list. |
| Both path endpoints resolved to same node | Labels were too broad or synonyms collapsed to one match. | Use exact node IDs or source paths for both endpoints. |
| `No directed path found ... --undirected` | Stored edge direction does not connect source to target. | If flow/dependency direction matters, stop. If connectivity matters, rerun with `--undirected` and explain the loss of direction. |
| Reverse arrow such as `<--calls [EXTRACTED]--` | Undirected traversal walked opposite the stored edge. | Explain the stored relation direction honestly; use `affected` for callers/impact. |
| High-degree `explain` hides details behind `... more` | Node has more than 20 direct connections. | Read the grouped-by-file summary, then use relation/context filters, `affected`, or focused source path/node ID. |
| `[!] TRUNCATED` at top of query/MCP output | Token budget cut the response. | Raise `--budget`/`token_budget`, add `--context`, or switch to `explain`/`get_neighbors`. |
| Expected callers absent from `query` | Query matched broad context or wrong relation. | Use `graphify query "who calls X" --context call`, or `graphify affected "X" --relation calls`. |
| `affected` says `No unique node match` | Seed label/source path is ambiguous. | Use full node ID, exact file-level source path, or first disambiguate with `explain`. |
| `Lesson:` shows `contested` or stale | Work-memory overlay has mixed or outdated outcomes. | Treat as a warning; re-run `query`/`explain` and update with `save-result --outcome corrected|useful`. |
| Query log unexpectedly exists | Logging was explicitly enabled by environment. | Check `GRAPHIFY_QUERY_LOG`, `GRAPHIFY_QUERY_LOG_ENABLE`, and `GRAPHIFY_QUERY_LOG_RESPONSES`; use `GRAPHIFY_QUERY_LOG_DISABLE=1` to force off. |
| MCP import error says `mcp not installed` | Optional serving dependencies are missing. | Install `graphifyy[mcp]` in the serving interpreter. |
| HTTP 401 | API key required but missing or wrong. | Send `Authorization: Bearer <key>` or `X-API-Key: <key>`; confirm blank keys are not being used. |
| HTTP 404 | Client used the wrong mount path. | Use the configured `--path`, default `/mcp`. |
| HTTP Host/DNS-rebinding rejection | Client host header does not match non-wildcard bind. | Connect to the exact bound host, `localhost`, or `127.0.0.1`; do not disable security by binding wide without an API key. |
| Project-path MCP call fails, server still works | `project_path/graphify-out/graph.json` is missing/corrupt. | Fix that project's graph; the default graph can continue serving. |

## No graph or stale graph

`query`, `path`, `explain`, `affected`, `god-nodes`, and MCP serving all require an existing graph. If the user asks a codebase question and the graph is missing or stale for the files they care about, do not answer from memory or grep first. Route to graph-building with one of these likely actions:

```bash
graphify extract . --code-only          # first local code graph
graphify update .                       # code-only delta after a graph exists
graphify cluster-only . --no-viz        # refresh report/community artifacts only
```

After a rebuild/update, rerun the original query command and cite the new graph output.

## Ambiguous labels and source paths

Graphify intentionally refuses to guess when one label maps to different files. A safe disambiguation sequence is:

```bash
graphify explain "MetricsPort" --graph graphify-out/graph.json
# If ambiguous, pick one candidate path or ID from the output:
graphify explain "services/chat/src/application/ports/metrics.port.ts" --graph graphify-out/graph.json
graphify explain "chat_metrics_port" --graph graphify-out/graph.json
```

For file paths, Graphify prefers the file-level node when there is a unique `L1` or basename match. If no file-level node is unique, `affected` and `explain` should not guess.

## No path and reverse-arrow safety

Directed path is the default. Treat these as different facts:

- `A --calls--> B`: the graph stores a forward call/dependency from A to B.
- `B <--calls-- A`: an undirected search connected B back to A, but the stored relation is still A calls B.
- `No directed path found`: no stored direction connects source to target.

Safe response pattern:

1. Say whether the command was directed or undirected.
2. Quote the exact path line.
3. Explain each arrow in terms of stored edge direction.
4. If the user asked for impact/callers, run `affected` rather than reversing the semantic meaning.

## Query output is too broad or too small

For broad/noisy output:

```bash
graphify query "who calls PaymentService" --context call --budget 3000
graphify explain "PaymentService" --graph graphify-out/graph.json
```

For too-small/no-match output:

1. Run `god-nodes --json` or a known `explain` to discover actual labels.
2. Retry with exact labels, node IDs, or source paths.
3. If graph vocabulary truly lacks the user's concept, say the graph has no evidence and ask whether to rebuild/update or inspect source outside graph evidence.

For truncated output:

- Increase `--budget` / MCP `token_budget`.
- Add `--context call|import|field|parameter_type|return_type|generic_arg`.
- Use `explain` or MCP `get_neighbors` on a resolved node.
- Do not interpret missing lines after a truncation notice as absence.

## Work-memory repair

If a previous graph answer was useful:

```bash
graphify save-result --question "Q" --answer "A" --nodes NodeA NodeB --outcome useful
graphify reflect --if-stale --graph graphify-out/graph.json
```

If it was wrong:

```bash
graphify save-result \
  --question "Q" \
  --answer "the earlier answer was wrong" \
  --nodes NodeA \
  --outcome corrected \
  --correction "Correct answer with graph evidence."
graphify reflect --if-stale --graph graphify-out/graph.json
```

If a route was a dead end:

```bash
graphify save-result --question "Q" --answer "No graph evidence found." --outcome dead_end
graphify reflect --if-stale
```

Lessons are deterministic and no-LLM, but they are not proof. Re-run the relevant graph command when code changed or the lesson is contested.

## MCP serving failures

### Missing extra

```text
ImportError: mcp not installed. Run: pip install "graphifyy[mcp]"
```

Install the extra in the exact interpreter that starts the server, then rerun `python -m graphify.serve --help`.

### Unsafe HTTP bind

If the user wants `--host 0.0.0.0`, require an API key:

```bash
export GRAPHIFY_API_KEY="<secret>"
python -m graphify.serve graphify-out/graph.json --transport http --host 0.0.0.0 --api-key "$GRAPHIFY_API_KEY"
```

Do not expose a proprietary graph unauthenticated. Loopback (`127.0.0.1`) is the safe default.

### Wrong project graph in multi-project mode

MCP tools accept `project_path`; it must be a project directory, not the graph file itself. The server resolves it as `<project_path>/graphify-out/graph.json`. If the tool says the graph is missing or corrupt, fix that project graph and retry; the server should keep serving the default graph.

## When to stop and ask

Stop for user input instead of guessing when:

- The graph is missing/stale and rebuilding would write to user workspace.
- Multiple ambiguous nodes match and the user did not provide enough context to choose.
- The only available path is undirected but the user's question depends on call/import/dependency direction.
- The user asks to expose an HTTP server beyond localhost without approving authentication and bind host.
- Raising `GRAPHIFY_MAX_GRAPH_BYTES` could exceed available memory or policy limits.
