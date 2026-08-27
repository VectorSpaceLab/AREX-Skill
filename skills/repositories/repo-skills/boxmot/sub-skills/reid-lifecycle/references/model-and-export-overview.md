# Model and Export Overview

## Registry facts

Useful registries:

- `boxmot.reid.backbones.registered_backbone_names()` lists registered ReID backbones.
- `boxmot.configs.list_training_recipes()` lists bundled training recipes.
- `boxmot.reid.datasets.DATASET_REGISTRY` maps dataset aliases to dataset classes.
- `boxmot.reid.core.config.TRAINED_URLS` lists known downloadable `.pt` checkpoints.
- `boxmot.reid.core.registry.ReIDModelRegistry.get_model_name(path)` infers architecture from checkpoint metadata or filename.
- `boxmot.reid.core.registry.ReIDModelRegistry.get_nr_classes(path)` infers dataset class count.

## Training recipes observed in the inspected package

- `csl_tinyvit_7m`
- `csl_tinyvit_11m`
- `csl_tinyvit_23m`
- `lmbn_n`
- `lmbn_n_market1501`
- `mobilenetv4`
- `mobilenetv4_conv_small`
- `mobilenetv4_conv_medium`
- `mobilenetv4_conv_large`
- `vit`

Use the registry summary script for a current list:

```bash
python sub-skills/reid-lifecycle/scripts/reid_registry_summary.py --json --limit 20
```

## Export formats

| Format | CLI argument | Suffix | CPU | GPU |
| --- | --- | --- | --- | --- |
| PyTorch | `-` | `.pt` | yes | yes |
| TorchScript | `torchscript` | `.torchscript` | yes | yes |
| ONNX | `onnx` | `.onnx` | yes | yes |
| OpenVINO | `openvino` | `_openvino_model` | yes | no |
| TensorRT | `engine` | `.engine` | no | yes |
| TensorFlow Lite | `tflite` | `.tflite` | yes | no |

## Export notes

- ONNX is the default export include.
- OpenVINO and TensorRT use ONNX as an intermediate.
- TensorRT requires a compatible NVIDIA runtime and GPU.
- TFLite static quantization requires calibration data; the default static activation bits are 16.
- `--half` with TensorRT export requires GPU.

## Embedding backend suffixes

`ReID.model_type(...)` matches model suffixes to these backend families:

- `.pt`
- `.torchscript`
- `.onnx`
- `_openvino_model` / `.xml` / `.bin`
- `.engine`
- `.tflite`

## Why preprocess matters

ReID checkpoints and training configs may encode crop preprocessing and feature-selection settings. Keep `preprocess`, `imgsz`, and `inference_feature` aligned between training, evaluation, comparison, export, and tracking when reproducibility matters.
