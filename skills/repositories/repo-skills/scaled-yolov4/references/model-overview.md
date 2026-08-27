# Model overview

## Model family in this checkout

This repository provides a ScaledYOLOv4 object-detection family built around these YAML configs:

- `models/yolov4-p5.yaml`
- `models/yolov4-p6.yaml`
- `models/yolov4-p7.yaml`
- `models/yolov4-csp.yaml`

The README documents the P5/P6/P7 variants as the main public workflows. The YAML files define `anchors`, `nc`, `depth_multiple`, `width_multiple`, `backbone`, and `head` entries that are consumed by the model builder. The same source tree is mirrored under `runtime/` so the bundled helpers can run the concrete workflows without depending on the original checkout.

## Core model objects

- `models/yolo.py: Model(cfg='yolov4-p5.yaml', ch=3, nc=None)` loads a YAML model definition or a dict, optionally overrides `nc`, builds the module graph with `parse_model`, and then computes detection strides from a synthetic forward pass.
- `models/yolo.py: Detect` stores anchor tensors, the detection-layer count, the output width `nc + 5`, and an `export` flag used during TorchScript/ONNX export.
- `models/experimental.py: attempt_load(weights, map_location=None)` loads one or more checkpoints into an ensemble wrapper and returns a single model or an ensemble.
- `models/common.py: Conv` is the default convolution block, and it uses `mish_cuda.MishCuda` as its activation.
- The bundled `runtime/` mirror contains executable copies of `detect.py`, `test.py`, `train.py`, `models/`, `utils/`, and the shipped YAML configs.

## Why the CUDA extension matters

`models/common.py` imports `MishCuda` from `mish_cuda` directly. That means:

- A pure CPU import check is not enough to prove the full model stack works.
- Full model construction and forward validation should be done in a CUDA-capable environment that has the Mish extension installed.
- If the import fails, the failure is usually environmental, not a model-logic bug.

## Builder behavior to remember

- `Model` computes strides by running a synthetic 256x256 pass during initialization.
- `Detect` normalizes anchors by stride and checks anchor order.
- Bias initialization happens once during model creation.
- `Model.forward(augment=True)` runs augmented inference with scale and flip combinations.
- `Model.fuse()` converts `Conv` blocks into fused conv-only inference blocks for deployment/export paths.

## Architectural conventions

- `parse_model` reads the YAML `backbone` and `head` lists and turns them into a sequential module graph.
- Several blocks are imported from `models/common.py` and `models/experimental.py`, including CSP-style and cross-convolution variants.
- The repo uses YOLO-style multi-scale detection heads, so stride, anchor order, and class-count consistency matter for all downstream workflows.

## Smoke-check guidance

The bundled `scripts/check_model_forward.py` can build one or more YAMLs from the bundled `runtime/` mirror and run a tiny synthetic forward pass under `torch.no_grad()`. Use it when you want to confirm that the installed environment can instantiate the model family without touching dataset assets or training data.
