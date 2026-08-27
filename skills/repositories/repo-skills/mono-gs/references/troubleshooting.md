# MonoGS Troubleshooting

## Choose the nearest owner first

- Install, CUDA, `nvcc`, submodule, and import failures: `sub-skills/environment-setup/`.
- Dataset path, config inheritance, and missing frames/poses: `sub-skills/data-and-configs/`.
- Long offline run behavior, GUI/headless choices, multiprocessing, and OOM:
  `sub-skills/offline-slam/`.
- Metrics, W&B, result folders, LPIPS, ATE, and saved PLYs:
  `sub-skills/evaluation-and-results/`.
- RealSense camera, USB, Open3D/GLFW/OpenGL window issues:
  `sub-skills/live-demo/`.

## CUDA or extension imports fail

Symptoms include `ModuleNotFoundError` for `simple_knn._C` or
`diff_gaussian_rasterization`, `torch.cuda.is_available() == False`, or runtime
messages about missing kernels. MonoGS core workflows require a CUDA-capable
PyTorch environment and compiled extension submodules.

Use [scripts/check_monogs_environment.py](../scripts/check_monogs_environment.py)
with `--require-cuda` against the active checkout before debugging datasets or
configs.

## Config loads but the run fails immediately

Likely causes:

- `Dataset.dataset_path` points at a missing or wrong dataset root.
- A scene config's `inherit_from` path was copied incorrectly.
- A live RealSense config was used for an offline task.
- The selected sensor type does not match the data family.

Use the `data-and-configs` validator with `--check-files`, then re-plan the run
with `offline-slam/scripts/plan_slam_run.py`.

## GUI appears during a batch run

`slam.py` has no `--headless` flag. Disable GUI through a config copy with
`Results.use_gui: false`, or use `--eval` for evaluation. Live RealSense mode
forces GUI on, so do not use live configs for headless evaluation.

## W&B prompts during evaluation

`--eval` forces `Results.use_wandb=True`. For offline environments use:

```bash
WANDB_MODE=disabled python slam.py --config <config> --eval
```

or use a config copy with `Results.use_wandb: false` and omit `--eval`.

## Downloads are blocked

The bundled dataset scripts intentionally make network access explicit. If the
host cannot download TUM, Replica, or EuRoC data, stop and ask for a mounted
existing dataset, a mirror approved by the user, or a narrowed task that does not
require native dataset execution.
