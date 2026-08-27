---
name: det3d
description: "Guide Det3D PyTorch 3D object-detection workflows across
  configuration, KITTI/nuScenes/Lyft data preparation, GPU training and
  evaluation, custom CUDA operations, and visualization."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Det3D

Det3D is a legacy PyTorch toolbox for point-cloud 3D object detection. Use this
skill when a task names Det3D, `det3d`, PointPillars, SECOND, VoxelNet, CBGS,
KITTI/nuScenes/Lyft configs, point-cloud voxelization, or its `tools/train.py`
and `tools/test.py` workflows.

## First route

1. Identify the target dataset/version, model family, config, checkpoint, and
   whether the request is inspection, data preparation, training, evaluation,
   or visualization.
2. Read [compatibility.md](references/compatibility.md) and
   [troubleshooting.md](references/troubleshooting.md) before installing or
   changing dependencies.
3. Run the read-only [runtime diagnostic](sub-skills/runtime-ops/scripts/check_runtime.py)
   when imports or GPU behavior are uncertain.
4. Choose one focused route:

| Request signal | Read |
|---|---|
| Python configs, registries, PointPillars/SECOND/VoxelNet, anchors, model components | [configuration-and-models](sub-skills/configuration-and-models/SKILL.md) |
| KITTI, nuScenes, Lyft roots, info/db files, sweeps, transforms, voxel/data validation | [datasets-and-preprocessing](sub-skills/datasets-and-preprocessing/SKILL.md) |
| train/test CLI, checkpoints, resume, metrics, distributed/NCCL launch | [training-and-evaluation](sub-skills/training-and-evaluation/SKILL.md) |
| install/import, CUDA/C++ extensions, `spconv`, ABI/toolkit, backend diagnostics | [runtime-ops](sub-skills/runtime-ops/SKILL.md) |
| BEV/LiDAR/KITTI display, logs, FLOPs, headless rendering, result inspection | [visualization-and-analysis](sub-skills/visualization-and-analysis/SKILL.md) |

Cross-route tasks should keep one owner: configuration owns model structure;
data owns source schemas and conversion; training owns job/result lifecycle;
runtime owns environment/backend diagnosis; visualization owns display/artifact
interpretation.

## Public prerequisites

The source project documents Linux, Python 3.6+, PyTorch 1.1–1.6, CUDA 10.0/10.1,
CMake >=3.13.2, a compatible historical `spconv`, and dataset SDKs. Treat
these as versioned legacy constraints. A modern PyTorch/CUDA installation may
import some utilities while remaining incompatible with the custom extensions
or sparse-convolution model path. Det3D training/evaluation is documented as
GPU-only; CPU import is not a CPU training fallback.

Install in an isolated environment, select a torch/CUDA/toolkit/`spconv`
combination as a unit, then build extensions against that exact environment.
Install only the dataset and visualization extras needed by the selected route.
Do not download datasets/checkpoints or launch training implicitly.

## Minimal checks

```bash
python -c "import det3d; print(det3d.__version__)"
python sub-skills/runtime-ops/scripts/check_runtime.py
python sub-skills/datasets-and-preprocessing/scripts/validate_dataset_layout.py DATA_ROOT --dataset kitti
python sub-skills/training-and-evaluation/scripts/plan_launch.py test CONFIG --checkpoint CHECKPOINT
```

The last two helpers are non-mutating; the dataset checker returns nonzero when
required directories are absent, and the launch planner never starts a job.
For config-only inspection use `sub-skills/configuration-and-models/scripts/inspect_config.py`.

## Boundaries and safety

- Use user-provided paths for data, configs, checkpoints, and work directories.
- Treat `create_data`, training, evaluation, distributed launch, extension
  builds, and interactive visualization as side-effectful or hardware-bound.
- Do not claim an old model-zoo score is reproduced without matching dataset
  split, preprocessing, evaluator, checkpoint, and dependency versions.
- Do not point future agents to the original checkout's scripts or notebooks;
  the linked references and helpers are the self-contained replacements.

Read [repo-provenance.md](references/repo-provenance.md) when deciding whether
this graph is stale relative to a different Det3D checkout.
