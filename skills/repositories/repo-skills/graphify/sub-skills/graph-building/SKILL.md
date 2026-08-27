---
name: graph-building
description: "Builds and updates Graphify graph artifacts from local files,
  including code-only extraction, semantic extraction decisions,
  update/cluster/add/watch flows, and graph validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Graphify graph-building

Use this sub-skill when the user needs to create, refresh, or validate `graphify-out/` artifacts for a local corpus: code-only extraction, semantic extraction setup, incremental updates, cluster-only relabeling, URL/media additions, watch-mode rebuilds, ignore/exclude handling, manifest/cache behavior, and safe build smoke checks.

## Route first

- Start here for: `graphify extract`, `/graphify .`, `--code-only`, `--no-cluster`, `--update`, `graphify update`, `cluster-only`, `label`, `add`, `watch`, `.graphifyignore`, `--exclude`, `manifest.json`, `cache/`, missing graph artifacts, or graph-build validation.
- Read the root router at [../../SKILL.md](../../SKILL.md) when the user asks a broad Graphify question or you need install/package orientation shared across sub-skills.
- After a graph exists, route query/path/explain/affected/MCP serving to [../query-navigation/SKILL.md](../query-navigation/SKILL.md).
- Route HTML/wiki/Obsidian/SVG/GraphML/Cypher/database exports, graph merging, and PR/global graph workflows to [../exports-integrations/SKILL.md](../exports-integrations/SKILL.md).
- Route assistant skill installation, hooks, always-on files, and platform-specific integration to [../agent-integration/SKILL.md](../agent-integration/SKILL.md).
- Route source-format matrices, parser gaps, language extractor debugging, and maintainer extractor changes to [../extractor-troubleshooting/SKILL.md](../extractor-troubleshooting/SKILL.md), unless all you need is an ordinary build command.

## Minimum working flow

1. Confirm package access without naming any private environment:
   ```bash
   python -m graphify --help
   # or, if installed as a tool:
   graphify --help
   ```
   Install the public package as `graphifyy`; the import package and CLI command are `graphify`.
2. Choose the build mode from [references/workflows.md](references/workflows.md):
   - Code-only or no provider key: `graphify extract <path> --code-only`, then `graphify cluster-only <path>` when you need `GRAPH_REPORT.md` and `graph.html`.
   - Mixed docs/media with a configured provider: `graphify extract <path> --backend <provider>`, then `graphify cluster-only <path>`.
   - Existing graph with code changes only: `graphify update <path>`; add `--no-cluster` for a raw graph-only update.
3. Validate artifacts with [scripts/build_tiny_graph.py](scripts/build_tiny_graph.py) or the artifact checklist in [references/workflows.md](references/workflows.md#validate-the-resulting-artifacts).
4. If a command fails, check [references/troubleshooting.md](references/troubleshooting.md) before retrying or forcing an overwrite.

## What to read

- [references/workflows.md](references/workflows.md): command recipes, decision tree, graph artifact validation, update/add/watch/cluster-only flows.
- [references/api-reference.md](references/api-reference.md): verified CLI/API entry points, return shapes, graph schema, confidence labels, cache and manifest contracts.
- [references/optional-dependencies.md](references/optional-dependencies.md): extras for semantic providers, PDF/Office/Google/media inputs, watch mode, language formats, and what remains optional/unverified by default.
- [references/troubleshooting.md](references/troubleshooting.md): install/import, no-key, no files, optional dependency, stale graph, shrink guard, manifest/cache, invalid graph, and watch/add failures.
- [scripts/build_tiny_graph.py](scripts/build_tiny_graph.py): safe local smoke helper that creates a temporary one-file corpus and runs a code-only extraction without network, credentials, or writes to the user's repo.

## Guardrails

- Do not ask for an API key when the correct answer is code-only extraction. A code-only corpus runs locally with AST extraction and no LLM.
- Do not overwrite a smaller/partial graph over a larger good graph unless the user explicitly accepts `--force` or `--allow-partial` after seeing the risk.
- Do not tell future agents to open the original Graphify checkout, source examples, or source docs. This sub-skill and its bundled references are the runtime source of truth.
- Do not route query answering, serving, exports, assistant hooks, or extractor-maintainer work through this sub-skill except as explicit cross-links.
