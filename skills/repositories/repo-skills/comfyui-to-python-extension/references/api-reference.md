# API Reference

This reference collects the public Python surface that the repo skill should mention.

## Public entry points

| Symbol | Signature | Purpose |
| --- | --- | --- |
| `comfyui_to_python.ComfyUItoPython` | `ComfyUItoPython(workflow: str = '', frontend_workflow: str \| dict \| None = None, input_file: str = '', output_file: str \| TextIO = '', queue_size: int = 1, node_class_mappings: dict \| None = None, needs_init_custom_nodes: bool = False)` | Immediate export facade used by the package and extension route. Instantiating it runs the export. |
| `comfyui_to_python.run` | `run(input_file: str = 'workflow_api.json', output_file: str = 'workflow_api.py', queue_size: int = 10) -> None` | Convenience wrapper used by the CLI entry point. |
| `comfyui_to_python.app.ExportApplication` | `ExportApplication(workflow='', frontend_workflow=None, input_file='', output_file='', queue_size=1, node_class_mappings=None, needs_init_custom_nodes=False, node_mapping_loader=None, custom_node_importer=None)` | High-level export orchestrator. |
| `comfyui_to_python.cli.build_argument_parser` | `() -> ArgumentParser` | Builds the CLI parser and default flags. |
| `comfyui_to_python.cli.main` | `() -> None` | Parses args and runs the exporter. |
| `comfyui_to_python.generator.planner.WorkflowPlanner.build_plan` | `build_plan(load_order, workflow_data, metadata_workflow_data=None, queue_size=10) -> GenerationPlan` | Turns ordered workflow nodes into a renderable plan. |
| `comfyui_to_python.generator.render.WorkflowRenderer.render` | `render(plan) -> str` | Renders the plan into formatted standalone Python. |
| `comfyui_to_python.load_order.LoadOrderDeterminer.determine_load_order` | `() -> list[tuple[str, Dict, bool]]` | Produces loader-first execution order. |
| `comfyui_to_python.workflow_loader.load_workflow_data` | `load_workflow_data(workflow: str, input_file: str)` | Loads workflow JSON from inline text or a file. |
| `comfyui_to_python.workflow_loader.load_frontend_workflow_data` | `load_frontend_workflow_data(frontend_workflow: str | dict | None)` | Loads optional frontend workflow metadata. |
| `comfyui_to_python.io.load_json_input` | `load_json_input(file_path: str | TextIO, encoding: str = 'utf-8') -> dict` | Reads workflow JSON from a path or file-like object. |
| `comfyui_to_python.io.write_python_output` | `write_python_output(file_path: str | TextIO, code: str) -> None` | Writes generated Python to a path or file-like object. |
| `comfyui_to_python.node_runtime.get_comfyui_path` | `() -> str` | Returns `COMFYUI_PATH` or searches parent directories for a `ComfyUI` folder. |
| `comfyui_to_python.node_runtime.add_comfyui_directory_to_sys_path` | `() -> None` | Puts the ComfyUI checkout on `sys.path`. |
| `comfyui_to_python.node_runtime.add_extra_model_paths` | `() -> None` | Loads `extra_model_paths.yaml` when present. |
| `comfyui_to_python.node_runtime.bootstrap_comfyui_runtime` | `() -> None` | Mirrors ComfyUI startup steps before `torch` import in generated scripts. |
| `comfyui_to_python.node_runtime.cleanup_comfyui_runtime` | `cleanup_comfyui_runtime(unload_models: bool | None = None) -> None` | Best-effort teardown and optional model unload. |
| `comfyui_to_python.node_runtime.import_custom_nodes` | `() -> None` | Initializes ComfyUI custom nodes before export when needed. |
| `comfyui_to_python.node_runtime.get_node_class_mappings` | `() -> dict` | Loads `NODE_CLASS_MAPPINGS` from ComfyUI on demand. |
| `comfyui_to_python.node_runtime.get_value_at_index` | `get_value_at_index(obj: Sequence | Mapping, index: int) -> Any` | Extracts the indexed output from a node result. |

## Compatibility module

- `comfyui_to_python_utils.py` re-exports a subset of the runtime helpers for compatibility with older entry points and test harnesses.

## What to remember

- `ComfyUItoPython(...)` is an immediate-action facade, not a lazy object.
- `run(...)` is the user-facing CLI helper and defaults to `workflow_api.json` and `workflow_api.py`.
- Generated scripts are not just code dumps; they include bootstrap, cleanup, and workflow metadata helpers.
