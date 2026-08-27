# Troubleshooting

## Purpose

Use this page for cross-cutting BEVFormer failures that do not yet belong to one sub-skill. It points you to the owning route and the bundled helper that should be used next.

## Common Failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: projects.mmdet3d_plugin` or `No module named mmdet3d` | The legacy OpenMMLab stack is missing, or the checkout is not on the import path. | Run `scripts/check_bevformer_environment.py --repo-root <checkout-root>` and then switch to `installation-and-configs`. |
| Config printing fails with `yapf`, `pretty_text`, or a config formatting import error | The installed `yapf`/`mmcv` combination does not match the repo's legacy stack. | Use `installation-and-configs`; the static config inspector avoids the old pretty-print path. |
| A BEVFormerV2 config complains about `frames`, `mono_cfg`, or `DD3DMapper` | A V2 config is being treated like a V1 config, or the V2-specific dataset fields are missing. | Read `model-zoo-and-configs.md`, then use `installation-and-configs` and `dataset-preparation`. |
| The layout checker reports missing `samples/`, `sweeps/`, `maps/`, `v1.0-trainval/`, `v1.0-test/`, `can_bus/`, or `nuscenes_infos_temporal_*.pkl` | The nuScenes tree or CAN-bus expansion is incomplete. | Run the dataset-preparation layout checker and fix the missing paths before training. |
| A train or eval command fails because the checkpoint is missing, or `--eval` and `--format-only` are both set | The launch command is incomplete or has conflicting flags. | Use the command builders in `training-and-evaluation` and supply a real checkpoint. |
| The log summarizer prints `records=0` or cannot find the requested metric | The file is not JSON/JSONL, or the metric name does not match the log keys. | Use `analysis-and-utilities` with a tiny JSONL fixture and the exact metric key. |
| `torch.cuda.is_available()` is false on a GPU host | The torch wheel, driver, or container GPU passthrough is wrong for the machine. | Reinstall the documented CUDA wheel stack and rerun the environment checker before attempting train/eval. |

## Escalation Rule

- If the failure is about install/import/config inspection, go to `installation-and-configs`.
- If the failure is about raw nuScenes or CAN-bus paths, go to `dataset-preparation`.
- If the failure is about command composition, launchers, or checkpoints, go to `training-and-evaluation`.
- If the failure is about logs, plots, or output summaries, go to `analysis-and-utilities`.
