---
name: meshroom
description: "Guides Meshroom graph-engine, node-descriptor, plugin, CLI
  pipeline, PySide/QML UI, and local-farm submission workflows for agents
  working with Meshroom projects or the Meshroom Python package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Meshroom

Use this skill when a task involves **Meshroom**, the AliceVision node-based Python/QML framework for building, editing, saving, computing, and submitting data-processing graphs. Meshroom itself is the graph/UI/CLI/plugin framework; AliceVision photogrammetry algorithms and binaries are external plugins/dependencies.

## First Checks

1. Read [Repository provenance](references/repo-provenance.md) when freshness matters. Refresh this skill if the current Meshroom checkout has a different commit, package version, or changed public entry points.
2. Read [Setup and environment](references/setup-and-environment.md) before diagnosing installs, imports, Python versions, optional PySide/QML issues, or external AliceVision dependencies.
3. Run [scripts/check_meshroom_runtime.py](scripts/check_meshroom_runtime.py) for a safe import/version/CLI smoke check when the runtime may be broken.
4. Use [Troubleshooting](references/troubleshooting.md) for cross-cutting import, plugin, CLI, UI, cache, and optional-dependency failures.

## Route by Task

| User task or signal | Read |
| --- | --- |
| Programmatically create, connect, save, load, import, upgrade, or execute `.mg` graphs; diagnose `CompatibilityNode`, cache, status, DFS, or invalidation behavior | [core-graph-engine](sub-skills/core-graph-engine/SKILL.md) |
| Write or debug a Meshroom node descriptor, attribute schema, `CommandLineNode`, `InputNode`, `OutputNode`, dynamic size, or built-in general utility node | [node-descriptors](sub-skills/node-descriptors/SKILL.md) |
| Load custom plugins/templates/submitters, configure `MESHROOM_*` paths, inspect plugin `config.json`, or diagnose duplicate/invalid node providers | [plugin-system](sub-skills/plugin-system/SKILL.md) |
| Use `meshroom_batch`, `meshroom_compute`, `meshroom_info`, `meshroom_submit`, `meshroom_status`, `meshroom_statistics`, `meshroom_newNodeType`, or scene-parameter helper workflows | [cli-pipeline-execution](sub-skills/cli-pipeline-execution/SKILL.md) |
| Launch or debug the PySide6/QML application, `MeshroomApp`, `Scene`, `UIGraph`, QML imports, viewers, or UI context properties | [ui-integration](sub-skills/ui-integration/SKILL.md) |
| Start/stop/query Meshroom LocalFarm, inspect farm jobs/tasks, debug `LocalFarmSubmitter`, or reason about chunk task expansion | [local-farm-submission](sub-skills/local-farm-submission/SKILL.md) |

## Minimal Runtime Pattern

For source checkouts, keep commands explicit instead of relying on shell activation:

```bash
python -m pip install -r requirements.txt
python -m pip install -e . --no-build-isolation --config-settings editable_mode=compat
python -c "import meshroom; print(meshroom.__version__)"
```

Use `PYTHONPATH=$PWD python meshroom/ui` or `./start.sh` for source UI launch when a display/QML runtime is available. Use package/module imports for library workflows and the `bin/` entry points for CLI workflows.

## Important Boundaries

- Meshroom graph, node descriptor, plugin, submitter, and UI APIs are in this repo.
- AliceVision executable nodes, photogrammetry algorithms, sensor databases, voctrees, and reconstruction binaries are external. This skill can help wire their plugin paths and environment variables, but it does not document AliceVision C++ algorithm internals.
- Full UI launch can require display/OpenGL/QML platform support. A Python import check is not the same as a displayed application.
- LocalFarm is Unix-oriented because the backend daemon uses process forking; treat Windows farm execution as unsupported unless the codebase changes.

## Development/Verification Rules

- Target Python 3.9-3.11 for code reachable from core and CLI entry points.
- Use camelCase names in Meshroom Python/QML code to match the project style.
- For core changes, add focused unit tests and run targeted `pytest` cases. Use `flake8 . --max-line-length=127` for lint when available.
- Do not run expensive photogrammetry pipelines or download external datasets merely to verify framework-level changes. Prefer focused unit tests, CLI help/version checks, and tiny graph/node fixtures.

## Useful Public Entry Points

- Package: `meshroom`, `meshroom.core`, `meshroom.core.desc`, `meshroom.env`, `meshroom.ui.app`.
- CLIs: `meshroom_batch`, `meshroom_compute`, `meshroom_info`, `meshroom_submit`, `meshroom_status`, `meshroom_statistics`, `meshroom_createChunks`, `meshroom_newNodeType`, `meshroom_localfarm`.
- Built-in node/plugin roots: `meshroom/nodes/general`, `meshroom/submitters/localFarm`, `localfarm`.

## If Unsure

- Need dataflow semantics? Start at [core graph workflows](sub-skills/core-graph-engine/references/graph-workflows.md).
- Need node schema syntax? Start at [descriptor API reference](sub-skills/node-descriptors/references/descriptor-api-reference.md).
- Need path/env discovery? Start at [plugin loading reference](sub-skills/plugin-system/references/plugin-loading-reference.md).
- Need command flags? Start at [CLI reference](sub-skills/cli-pipeline-execution/references/cli-reference.md).
- Need UI startup? Start at [UI reference](sub-skills/ui-integration/references/ui-reference.md).
- Need farm jobs/tasks? Start at [LocalFarm workflows](sub-skills/local-farm-submission/references/local-farm-workflows.md).
