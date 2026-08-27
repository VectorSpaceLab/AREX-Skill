# Generated Script Runtime

The exporter does more than stringify a workflow. It renders a standalone runner with bootstrap, cleanup, and workflow metadata helpers.

## Runtime shape

1. Import helpers and ComfyUI runtime utilities.
2. Build the workflow literal with `build_workflow()`.
3. Build optional frontend metadata with `build_extra_pnginfo()`.
4. Deep-copy the workflow into `prompt` for mutation during execution.
5. Call `bootstrap_comfyui_runtime()` before importing `torch`.
6. Load `extra_model_paths.yaml` and custom nodes when needed.
7. Enter `torch.inference_mode()` and loop for `queue_size` iterations.
8. Run `cleanup_comfyui_runtime(unload_models=unload_models)` in a `finally` block.

## Important helpers

| Helper | Role |
| --- | --- |
| `bootstrap_comfyui_runtime()` | Mirrors the allocator and CLI-argument setup that ComfyUI performs before model execution. |
| `add_extra_model_paths()` | Loads ComfyUI model-path configuration when it is available. |
| `import_custom_nodes()` | Initializes custom node registration when the workflow needs it. |
| `get_value_at_index()` | Pulls the correct output from a node result, including wrapped `result` payloads. |
| `cleanup_comfyui_runtime()` | Performs best-effort teardown and optional model unload. |

## Export planning behavior

- `LoadOrderDeterminer` prioritizes loader-like nodes, encode functions, and nodes without linked inputs.
- `WorkflowPlanner` sanitizes node ids so subgraph-style ids remain unique in Python identifiers.
- Symbol-heavy input names are emitted with dictionary expansion rather than invalid keyword arguments.
- `seed` and `noise_seed` values are synchronized back into `prompt` so the exported script preserves the workflow state.
- `WorkflowRenderer` formats the final result with `black`.

## Troubleshooting cues

- If the generated script cannot import `torch`, the runtime Python is wrong or ComfyUI dependencies are missing.
- If custom nodes do not resolve, make sure the runtime can find the ComfyUI checkout and the node package itself.
- If the script writes the wrong output file name, remember that the CLI default is `workflow_api.py`.
- If cleanup does not unload models, set `COMFYUI_TOPYTHON_UNLOAD_MODELS=1` or call `main(unload_models=True)`.
