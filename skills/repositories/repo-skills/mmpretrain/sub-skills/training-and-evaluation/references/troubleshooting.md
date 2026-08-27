# Troubleshooting

Use `scripts/print_config.py` first whenever the failure looks like a config merge or launch-argument problem. It shows the resolved config after inheritance and command-line overrides.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `mmengine` or `mmcv` | The runtime dependencies are not installed in the active environment. | Install the package dependencies before using the launchers or bundled helpers that load configs. |
| `get unexpected keyword ...` after editing a schedule or runtime block | An inherited dict still contributes old keys. | Add `_delete_=True` to replace the inherited branch, then inspect the merged config again. |
| `--cfg-options` changes do not appear to take effect | The override string was split or quoted incorrectly. | Keep list/tuple values quoted, avoid whitespace inside the quoted value, and use dotted keys for nested fields. |
| `ValueError` about `--out-item` needing `--out` | The test command asked for a dump format without an output file. | Add `--out path/to/file` or remove `--out-item`. |
| `VisualizationHook is not set` when using `--show` or `--show-dir` | The config has no visualization hook in `default_hooks`. | Enable the visualization hook in the config before retrying. |
| A resumed run starts from the wrong checkpoint | `--resume` and `load_from` were confused. | Use `--resume` with no value for auto-resume, `--resume PATH` to continue a specific checkpoint, and `load_from` only for initialization. |
| `--amp` fails on a custom optimizer wrapper | The wrapper type is not compatible with AMP. | Use `OptimWrapper` or `AmpOptimWrapper`, or disable `--amp` for that run. |
| TTA results look different from the non-TTA run | The config lacks `tta_model` or `tta_pipeline`, so the CLI falls back to flip TTA. | Inspect the resolved config and add explicit TTA settings if you need a custom merge policy. |
| Distributed training or testing hangs | The node list, port, or master address is inconsistent across processes, or a stale job still owns the port. | Reuse the same `PORT` and `MASTER_ADDR` on every node, give each node a unique `NODE_RANK`, and free the port before relaunching. |
| NCCL errors appear on a GPU run | The distributed backend or GPU visibility is wrong for the machine. | Check that the launcher matches the hardware, verify visible GPUs, and retry with a clean environment. |
| CPU fallback still seems to use a GPU | A GPU remains visible to the process. | Prefix the command with `CUDA_VISIBLE_DEVICES=-1` and keep the launcher on `none` for single-process CPU runs. |
| Dataloader workers hang or crash | Persistent workers or pinned memory are causing trouble. | Retry with `--no-persistent-workers` and, if needed, `--no-pin-memory`. |
| `--auto-scale-lr` appears to do nothing | The config does not declare a meaningful `auto_scale_lr.base_batch_size`. | Set the base batch size in the config, then rerun with `--auto-scale-lr`. |
| K-fold cross validation fails on validation or test wrapping | The wrapped dataset no longer has a `pipeline`, or the config already uses a wrapper that the helper cannot safely rewrite. | Ensure the dataset config keeps a `pipeline`, or write the K-fold experiment manually. |

## Quick checks

- Inspect the merged config with `scripts/print_config.py`.
- If the run is distributed, confirm `PORT`, `NNODES`, `NODE_RANK`, and `MASTER_ADDR` before launching.
- If the run is CPU-only, confirm `CUDA_VISIBLE_DEVICES=-1` is set in the same shell that launches the command.
