---
name: gluon-cv
description: "Use GluonCV for computer-vision model-zoo, dataset, transform,
  training-script, AutoML, and deployment workflows across MXNet and PyTorch
  backends."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: gluoncv
  version: "0.11.0"
license: Apache 2.0
---

# GluonCV repo skill

Use this skill when a task names GluonCV, `gluoncv`, MXNet GluonCV, the GluonCV model zoo, GluonCV Torch action-recognition models, GluonCV datasets/transforms, GluonCV script-zoo training/evaluation commands, `gluoncv.auto`, or GluonCV export/deployment workflows.

GluonCV 0.11.0 is a legacy computer-vision toolkit with two backend families:

- **MXNet:** broad model zoo, datasets, transforms, metrics, and most classic training/eval/demo scripts.
- **PyTorch:** concentrated support for action recognition/video, DirectPose, COOT/video-language, Torch configs, and DDP helpers.

## First checks

1. Verify installation and backend compatibility before using APIs:

   ```bash
   python scripts/check_gluoncv_environment.py
   ```

2. If import fails, read `references/install-and-backends.md` and `references/troubleshooting.md` before changing code.
3. Choose a sub-skill by the user's task shape, not just by source directory names.

## Route map

| User task | Read |
| --- | --- |
| Pick, list, instantiate, smoke-check, or customize MXNet GluonCV models; use `gluoncv.model_zoo.get_model`; handle `reset_class` for SSD/YOLO/Faster R-CNN/Mask R-CNN; diagnose MXNet model-zoo failures. | `sub-skills/mxnet-model-zoo/SKILL.md` |
| Prepare/validate datasets, bbox records, image/video transforms, batchify functions, dataset roots, metrics, visualization, or dataset-preparation script expectations. | `sub-skills/data-transforms-datasets/SKILL.md` |
| Use PyTorch GluonCV action-recognition/video models, DirectPose, COOT, YACS configs, CPU smokes, DDP helpers, tensor shapes, or Torch optional dependency fixes. | `sub-skills/torch-video-workflows/SKILL.md` |
| Build safe command templates from GluonCV's classification/detection/segmentation/pose/action/depth/tracking/GAN/Re-ID training/evaluation/demo script zoo. | `sub-skills/training-evaluation-scripts/SKILL.md` |
| Use optional `gluoncv.auto` AutoGluon tasks, validate export/deployment model names, or reason about ONNX/TVM/quantized/int8 deployment prerequisites. | `sub-skills/automl-deployment-export/SKILL.md` |

## Backend and install guidance

Read `references/install-and-backends.md` when choosing dependencies. Important legacy constraints:

- `gluoncv` requires at least one backend import to succeed: MXNet `>=1.4,<2.0` or PyTorch `>=1.4,<2.0`.
- Modern default packages can be incompatible. MXNet 1.9.x commonly needs `numpy<1.24`; the Torch side may need `Pillow<10` because legacy code references `PIL.Image.LINEAR`.
- `gluoncv[full]` and `gluoncv[auto]` pull optional old stacks. Install only the extras needed for the selected workflow.
- CUDA, DDP, DALI, Horovod, TVM, ONNX, `decord`, `pycocotools`, and AutoGluon are optional workflow dependencies unless the user explicitly selects them.

Minimal import check:

```python
import gluoncv
print(gluoncv.__version__)
print(getattr(gluoncv, '_found_mxnet', None), getattr(gluoncv, '_found_pytorch', None))
```

If both MXNet and PyTorch are installed, GluonCV may warn about increased GPU memory footprint. Treat that warning as expected unless the task is memory-sensitive.

## Source and freshness

- Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout or should be refreshed.
- Runtime content here is self-contained. Do not rely on the original repository checkout to find examples, scripts, docs, tests, or configs; use the bundled references and helpers instead.
- If the user is editing GluonCV's repository internals rather than using the package, still start here for public API context, then use repository-maintenance practices and focused native tests appropriate to the edit.

## Safety defaults

- Prefer `pretrained=False`, CPU smokes, registry/list checks, and helper `--help` or JSON validation before network, GPU, training, benchmark, export, or dataset-conversion side effects.
- Confirm data paths, output directories, accelerator availability, runtime budget, network/cache policy, and overwrite behavior before launching real jobs.
- Keep optional backend claims explicit: CPU API smokes do not verify CUDA performance, DDP behavior, TVM compilation, ONNX runtime, or AutoGluon training.
