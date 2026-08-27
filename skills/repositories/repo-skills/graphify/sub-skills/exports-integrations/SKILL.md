---
name: exports-integrations
description: "Export, merge, and integrate Graphify graph outputs safely without
  requiring live external services by default."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Graphify exports and integrations

Use this sub-skill when the user already has, or is planning around, Graphify graph artifacts and asks to export, merge, publish, compare, or integrate them. It covers local HTML/tree/callflow/wiki/Obsidian/SVG/GraphML/Cypher outputs, multi-repo graph merges, Git merge-driver behavior, GitHub clone/PR helpers, affected/god-node commands, and optional Neo4j/FalkorDB pushes.

Do **not** use this sub-skill as the primary route for building the first graph, interpreting graph query answers, or installing assistant hooks. Route those tasks instead:

- Build/update/extraction prerequisites: [graph-building](../graph-building/SKILL.md)
- Query/path/explain interpretation after an export: [query-navigation](../query-navigation/SKILL.md)
- Assistant skill installation and hook setup: [agent-integration](../agent-integration/SKILL.md)
- Source-format or extractor failures behind bad exports: [extractor-troubleshooting](../extractor-troubleshooting/SKILL.md)
- Root router and package overview: [root graphify skill](../../SKILL.md)

## Start here

1. Confirm the graph path. Most commands default to `graphify-out/graph.json`; pass `--graph PATH` when using a merged graph or a non-default output directory.
2. If `graph.json` is missing or stale, stop this route and use [graph-building](../graph-building/SKILL.md) first. Do not invent export instructions from source files alone.
3. Prefer local, portable exports first. A database push is a side-effecting integration and requires explicit service URI, credential, and target confirmation.
4. Keep secrets out of shell history. For Neo4j/FalkorDB CLI pushes, prefer `NEO4J_PASSWORD` or `FALKORDB_PASSWORD` over `--password`.
5. Validate every produced artifact before handing it to the user: check existence, non-empty size, expected extension, and a lightweight format-specific signal.

## Route map

| User asks for | Use | Key commands |
|---|---|---|
| Browser visualization, markdown wiki, vault, SVG, GraphML, Cypher, tree, or call-flow HTML | [Export reference](references/export-reference.md) | `graphify export html`, `graphify export wiki`, `graphify export obsidian`, `graphify tree`, `graphify export callflow-html`, `graphify export graphml`, `graphify export neo4j` |
| Neo4j/FalkorDB integration | [Export reference: database section](references/export-reference.md#database-exports-and-pushes) | Generate `cypher.txt` by default; push only with `--push` and explicit service details |
| Two or more local service graphs, cloned GitHub repos, or a global graph | [Multi-repo and PR workflows](references/multi-repo-and-prs.md) | `graphify merge-graphs`, `graphify clone`, `graphify global add/list/path` |
| Git merge conflict in committed `graph.json` | [Multi-repo and PR workflows](references/multi-repo-and-prs.md#git-merge-driver-for-graphjson) | `graphify merge-driver <base> <current> <other>` |
| PR dashboard, impact, conflicts, or triage | [Multi-repo and PR workflows](references/multi-repo-and-prs.md#pull-request-and-impact-helpers) | `graphify prs`, `graphify prs 42`, `graphify prs --conflicts`, `graphify prs --triage` |
| Blast-radius or architectural hubs | [Multi-repo and PR workflows](references/multi-repo-and-prs.md#affected-and-god-node-helpers) | `graphify affected "X"`, `graphify god-nodes --json` |
| Export failed, output missing, graph too large, optional dependency missing, DB unavailable, merge collision, tree root mismatch | [Troubleshooting](references/troubleshooting.md) | Follow the symptom-specific recovery table |
| Need a safe local smoke check before touching user artifacts | [Bundled export smoke script](scripts/export_tiny_graph.py) | From the `graphify` repo-skill root: `python sub-skills/exports-integrations/scripts/export_tiny_graph.py` |

## Safe default policy

- Local exports (`html`, `wiki`, `obsidian`, `graphml`, local `cypher.txt`, `tree`, `callflow-html`) are safe to run in a scratch output directory or on a user-confirmed graph output directory.
- `svg` is local but needs the optional `svg` extra because it imports matplotlib.
- `neo4j --push` and `falkordb --push` are **not** default checks. They contact a live service and mutate a graph database using MERGE/upsert statements.
- `prs` commands require GitHub CLI access and may make network calls. `prs --triage` also needs a configured LLM backend.
- `graphify clone` performs Git network I/O and writes to the Graphify repo cache or the supplied `--out` directory.

## Validation checklist

After running an export or merge, verify the output that matters to the user:

- HTML/tree/callflow: file exists, size is non-zero, and the command printed a written/open message.
- Wiki: `wiki/index.md` exists and links to community or god-node pages.
- Obsidian: target vault directory has Markdown notes plus `graph.canvas` when using the CLI route.
- GraphML: file contains `<graphml` and opens with a GraphML consumer if the user needs visual validation.
- Cypher: `cypher.txt` contains `MERGE` statements; do not execute it unless the user chooses a database target.
- Merged graph: node ids are prefixed with repo tags such as `api::handler`, and node attributes include `repo`/`local_id` for origin filtering.

For a reproducible smoke check that avoids external services, run the bundled [export_tiny_graph.py](scripts/export_tiny_graph.py) helper. From the `graphify` repo-skill root, use `python sub-skills/exports-integrations/scripts/export_tiny_graph.py`.