# Graphify Cross-Cutting Troubleshooting

Use this page when the failure is not yet tied to one sub-skill. Once the surface is clear, follow the linked workflow-specific troubleshooting page.

## Triage route

| Symptom family | Go to |
|---|---|
| Build/update/watch/add, missing files, no provider key, stale graph, cache/manifest, `GRAPH_REPORT.md` missing | [graph-building troubleshooting](../sub-skills/graph-building/references/troubleshooting.md) |
| Query/path/explain/affected/god-nodes, missing/corrupt/oversized graph, no match/path, ambiguous node, MCP serving | [query-navigation troubleshooting](../sub-skills/query-navigation/references/troubleshooting.md) |
| Assistant skill install/uninstall, platform artifacts, hooks, strict mode, PATH in hooks, accidental HOME/project mutation | [agent-integration troubleshooting](../sub-skills/agent-integration/references/troubleshooting.md) |
| Exports, wiki/Obsidian/GraphML/Cypher, database push, merge-graphs, PR helpers | [exports-integrations troubleshooting](../sub-skills/exports-integrations/references/troubleshooting.md) |
| Unsupported extensions, optional parser extras, zero-node extraction, duplicate/legacy IDs, resolver or edge-direction source defects | [extractor-troubleshooting troubleshooting](../sub-skills/extractor-troubleshooting/references/troubleshooting.md) |

## Package and command identity

| Symptom | Likely cause | Recovery |
|---|---|---|
| `graphify: command not found` | Tool executable directory not on `PATH`, or package installed in another environment. | Try `python -m graphify --help`. For uv tool installs run `uv tool update-shell`; for pipx run `pipx ensurepath`. |
| `uvx graphify ...` fails with no versions | The PyPI package is `graphifyy`, not `graphify`. | Use `uvx --from graphifyy graphify ...`. |
| `ModuleNotFoundError: No module named 'graphify'` | Python executing the command is not the one where `graphifyy` is installed. | Install into the intended interpreter or use an isolated tool manager (`uv tool install graphifyy`, `pipx install graphifyy`). |
| `pip show graphify` finds an unrelated package | Wrong package name. | Use `pip show graphifyy` and reinstall the official package. |
| CLI works in shell but Git hook/GUI/assistant cannot find it | Hook or GUI environment has a different PATH. | Rerun `graphify hook install` after installing/upgrading; hooks embed the current interpreter path. |

Run the root preflight:

```bash
python scripts/check_graphify_install.py
python scripts/check_graphify_install.py --json
```

## Missing or stale graph

- If `graphify-out/graph.json` does not exist, build one through [graph-building](../sub-skills/graph-building/SKILL.md).
- If code changed after graph creation, prefer `graphify update .`.
- If docs/images/PDFs/media changed, a semantic extraction route is required; code-only update will not semantically process them.
- If only `GRAPH_REPORT.md` or `graph.html` is missing while `graph.json` exists, run `graphify cluster-only . --no-viz` or the appropriate export route.
- Do not purge `graphify-out/` just because files are dirty or stale. Dirty graph files after hooks/update are expected.

## Optional dependencies and credentials

Install only the smallest extra set needed for the selected workflow:

| Need | Extra / boundary |
|---|---|
| Provider-backed semantic docs/media extraction | One provider extra such as `gemini`, `openai`, `anthropic`, `kimi`, `ollama`, or `bedrock` plus credentials/service. |
| PDF/Office/Google/video inputs | `pdf`, `office`, `google`, or `video`; may need network/auth/model cache. |
| Watch mode | `watch`. |
| MCP serving | `mcp`; use localhost by default and require an API key before external HTTP binding. |
| Neo4j/FalkorDB/PostgreSQL | `neo4j`, `falkordb`, `postgres`; live pushes/introspection require explicit service and credentials. |
| SVG export | `svg`. |
| Optional parser formats | `sql`, `terraform`, `pascal`, or `dm` depending on file type. |

Do not install `graphifyy[all]` unless the user explicitly asks for broad optional coverage and accepts dependency cost. Do not make provider/API, database, GitHub, Google Workspace, media download, or external HTTP operations default verification steps.

## Safe answer and mutation rules

- If a fresh graph exists and the user asks a codebase/architecture question, query it first with [query-navigation](../sub-skills/query-navigation/SKILL.md).
- If a graph command fails due to missing/corrupt artifacts, route to graph-building before reading raw source.
- Ask before mutating real assistant config, a user-global HOME, project instruction files, Git hooks, live databases, cloud providers, or exposed HTTP services.
- Ask before using `--force`, `--allow-partial`, deleting `graphify-out/`, or purging installed artifacts.
- Prefer portable/local artifacts (`graph.json`, HTML/wiki/GraphML/Cypher files) before live pushes or networked services.

## Security and privacy reminders

- Graph paths passed to serving/query tools should be `.json` graph files under the intended `graphify-out/` directory.
- Graph artifacts can contain proprietary labels, source paths, and query-memory text. Treat them as sensitive project data.
- Use environment variables rather than argv for secrets such as database passwords or API keys.
- `graphify add` fetches user-provided URLs only after URL validation; do not continue to update if the fetch failed.
- Graphify AST extraction parses source; it does not execute source files. The bundled diagnostic helpers also avoid executing user code.
