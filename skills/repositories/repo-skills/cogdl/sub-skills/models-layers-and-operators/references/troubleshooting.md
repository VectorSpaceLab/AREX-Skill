# Models, Layers, and Operators Troubleshooting

| Symptom | Likely cause | Recovery | Next step |
| --- | --- | --- | --- |
| `Failed to import ... model.` | The requested model is not in `SUPPORTED_MODELS`, or the registry path is stale. | Inspect the registry with `scripts/inspect_model_registry.py` and choose a registered name. | Keep the user on a supported model family. |
| Parser/model-specific flags are missing | The model class does not define `add_args` or the registry path is incomplete. | Check the model entry in `SUPPORTED_MODELS` and the installed package import path. | If the model is new, fix the registry before continuing. |
| Layer output shape is wrong | The custom model and layer sizes do not match the graph feature dimension or `out_feats`. | Run `scripts/custom_gnn_smoke.py` on a toy graph first and adjust the constructor arguments. | Route the full model back through the smoke script. |
| `Graph.x` is missing or not a tensor | The task needs node features, but the data sub-skill has not produced them yet. | Build a proper `Graph` first or route the data issue to the graph-data sub-skill. | Do not debug the model before the data exists. |
| CUDA/operator import errors | Optional compiled kernels or GPU builds are unavailable or incompatible. | Keep the CPU path as the baseline and only install/verify the GPU path if the task truly needs it. | If the user specifically wants GPU kernels, move to the backend-specific path. |
| PyG/Jittor example import failures | The optional third-party dependency is missing. | Treat the example as reference-only unless the user explicitly wants to install that extra stack. | Mention the missing package by name. |
| `gcn`/`gat` works but a custom model fails | The custom model likely misses a normalization step or uses the wrong forward signature. | Compare the model against the recipe in `references/custom-gnn.md` and rerun the toy smoke. | If still broken, check the layer arguments and the `Graph` object. |

## Recovery order

1. Confirm the registry name.
2. Confirm the layer signature and forward call shape.
3. Run the toy smoke script.
4. Only then return to the full experiment or training wrapper workflow.
