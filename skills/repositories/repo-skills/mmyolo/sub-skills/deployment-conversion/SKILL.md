---
name: deployment-conversion
description: "Guide MMYOLO export, checkpoint conversion, and deployment backend workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Deployment Conversion

Use this sub-skill when the user wants to turn an MMYOLO checkpoint into a deployment artifact or reason about a deployment backend.

## Use this sub-skill for
- EasyDeploy ONNX export and TensorRT engine build.
- EasyDeploy backend inference over exported ONNX or engine artifacts.
- MMDeploy deployment configs, SDK inference, and backend evaluation.
- YOLO-family checkpoint key conversion into MMYOLO format.
- Optional dependency and hardware gate checks for deployment backends.

## Do not use this sub-skill for
- Plain image or video inference from source checkpoints; use `inference-visualization`.
- Training, validation, testing, or log analysis; use `training-evaluation`.
- Basic config editing or model-family selection; use `config-customization`.

## Start here
1. Run [`scripts/check_deployment_dependencies.py`](scripts/check_deployment_dependencies.py).
2. Read [`references/deployment-conversion.md`](references/deployment-conversion.md).
3. Read [`references/model-converters.md`](references/model-converters.md).
4. If the request is blocked, read [`references/troubleshooting.md`](references/troubleshooting.md).

## Coverage
- EasyDeploy export, build, and image-demo flows.
- ONNXRuntime, TensorRT, RKNN, MMDeploy, and SDK-backed deployment paths.
- `mmyolo/deploy` object detection integration and backend-artifact inference.
- YOLOv5, YOLOv6, YOLOv7, YOLOv8, YOLOX, PPYOLOE, and RTMDet key conversion.
- Optional dependency and hardware gates for ONNXRuntime, TensorRT, RKNN, and DeepStream.

## Routing hint
If the user is asking for a deployment artifact, backend config, or conversion plan, stay here. If the user is only asking how to view detections on images or folders, route away to `inference-visualization`.
