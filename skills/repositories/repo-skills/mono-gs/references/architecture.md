# MonoGS Architecture

## Purpose

Read this when a task spans installation, dataset/config preparation, running
SLAM, evaluation, or live visualization. It maps the major runtime pieces and
which sub-skill owns each workflow.

## Entry point

MonoGS has one runtime CLI:

```bash
python slam.py --config <config-yaml> [--eval]
```

`--config` loads an inherited YAML tree. `--eval` overrides the loaded config to
run headless evaluation with result saving, rendering metrics, and W&B enabled.

## Runtime flow

1. `utils.config_utils.load_config` resolves recursive `inherit_from` YAML.
2. `slam.py` derives runtime fields such as `Training.monocular` from
   `Dataset.sensor_type`.
3. `GaussianModel` is created with spherical-harmonic degree 3 when enabled,
   otherwise 0.
4. `utils.dataset.load_dataset` chooses a loader for TUM, Replica, EuRoC, or
   RealSense.
5. `SLAM` creates frontend/backend queues and optional GUI queues.
6. `BackEnd` runs in a spawned process and optimizes/densifies/prunes Gaussians.
7. `FrontEnd` runs tracking/keyframe logic in the main process.
8. The GUI process starts only when `Results.use_gui` is true; RealSense live
   mode forces GUI on.
9. Evaluation functions save trajectory stats, render metrics, and point-cloud
   PLY artifacts when the config enables them.

## Ownership map

| Area | Owner sub-skill | Key evidence distilled |
| --- | --- | --- |
| Python/CUDA environment, submodules, import checks | `environment-setup` | `environment.yml`, submodule setup files, CUDA renderer/model imports |
| Dataset downloads, data trees, config inheritance | `data-and-configs` | `configs/**`, dataset parsers, download shell scripts |
| Offline monocular/RGB-D/stereo runs | `offline-slam` | `slam.py`, frontend/backend/dataset classes, README commands |
| Evaluation metrics and result folders | `evaluation-and-results` | `slam.py --eval`, `utils/eval_utils.py`, Gaussian PLY saving |
| RealSense and GUI operation | `live-demo` | live configs, `RealsenseDataset`, Open3D/GLFW GUI code |

## Backend truth

Core MonoGS workflows are CUDA-first. The renderer imports a custom
`diff_gaussian_rasterization` extension, `GaussianModel` imports `simple_knn`,
and most tensors are created on `cuda` or `cuda:0`. A CPU-only import is not a
valid substitute for offline SLAM or evaluation.
