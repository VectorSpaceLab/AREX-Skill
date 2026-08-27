# Meshroom Cross-Cutting Troubleshooting

## Import or Install Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'meshroom'` outside the checkout | package not installed, editable install did not expose package, or command is running under the wrong Python | Run `python -m pip show Meshroom`, then `python -c "import meshroom"` from a neutral directory. For source checkouts, reinstall with `python -m pip install -e . --no-build-isolation --config-settings editable_mode=compat`. |
| Editable install fails while importing `cx_Freeze` | setup metadata imports packaging dependency before isolated build env has it | Install `dev_requirements.txt`, then retry editable install with `--no-build-isolation`. |
| `pip check` reports broken PySide6/shiboken/requests/markdown requirements | mixed environments or partial dependency upgrade | Recreate an isolated Python 3.9-3.11 env, reinstall `requirements.txt`, and avoid installing broad unrelated extras. |
| `meshroom.__version__` imports but CLI script cannot import Meshroom | CLI runs under a different Python or `PYTHONPATH` is missing in source checkout | Run the CLI as `python bin/<script>` from an environment where `import meshroom` works, or use `PYTHONPATH=$PWD` for source-only runs. |

## Plugin and Template Discovery Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Custom nodes not listed | plugin root does not contain `meshroom/`, package has no `__init__.py`, or path is on the wrong env var | Read `sub-skills/plugin-system/SKILL.md`; run its bundled plugin-folder checker; set `MESHROOM_PLUGINS_PATH` to the plugin root, not directly to a node package unless using `MESHROOM_NODES_PATH`. |
| Pipeline template is missing | `.mg` file is not inside a loaded plugin/template folder or `initPipelines()` ran before plugin load | Ensure the template path is on `MESHROOM_PIPELINE_TEMPLATES_PATH` or inside a plugin's `meshroom/` folder; initialize plugins before inspecting plugin-owned templates. |
| Node provider has `DESC_ERROR` | default value does not match attribute descriptor type or descriptor import failed | Use `node-descriptors/scripts/validate_node_descriptor.py` and inspect the formatted errors. Fix descriptor defaults before registering the node. |
| Duplicate node name warning | two loaded plugin packages expose classes with the same descriptor class name | Rename one node descriptor class or control plugin search path order. Meshroom will not register the duplicate provider. |

## CLI and Graph Runtime Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `meshroom_batch requires a pipeline graph with at least one output node` | `--output` was supplied but template has no `desc.OutputNode` instances | Use a template with output nodes retained, add an output node, or omit `--output`. |
| `Unknown output node` or `Unknown output node type` | `--output` target uses the wrong node instance/type name | Inspect the graph with `meshroom_info nodeinfo` or load the `.mg` to find node names/types, then use `NodeInstance=path` or `NodeType:attribute=value`. |
| `GraphCompatibilityError`, `CompatibilityNode`, or unknown node type | saved graph references node descriptors not currently loaded or incompatible major versions | Load the plugin that provided the node; inspect compatibility details; use graph upgrade only when the current descriptor can safely accept saved attributes. |
| Warning that nodes are already `RUNNING` or `SUBMITTED` | status files indicate external/local compute in progress | Use `meshroom_status`, check cache/status files, then choose `--forceStatus` only when you know no valid job is still running. |
| Stale or wrong cache folder | scene saved with explicit cache dir or moved relative to cache | Read `core-graph-engine` cache notes; use `Graph.setExplicitCacheDir()` or CLI `--overrideCacheDir` when saving a new scene. |

## UI/QML Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `QQmlApplicationEngine failed to load component` with little detail | QML warnings are suppressed by default | Set `MESHROOM_OUTPUT_QML_WARNINGS=1` and rerun the UI import/launch to expose the real QML error. |
| QtQuick Scene3D plugin missing | PySide6 wheel/platform package missing Qt3D/Scene3D runtime | Follow the PySide6 warning in setup docs; install the missing platform package or use a compatible PySide6/Qt runtime. |
| UI starts only headless/import checks pass, full window does not open | display server, OpenGL, native drivers, or QML platform unavailable | Do not treat import success as full GUI verification. Run with a real display/OpenGL stack or use offscreen-safe parser/import checks only. |

## LocalFarm Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `meshroom_localfarm status` cannot connect | backend daemon not started or farm root points elsewhere | Start with a known `--root`, check `backend.port`, `farm.pid`, and `backend.log` under that farm root. |
| LocalFarm unsupported on Windows | backend daemonization currently relies on Unix `fork` behavior | Treat LocalFarm as Unix-only unless code changed; use another submitter on Windows. |
| Submitted tasks never complete | command wrapper cannot find `meshroom_compute`, plugin env not forwarded, or stale status files | Read `local-farm-submission` references; confirm job env contains plugin paths; inspect per-task logs under `jobs/<jid>/tasks/`. |

## Optional External Dependencies

- Missing AliceVision binaries are not a Meshroom Python framework failure. They block AliceVision plugin compute workflows, not graph/descriptor/plugin/UI framework inspection.
- Missing QtAliceVision affects visualization capabilities, not all graph or CLI workflows.
- GPU visibility is not required for core Meshroom operation. Only treat CUDA/ROCm/MPS as required when the selected external plugin workflow explicitly needs it.
