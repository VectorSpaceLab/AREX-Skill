---
name: graphify
description: "Use Graphify to build, query, export, and integrate code/document
  knowledge graphs for AI coding assistants and MCP workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Graphify

Use this repo skill when a user names Graphify or `graphifyy`, works with `graphify-out/`, wants a code/document knowledge graph, asks how to query `graph.json`, installs Graphify into an AI coding assistant, or needs Graphify exports, hooks, MCP serving, or extractor troubleshooting.

Graphify's public distribution is `graphifyy`; the import package and CLI are `graphify`. The normal graph output directory is `graphify-out/` with `graph.json`, `GRAPH_REPORT.md`, and optional `graph.html`, wiki, export, cache, manifest, and lesson artifacts.

## First checks

```bash
# Public install identity.
python -m pip show graphifyy || true
python - <<'PY'
import graphify
print('graphify import ok')
PY

# CLI check. Use python -m graphify when the console command is not on PATH.
graphify --help || python -m graphify --help
```

For a self-contained preflight that does not touch a repository, run [scripts/check_graphify_install.py](scripts/check_graphify_install.py). Read [references/package-overview.md](references/package-overview.md) for package concepts, graph artifacts, and optional surfaces.

## Route map

| User intent | Read |
|---|---|
| Build, update, watch, or validate `graphify-out/` from local code/docs/media; choose `--code-only` vs semantic extraction; handle `.graphifyignore`, cache, manifest, `cluster-only`, or `add` | [graph-building](sub-skills/graph-building/SKILL.md) |
| Answer from an existing graph with `query`, `path`, `explain`, `affected`, `god-nodes`, work-memory lessons, or MCP stdio/HTTP serving | [query-navigation](sub-skills/query-navigation/SKILL.md) |
| Install/uninstall Graphify assistant skills, always-on guidance, platform hooks, Git hooks, strict mode, or inspect platform artifacts safely | [agent-integration](sub-skills/agent-integration/SKILL.md) |
| Export graph artifacts to HTML/wiki/Obsidian/SVG/GraphML/Cypher, merge multiple graphs, clone GitHub repos, use PR helpers, or push to Neo4j/FalkorDB only after approval | [exports-integrations](sub-skills/exports-integrations/SKILL.md) |
| Diagnose ignored file types, missing optional parsers, AST extractor/resolver failures, node-ID/source-file normalization, zero-node sources, or maintainer extractor changes | [extractor-troubleshooting](sub-skills/extractor-troubleshooting/SKILL.md) |

If a request spans several routes, preserve the natural order: build/update the graph, then query it, then export or install always-on guidance as needed.

## Cross-cutting references

- [references/cli-command-map.md](references/cli-command-map.md): command families and their owning sub-skills.
- [references/troubleshooting.md](references/troubleshooting.md): package/PATH, missing graph, optional extras, no-key, stale graph, service, and safety triage.
- [references/repo-provenance.md](references/repo-provenance.md): source snapshot and refresh baseline for this generated skill.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured router metadata for a later managed import.

## Operating defaults

- Prefer `graphify query`, `graphify path`, or `graphify explain` before grepping raw files when a fresh `graphify-out/graph.json` exists.
- Use `graphify extract <path> --code-only` for local code graphs that should not require provider keys or semantic extraction.
- Use explicit optional extras only when the selected workflow needs them; do not install `graphifyy[all]` by default.
- Treat database pushes, provider API calls, Google Workspace auth, video/model downloads, GitHub PR triage, and HTTP MCP exposure beyond localhost as side-effecting or credentialed operations that need explicit user approval.
- Do not delete, purge, or force-overwrite `graphify-out/` artifacts just because they are dirty or stale. Prefer update/rebuild routes and explain the overwrite risk first.
- Do not rely on the original Graphify source checkout. This runtime skill bundles the needed references and scripts.

## Staleness check

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a newer Graphify checkout. If the package version, public CLI entry points, optional extras, or source evidence paths changed, refresh this repo skill before making detailed claims.
