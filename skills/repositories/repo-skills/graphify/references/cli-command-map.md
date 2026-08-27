# Graphify CLI Command Map

Use this map to route commands to the nearest sub-skill. For details, read the linked sub-skill reference rather than expanding every flag here.

## Package and invocation

```bash
# Package name is graphifyy.
uv tool install graphifyy
pipx install graphifyy
python -m pip install graphifyy

# CLI forms.
graphify --help
python -m graphify --help
uvx --from graphifyy graphify --help
```

## Build and update commands

Owner: [graph-building](../sub-skills/graph-building/SKILL.md)

| Command | Use |
|---|---|
| `graphify extract <path>` or `graphify <path>` | Build graph artifacts from a local folder. |
| `graphify extract <path> --code-only` | Local AST-only code graph; no provider key. |
| `graphify extract <path> --backend <name>` | Provider-backed docs/papers/images semantic extraction. |
| `graphify update [path]` | Incrementally update code/AST graph from an existing graph. |
| `graphify cluster-only <path>` | Re-run community/report/HTML generation from an existing graph. |
| `graphify label <path>` | Regenerate or fill community labels. |
| `graphify add <url>` | Fetch URL material into `./raw` or `--dir`, then update/extract. |
| `graphify watch <path>` | Rebuild on code changes and flag semantic changes. |
| `graphify check-update <path>` | Check watch-mode `needs_update` status. |

## Query and navigation commands

Owner: [query-navigation](../sub-skills/query-navigation/SKILL.md)

| Command | Use |
|---|---|
| `graphify query "QUESTION"` | Breadth-first graph context for a question. |
| `graphify query "QUESTION" --dfs` | Depth-first chain exploration. |
| `graphify path "A" "B"` | Directed shortest path between concepts; use `--undirected` only for connectivity. |
| `graphify explain "X"` | One node, source, degree, and direct neighbors. |
| `graphify affected "X"` | Reverse impact/blast-radius traversal. |
| `graphify god-nodes` / `god_nodes` | High-degree architectural hubs. |
| `graphify save-result ...` | Persist useful/dead-end/corrected graph answer memory. |
| `graphify reflect --if-stale` | Build deterministic lesson summaries/overlays. |
| `graphify-mcp` / `python -m graphify.serve` | Serve graph tools over MCP stdio or HTTP. |

## Assistant integration commands

Owner: [agent-integration](../sub-skills/agent-integration/SKILL.md)

| Command | Use |
|---|---|
| `graphify install` | Default Claude/Windows Graphify assistant skill install. |
| `graphify install --platform <platform>` | User/global skill install for a named platform. |
| `graphify install --project --platform <platform>` | Project-scoped, commit-able install when supported. |
| `graphify <platform> install` | Platform-specific always-on/hook command for supported platforms. |
| `graphify uninstall` | Remove detected Graphify integrations; `--purge` also removes graph outputs. |
| `graphify uninstall --project --platform <platform>` | Remove only that project/platform scope. |
| `graphify hook install/status/uninstall` | Git hooks and graph merge-driver, separate from assistant hooks. |
| `graphify hook-check` / `hook-guard` | Internal hook helpers; do not call manually unless debugging hooks. |

## Export, merge, and integration commands

Owner: [exports-integrations](../sub-skills/exports-integrations/SKILL.md)

| Command | Use |
|---|---|
| `graphify export html` | Browser graph HTML. |
| `graphify export callflow-html` | Mermaid callflow/architecture HTML. |
| `graphify tree` | D3 collapsible source tree HTML. |
| `graphify export wiki` | Agent-crawlable Markdown wiki. |
| `graphify export obsidian` | Obsidian vault and Canvas. |
| `graphify export svg` | SVG visualization; optional `svg` extra. |
| `graphify export graphml` | GraphML for Gephi/yEd. |
| `graphify export neo4j` / `falkordb` | Local Cypher by default; live `--push` only with explicit service details. |
| `graphify merge-graphs <g1> <g2> ...` | Merge per-repo/per-service graphs. |
| `graphify merge-driver <base> <current> <other>` | Git merge-driver for `graph.json`. |
| `graphify clone <github-url>` | Clone GitHub repo into Graphify's repo cache. |
| `graphify prs ...` | GitHub PR dashboard/impact/triage; needs `gh` and sometimes a provider. |

## Provider/config/diagnostic commands

| Command | Owner | Use |
|---|---|---|
| `graphify provider add/list/show/remove` | [graph-building](../sub-skills/graph-building/SKILL.md) | Configure custom provider backends for semantic extraction/labeling. |
| `graphify diagnose multigraph ...` | [extractor-troubleshooting](../sub-skills/extractor-troubleshooting/SKILL.md) | Report same-endpoint edge-collapse risk and graph direction diagnostics. |
| `graphify benchmark` | [exports-integrations](../sub-skills/exports-integrations/SKILL.md) for report context only | Token-reduction benchmark; skip by default unless the user asks for it. |

## Safety reminders

- Commands that read `graph.json` accept `--graph PATH`; pass it explicitly for non-default graph locations.
- Commands that mutate user/project assistant config or live services need explicit user intent.
- Commands involving provider APIs, Google Workspace, media URLs, GitHub PRs, or database pushes may require credentials/network and are not safe default smoke checks.
