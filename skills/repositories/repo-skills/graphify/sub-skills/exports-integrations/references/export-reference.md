# Export reference

This reference is for transforming an existing Graphify graph into portable local artifacts or, only when explicitly requested, pushing it to a graph database. It assumes `graphify-out/graph.json` already exists. If it does not, route to [graph-building](../../graph-building/SKILL.md).

## Preflight

```bash
# Defaults to graphify-out/graph.json in the current directory.
ls graphify-out/graph.json

# Use this when the graph lives elsewhere.
graphify export html --graph /path/to/graph.json
```

Useful sidecars when present:

- `.graphify_analysis.json`: communities, cohesion, god nodes, and surprises. Required for `graphify export wiki`; used by other exporters when available.
- `.graphify_labels.json`: community labels. Pass with `--labels PATH` when it is not next to the graph.
- `GRAPH_REPORT.md`: report highlights for `graphify export callflow-html`.

`GRAPHIFY_OUT` can redirect default readers/writers for commands that honor the default graph output directory, but the most explicit and portable pattern is `--graph PATH` plus explicit output flags where available.

## Local export command map

| Format/task | Command | Output | Notes and validation |
|---|---|---|---|
| Interactive browser graph | `graphify export html [--graph PATH] [--labels PATH] [--node-limit N] [--no-viz]` | `graph.html` beside the graph | Uses a local HTML file with vis-network. Default visualization limit is 5000 nodes; `--node-limit` can force an aggregated community view. `--no-viz` removes/skips `graph.html`. Validate the file exists and is non-empty. |
| Architecture/call-flow HTML | `graphify export callflow-html [GRAPH|DIR] [--graph PATH] [--labels PATH] [--report PATH] [--sections PATH] [--output HTML] [--lang auto|zh-CN|en] [--max-sections N] [--diagram-scale N] [--max-diagram-nodes N] [--max-diagram-edges N]` | Default `graphify-out/<project>-callflow.html` or `--output` | Builds Mermaid-based architecture sections, diagrams, and call tables from `graph.json`, labels, and report highlights. For large graphs, lower `--max-sections` or diagram caps. Validate stdout says `callflow HTML written`. |
| D3 collapsible source tree | `graphify tree [--graph PATH] [--output HTML] [--root PATH] [--max-children N] [--top-k-edges N] [--label NAME]` | Default `GRAPH_TREE.html` beside the graph | This is a top-level command, not `graphify export tree`. Use repo-relative `--root`; an explicit root that matches no `source_file` fails instead of flattening. Validate stdout says `wrote`. |
| Agent-crawlable Markdown wiki | `graphify export wiki [--graph PATH] [--labels PATH]` | `wiki/index.md` plus article pages | Requires non-empty community data. If `.graphify_analysis.json` is missing/empty, run `graphify cluster-only .` or rebuild through [graph-building](../../graph-building/SKILL.md). Validate `wiki/index.md`. |
| Obsidian vault and Canvas | `graphify export obsidian [--graph PATH] [--labels PATH] [--dir PATH]` | Default `obsidian/` beside the graph, or custom `--dir`; also writes `graph.canvas` | Writes one note per node and community notes. When pointed at an existing vault, Graphify tracks owned files in `.graphify_obsidian_manifest.json` and refuses to overwrite non-owned user notes. Validate Markdown notes and `graph.canvas`. |
| SVG | `graphify export svg [--graph PATH] [--labels PATH]` | `graph.svg` beside the graph | Requires optional `svg` extra (`graphifyy[svg]`) because the exporter imports matplotlib. Use for README/Notion/Obsidian embeds. Validate the file begins as SVG/XML. |
| GraphML | `graphify export graphml [--graph PATH]` | `graph.graphml` beside the graph | Opens in Gephi, yEd, and other GraphML tools. Communities are written as node attributes; non-scalar dict/list attrs are JSON-serialized and internal `_` markers are stripped. Validate `<graphml` appears and no `.tmp` sibling remains. |
| Portable Cypher for Neo4j | `graphify export neo4j [--graph PATH]` | `cypher.txt` beside the graph | Local file generation only; no service contact. Validate it contains `MERGE`. Import later with a user-approved Neo4j workflow such as `cypher-shell < graphify-out/cypher.txt`. |
| Portable OpenCypher for FalkorDB | `graphify export falkordb [--graph PATH]` | `cypher.txt` beside the graph | Local file generation only. FalkorDB runs one statement at a time via `GRAPH.QUERY`, so prefer live `--push` only when a service is explicitly provided. |

