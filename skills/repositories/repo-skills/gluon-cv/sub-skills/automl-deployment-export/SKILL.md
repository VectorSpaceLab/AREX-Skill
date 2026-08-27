---
name: automl-deployment-export
description: "Use optional GluonCV AutoGluon wrappers and MXNet/Torch deployment
  export utilities safely."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: gluon-cv
  package: gluoncv
license: Apache 2.0
---

# GluonCV AutoML and deployment export

Use this sub-skill when a task mentions `gluoncv.auto`, AutoGluon, `ImageClassification`, `ImagePrediction`, `ObjectDetection`, `LiteConfig`, `DefaultConfig`, `fit`, `fit_summary`, `fit_history`, `load`, exporting a pretrained model, MXNet `symbol.json`/`.params` deployment files, ONNX, TVM, DirectPose export, quantized/int8 inference, or errors about missing `autogluon`, `timm`, `onnx`, `tvm`, `pycocotools`, pretrained weights, or model cache.

This sub-skill is for optional surfaces. A base `gluoncv` import does not prove that `gluoncv.auto`, AutoGluon training, ONNX export, TVM export, or quantized deployment stacks are installed.

## Natural triggers

Load this sub-skill for requests involving:

- `from gluoncv.auto.tasks import ImageClassification, ImagePrediction, ObjectDetection`.
- AutoGluon HPO/search spaces, `autogluon.core`, `ag.Categorical`, `ag.Int`, `ag.Real`, old AutoGluon dependency pins, or AutoGluon deprecation warnings.
- Image-classification or object-detection AutoML task methods: `fit`, `fit_summary`, `fit_history`, `save`, and task-class `load`.
- Auto task datasets through `Task.Dataset`, including classification folders/CSV and object-detection VOC/COCO records.
- Exporting MXNet model-zoo networks with `gluoncv.utils.export_block`, the export-pretrained helper pattern, or C++ deployment JSON/params files.
- ONNX Runtime inference, MXNet-to-ONNX conversion, TVM export, DirectPose TVM mode, or TorchScript-to-TVM conversion.
- `--quantized`, `--deploy`, `--model-prefix`, `int8`, calibration, MXNet-MKL, VNNI, or CPU deployment acceleration.

## Route away

- General training/evaluation/demo script command construction: use `../training-evaluation-scripts/`.
- MXNet model-name families, `get_model` kwargs, dry model instantiation, custom heads, and model cache basics: use `../mxnet-model-zoo/`.
- Dataset layout and annotation validation before AutoML training: use `../data-transforms-datasets/`.
- PyTorch action-recognition, DirectPose model/config usage outside export packaging: use `../torch-video-workflows/`.

## First workflow choice

1. **Classify the request as AutoML or deployment.** AutoML tasks train or load AutoGluon-backed estimators; deployment workflows export or consume pretrained/static artifacts.
2. **Check optional dependencies before code changes.** `gluoncv.auto` needs the legacy AutoGluon stack. Torch-backed image classification also needs `torch` plus `timm`. ONNX, TVM, pycocotools, MXNet-MKL, and GPU packages are optional workflow-specific stacks.
3. **For AutoML, choose the task wrapper and config.** Use `ImageClassification`/`ImagePrediction` for image folders or CSVs and `ObjectDetection` for VOC/COCO-like data. Start with conservative config values; CPU/no-GPU runs fall back to `LiteConfig` and are often too slow for non-tiny datasets.
4. **For export, validate model names without exporting first.** Run the bundled helper; it checks the MXNet model registry and prints export prerequisites without downloading weights or writing model files:

   ```bash
   python scripts/export_name_check.py --model resnet18_v1
   ```

5. **Only perform real export when side effects are allowed.** Exporting a pretrained model usually downloads weights if absent and writes `*-symbol.json` plus `*-0000.params`. ONNX/TVM exports add their own heavy dependencies and generated artifacts.
6. **Keep deployment format and input preprocessing explicit.** The default MXNet export preprocess expects raw RGB HWC input and embeds mean/std normalization. Disabling preprocess changes layout expectations to CHW/CTHW and may require an explicit `data_shape`.

## Core facts to preserve

- `gluoncv.auto.tasks` is a legacy optional AutoGluon surface and warns that `auto` was planned for deprecation in favor of AutoGluon Vision.
- The package's `auto` extra pins `autogluon.core==0.3.1`; modern Python environments may not resolve this old stack.
- `ImageClassification` dispatches model names to `timm`/Torch first when `torch` and `timm` are installed, then falls back to MXNet GluonCV model names when MXNet is installed.
- If no GPU is detected or allowed, the AutoML task constructors use conservative `LiteConfig` defaults with zero GPUs. They cap requested GPUs to the detected count and warn when a config asks for more GPUs than available.
- `fit(...)` returns an estimator object; use `task.fit_summary()` and `task.fit_history()` for HPO summaries, then `estimator.save(...)` and `TaskClass.load(...)` or estimator-class `load(...)` for persistence.
- MXNet deployment export uses `gluoncv.utils.export_block(path, block, ...)`. The simple pretrained export pattern is `get_model(name, pretrained=True)` followed by `export_block(name, net, preprocess=True, layout='HWC')`.
- ONNX export is a second stage after MXNet symbol/params export and depends on MXNet ONNX support plus ONNX Runtime for inference checks.
- TVM export is optional. MXNet TVM export uses `gluoncv.utils.export_tvm`; Torch DirectPose TVM export uses TorchScript tracing, TVM Relay, and a custom NMS converter.
- Quantized/int8 inference is an MXNet deployment variant, not a universal model flag. It requires compatible MXNet/MKL or quantization support and suitable model candidates.

## References and helper

- [AutoML and export reference](references/automl-and-export.md) — task APIs, config/resource behavior, dependency gates, export recipes, ONNX/TVM/int8 notes.
- [AutoML/export troubleshooting](references/troubleshooting.md) — missing optional dependencies, legacy Python conflicts, GPU fallback, export/cache, ONNX/TVM, and quantization failures.
- [MXNet export name checker](scripts/export_name_check.py) — safe argparse helper for model-name validation and export-prerequisite reporting; performs no download/export by default.
