---
name: mmdetection3d
description: "Use MMDetection3D for 3D detection, segmentation, dataset
  preparation, configs, training, evaluation, visualization, customization, and
  serving workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDetection3D repo skill

Use this skill when a task involves MMDetection3D / `mmdet3d`, OpenMMLab 3D detection, 3D semantic segmentation, LiDAR point clouds, monocular or multi-modality 3D detection, OpenMMLab configs, dataset conversion, training/evaluation launch commands, 3D boxes/points, or MMDetection3D deployment utilities.

MMDetection3D is a PyTorch/OpenMMLab toolbox for general 3D object detection and related 3D perception tasks. It commonly depends on PyTorch, MMEngine, MMCV, MMDetection, dataset SDKs, and CUDA-capable backends for most point-cloud model execution.

## First checks

1. Confirm whether the user wants to **use** MMDetection3D as a package, **run** a workflow in a checkout, or **modify** a component.
2. Check package/runtime readiness with [`scripts/check_mmdet3d_env.py`](scripts/check_mmdet3d_env.py). This script reports installed versions, CUDA availability, optional sparse backends, and key API imports without running model inference.
3. Read [`references/backend-compatibility.md`](references/backend-compatibility.md) before promising CPU, CUDA, sparse-convolution, or project-extension support.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when imports, OpenMMLab dependency versions, configs, datasets, checkpoints, or visualizers fail.
5. Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is stale for a current checkout.

## Installation shape

For normal use, prefer the public OpenMMLab installation flow:

```bash
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0rc4,<2.2.0"
mim install "mmdet>=3.0.0,<3.3.0"
mim install "mmdet3d>=1.4.0"
```

For source development, install PyTorch first, then the OpenMMLab dependencies above, then install the package from the checkout. Do not install every optional sparse backend or project extra unless the selected model family needs it.

Minimal smoke check:

```bash
python - <<'PY'
import mmdet3d, torch
print('mmdet3d', mmdet3d.__version__)
print('cuda available', torch.cuda.is_available())
PY
```

## Route map

| User intent | Read |
| --- | --- |
| Run point-cloud, monocular, multi-modality, or segmentation inference; choose low-level API vs inferencer class; handle saved predictions or no-display visualization | [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md) |
| Prepare KITTI, Waymo, NuScenes, Lyft, SemanticKITTI, S3DIS, ScanNet, SUN RGB-D, custom layouts, or old info-pickle migrations | [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md) |
| Select or adapt configs, model-zoo families, dataset/model bases, config inheritance, registry scope, or `--cfg-options` | [`sub-skills/configuration-model-zoo/SKILL.md`](sub-skills/configuration-model-zoo/SKILL.md) |
| Build training, testing, evaluation, TTA, visualization-hook, distributed, multi-machine, or Slurm commands | [`sub-skills/training-evaluation/SKILL.md`](sub-skills/training-evaluation/SKILL.md) |
| Use 3D box/point/coordinate APIs, project boxes to images, debug yaw/origin/mode issues, or use visualizer outputs | [`sub-skills/structures-visualization/SKILL.md`](sub-skills/structures-visualization/SKILL.md) |
| Add custom datasets, transforms, model components, runtime hooks, or optional project extensions | [`sub-skills/customization-extensions/SKILL.md`](sub-skills/customization-extensions/SKILL.md) |
| Package for TorchServe, inspect serving artifacts, publish/convert checkpoints, analyze logs, print configs, estimate FLOPs, or use miscellaneous tools | [`sub-skills/serving-tools/SKILL.md`](sub-skills/serving-tools/SKILL.md) |

## Operating boundaries

- Do not run training, evaluation, dataset conversion, model downloads, checkpoint-backed inference, Docker/TorchServe, Slurm jobs, or benchmark utilities unless the user explicitly requests execution and accepts the cost, data, hardware, and side effects.
- Most point-cloud models and several metrics require CUDA or CUDA-built dependencies for faithful execution. CPU-only checks can still validate imports, config parsing, command construction, dataset layouts, and selected geometry APIs.
- Optional sparse backends such as `spconv`, MinkowskiEngine, and TorchSparse are model-family dependent. Install only the backend required by the selected config.
- Keep user datasets, checkpoints, and output paths explicit. MMDetection3D configs often couple `data_root`, classes/metainfo, evaluators, pipelines, and box/coordinate modes.
- Prefer bundled command builders and checkers in this skill for planning. They are safe by default and do not start native MMDetection3D jobs.

## Common entry points

- Package APIs: `mmdet3d.apis.init_model`, `inference_detector`, `inference_mono_3d_detector`, `inference_multi_modality_detector`, `inference_segmentor`, and the 3D inferencer classes.
- Registries: `mmdet3d.registry.MODELS`, `DATASETS`, `TRANSFORMS`, `METRICS`, `VISUALIZERS`.
- Structures: `LiDARInstance3DBoxes`, `CameraInstance3DBoxes`, `DepthInstance3DBoxes`, `Box3DMode`, `Coord3DMode`, point classes, and projection helpers.
- Workflow surfaces: OpenMMLab config files, dataset info pickles, conversion commands, checkpoint/config pairs, work dirs, evaluator output prefixes, and visualization outputs.
