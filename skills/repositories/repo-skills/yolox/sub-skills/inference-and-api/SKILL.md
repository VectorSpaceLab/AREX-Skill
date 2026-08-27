---
name: inference-and-api
description: "Use YOLOX for PyTorch inference, demo CLI/API setup, model
  selection, checkpoint loading, preprocessing/postprocessing, visualization,
  and quick diagnostics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# YOLOX Inference And API

Use this sub-skill when the task is to run YOLOX image, video, or webcam inference, choose a built-in model or custom experiment, load a checkpoint, reproduce the package demo flow in Python, inspect inference-time APIs, or perform a lightweight install/model smoke check.

Route training, evaluation, custom datasets, caching, and experiment logging to `../training-and-data/SKILL.md`. Route ONNX, TorchScript, TensorRT, OpenVINO, ncnn, and other deployment backend work to `../export-and-deployment/SKILL.md`.

## Read/run map

- Read [references/inference-workflows.md](references/inference-workflows.md) for package-style demo commands, checkpoint loading expectations, and a distilled Python inference recipe.
- Read [references/model-and-api-reference.md](references/model-and-api-reference.md) for built-in model names, default experiment facts, key signatures, output conventions, and source-script treatment.
- Read [references/troubleshooting.md](references/troubleshooting.md) for checkpoint, image/video, device, FP16, legacy-weight, OpenCV, and TensorRT-route failures.
- Run [scripts/yolox_inference_smoke.py](scripts/yolox_inference_smoke.py) to validate imports, experiment resolution, model construction, optional CUDA allocation, and optional dummy forward without weights or downloads.

## Fast decisions

1. For standard COCO architectures, prefer `--name` with `yolox-s`, `yolox-m`, `yolox-l`, `yolox-x`, `yolox-tiny`, `yolox-nano`, or `yolov3`.
2. For a custom class count, custom size, or modified architecture, prefer `--exp-file` and a checkpoint trained from that same `Exp`.
3. For visual demos, use installed module commands such as `python -m yolox.tools.demo ...` rather than checkout script paths.
4. For library use, reproduce the core flow: `get_exp`, `exp.get_model()`, load `ckpt["model"]` or a state dict, `model.eval()`, optional CUDA/half/fuse, `ValTransform`, forward, `postprocess`, and `vis`.
5. For deployment-specific `--trt` or exported graphs, stop after identifying the route and hand off to export/deployment.

## Minimal safe diagnostic

From this sub-skill directory:

```bash
python scripts/yolox_inference_smoke.py --name yolox-nano --device cpu --test-size 64
```

Add `--dummy-forward` only when you want to exercise a real forward pass without weights. Use a small `--test-size` for CPU-only diagnostics.