The root `graphify --help` and `graphify export` usage output are the stable help surfaces. Some subcommands also print focused usage when called with missing required operands.

## Database exports and pushes

Keep local Cypher generation separate from live pushes:

1. If the user has no service or credentials, generate `cypher.txt` only:

   ```bash
   graphify export neo4j --graph graphify-out/graph.json
   graphify export falkordb --graph graphify-out/graph.json
   ```

2. If the user explicitly wants a live Neo4j push, confirm the URI, user, and password handling. The CLI requires a password for `--push`; prefer `NEO4J_PASSWORD` to avoid putting the secret on argv.

   ```bash
   export NEO4J_PASSWORD='...'
   graphify export neo4j --graph graphify-out/graph.json --push bolt://localhost:7687 --user neo4j
   ```

   Install variant when the driver is missing:

   ```bash
   uv tool install "graphifyy[neo4j]"
   # or install the neo4j driver in the active Python environment
   ```

3. If the user explicitly wants a live FalkorDB push, confirm host/port, auth requirement, and target graph expectations. FalkorDB auth is optional; use `FALKORDB_PASSWORD` only when the service requires it.

   ```bash
   graphify export falkordb --graph graphify-out/graph.json --push falkordb://localhost:6379
   ```

   Install variant when the SDK is missing:

   ```bash
   uv tool install "graphifyy[falkordb]"
   # or install the falkordb SDK in the active Python environment
   ```

Python API details verified for advanced integrations:

| API | Signature / behavior |
|---|---|
| `graphify.export.to_json` | `(G, communities, output_path, *, force=False, built_at_commit=None, community_labels=None) -> bool` |
| `graphify.export.to_html` | `(G, communities, output_path, community_labels=None, member_counts=None, node_limit=None, learning_overlay=None) -> None` |
| `graphify.export.to_svg` | `(G, communities, output_path, community_labels=None, figsize=(20, 14)) -> None` |
| `graphify.export.to_obsidian` | `(G, communities, output_dir, community_labels=None, cohesion=None) -> int` |
| `graphify.export.to_canvas` | `(G, communities, output_path, community_labels=None, node_filenames=None) -> None` |
| `graphify.export.to_graphml` | `(G, communities, output_path) -> None` |
| `graphify.export.to_cypher` | `(G, output_path) -> None` |
| `graphify.wiki.to_wiki` | `(G, communities, output_dir, community_labels=None, cohesion=None, god_nodes_data=None) -> int` |
| `graphify.export.push_to_neo4j` | Requires the `neo4j` Python driver and returns pushed node/edge counts; MERGE/upsert based. |
| `graphify.export.push_to_falkordb` | Requires the `falkordb` SDK, accepts optional `graph_name`, and returns pushed node/edge counts; MERGE/upsert based. |

Do not invent CLI flags from Python-only parameters. For example, the Python FalkorDB API has `graph_name`, but the verified CLI route is `graphify export falkordb --push URI [--user U] [--password P]`.

## Output validation recipes

```bash
# HTML/callflow/tree
python - <<'PY'
from pathlib import Path
for p in [Path('graphify-out/graph.html'), Path('graphify-out/GRAPH_TREE.html')]:
    if p.exists():
        print(p, p.stat().st_size, 'bytes')
PY

# Wiki
ls graphify-out/wiki/index.md

# Obsidian
find graphify-out/obsidian -maxdepth 1 -type f \( -name '*.md' -o -name 'graph.canvas' \) | sort | head

# GraphML
python - <<'PY'
from pathlib import Path
p = Path('graphify-out/graph.graphml')
print(p.exists(), '<graphml' in p.read_text(encoding='utf-8')[:500] if p.exists() else False)
PY

# Cypher generated locally, not executed
rg '^MERGE|^MATCH' graphify-out/cypher.txt
```

For an end-to-end local smoke that creates its own tiny graph and avoids external services, run `python sub-skills/exports-integrations/scripts/export_tiny_graph.py` from the `graphify` repo-skill root.