---
name: detectron2
description: "Use Detectron2 for object detection, segmentation, configuration,
  datasets, training, inference, export, and extension workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detectron2 Repo Skill

Use this repo skill when a task mentions Detectron2, Detectron, object detection, instance/keypoint/panoptic/semantic segmentation, Detectron2 model zoo configs, `DefaultPredictor`, `DefaultTrainer`, `DatasetCatalog`, Detectron2 export, or custom Detectron2 model components.

## Start Here

- Verify the package and optional runtime pieces with [scripts/check_detectron2_env.py](scripts/check_detectron2_env.py) before debugging imports, CUDA, OpenCV, Caffe2, or ONNX.
- Read [references/troubleshooting.md](references/troubleshooting.md) for install/build/import, optional dependency, CUDA/backend, model-zoo download, and source-demo caveats.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this generated skill is current for a local checkout.
- Router metadata for managed import lives in [references/repo-routing-metadata.json](references/repo-routing-metadata.json).

## Installation Baseline

Detectron2 is a PyTorch-based library with native C++/CUDA extensions. Public installs should start from a compatible PyTorch and torchvision pair, then install Detectron2 from a release wheel or source build appropriate for the platform.

```bash
python -m pip install torch torchvision
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
python - <<'PY'
import detectron2
print(detectron2.__version__)
PY
```

For source builds, ensure `torch` is importable before running Detectron2 setup. If editable source installation fails because build isolation cannot import `torch`, retry with a package/build process that disables build isolation after installing torch. OpenCV is optional for core APIs but needed for demo-style image/video visualization workflows.

## Route By Task

- **Configs and model zoo:** Use [sub-skills/configuration-model-zoo/SKILL.md](sub-skills/configuration-model-zoo/SKILL.md) for Yacs YAML configs, LazyConfig Python configs, `_BASE_`, overrides, `LazyCall`, `instantiate`, model-zoo config paths, and checkpoint URLs.
- **Data and datasets:** Use [sub-skills/data-datasets/SKILL.md](sub-skills/data-datasets/SKILL.md) for `DatasetCatalog`, `MetadataCatalog`, COCO helpers, standard dataset dicts, metadata keys, mappers, augmentations, and train/test data loaders.
- **Training and evaluation:** Use [sub-skills/training-evaluation/SKILL.md](sub-skills/training-evaluation/SKILL.md) for project-local train/eval driver commands, `DefaultTrainer`, hooks, `launch`, checkpointing, evaluators, `inference_on_dataset`, and solver/LR/batch-size adjustments.
- **Inference and visualization:** Use [sub-skills/inference-visualization/SKILL.md](sub-skills/inference-visualization/SKILL.md) for `DefaultPredictor`, direct model inference, `Instances`, `Boxes`, masks, model input/output formats, `Visualizer`, confidence thresholds, CPU overrides, and prediction JSON sanity checks.
- **Deployment and export:** Use [sub-skills/deployment-export/SKILL.md](sub-skills/deployment-export/SKILL.md) for TorchScript tracing/scripting, optional Caffe2/ONNX planning, `TracingAdapter`, `scripting_with_instances`, model analysis, benchmarking, and safe export command construction.
- **Extensions and projects:** Use [sub-skills/extension-projects/SKILL.md](sub-skills/extension-projects/SKILL.md) for registries, custom backbones/ROI heads/meta-architectures, `@configurable`, custom trainers, and bundled or optional research projects such as PointRend, DeepLab, Panoptic-DeepLab, DensePose, TensorMask, ViTDet, and MViTv2.

## Common Decisions

- **Yacs vs LazyConfig:** YAML configs use `get_cfg()`, `merge_from_file()`, and alternating `KEY VALUE` overrides. Python configs use `LazyConfig.load()` and `key=value` overrides.
- **Weights vs config:** Config inspection should not build a model or download weights. Use model-zoo URL helpers for checkpoint URLs, and load weights only when inference/evaluation/export is intentional.
- **Dataset first:** Custom training/evaluation needs dataset registration and metadata before `cfg.DATASETS.TRAIN/TEST` or evaluator logic can work.
- **CPU-only work:** Set `MODEL.DEVICE cpu` for Yacs configs or the matching LazyConfig model device field before constructing predictors/models.
- **Long-running work:** Ask before launching training, full evaluation, benchmarks, export runs that load large weights, multi-GPU/multi-machine jobs, or commands that download model/data artifacts.

## Bundled Helpers

- Root diagnostic: [scripts/check_detectron2_env.py](scripts/check_detectron2_env.py) checks imports, package version, torch/CUDA, OpenCV, Caffe2/ONNX availability, and key API signatures.
- Config inspector: [sub-skills/configuration-model-zoo/scripts/inspect_config.py](sub-skills/configuration-model-zoo/scripts/inspect_config.py) safely inspects Yacs, LazyConfig, or model-zoo configs without building models.
- Dataset validators: [sub-skills/data-datasets/scripts/validate_dataset_dicts.py](sub-skills/data-datasets/scripts/validate_dataset_dicts.py) and [sub-skills/data-datasets/scripts/validate_dataset_registration.py](sub-skills/data-datasets/scripts/validate_dataset_registration.py) check dataset records/catalog behavior.
- Command builders: training, inference/demo, export, and analysis sub-skills include dry-run command builders that print commands or plans but do not run heavyweight work.

## Source Caveats Captured

- The source checkout used for this skill had package version `0.6` and a clean git state at the recorded commit in provenance.
- The source demo CLI was treated as evidence rather than a runtime dependency because its `demo.py` imports a non-package path in this checkout; use the inference sub-skill helpers and API patterns instead.
- Caffe2 was not available in the inspection environment, so Caffe2 export guidance is optional and gated behind dependency checks.
