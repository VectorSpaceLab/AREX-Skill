# CLI Export Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'torch'` when running a generated script | The script is not running in the ComfyUI Python environment. | Run it with the interpreter that launches ComfyUI, or install the ComfyUI runtime dependencies into the target environment. |
| Exporter cannot find ComfyUI | `COMFYUI_PATH` is unset and no parent directory contains a `ComfyUI` folder. | Set `COMFYUI_PATH` or run from a checkout layout where ComfyUI is discoverable. |
| Generated script does not import a custom node | The workflow uses a custom node that is not available in the runtime. | Install the node in ComfyUI and make sure the checkout can load custom nodes before export or execution. |
| Exported code looks structurally wrong | The workflow JSON is missing required inputs or does not match the node mapping. | Re-export the workflow from ComfyUI, then regenerate the Python. |
| `black` import failure | The exporter renderer requires `black`. | Install `black` in the same environment that runs the exporter. |
| Generated script keeps old models in memory | The default cleanup is conservative. | Set `COMFYUI_TOPYTHON_UNLOAD_MODELS=1` or call `main(unload_models=True)`. |
| Output uses unexpected node identifiers | The planner is sanitizing subgraph-style ids or symbol-heavy keys. | Treat the sanitized names as expected; inspect the generated code sections rather than the raw workflow keys. |

## Native checks that match these problems

- `tests/test_generator_codegen_issue_regressions.py`
- `tests/test_node_runtime_cleanup.py`
- `tests/test_upscale_model_loader_export.py`
- `tests/test_runtime_validation_harness.py`
