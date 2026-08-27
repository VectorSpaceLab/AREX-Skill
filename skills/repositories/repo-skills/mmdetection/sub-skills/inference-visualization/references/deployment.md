# Deployment Route Selection

## Deployment Choices

| Need | Route | Notes |
| --- | --- | --- |
| Local Python inference, research, notebooks | `DetInferencer` or `init_detector` | Fastest to implement and easiest to debug. |
| Batch/offline image prediction | Packaged helper or `DetInferencer` | Save JSON and/or visualization files locally. |
| Video file processing | Manual frame loop | Depends on OpenCV codecs and output requirements. |
| Very large imagery | Sliced inference | Needs SAHI-style slicing and prediction merge. |
| ONNX/TensorRT/OpenVINO/etc. | MMDeploy | External deployment configs and backend runtime required. |
| HTTP model serving | TorchServe-style service | Requires service packaging, model archive, and server/container setup. |

## MMDeploy Overview

MMDetection deployment is usually handled by MMDeploy. The conversion route needs three separate choices:

1. **MMDetection model config** such as a Faster R-CNN, RTMDet, Mask R-CNN, or Grounding DINO config.
2. **Checkpoint** matching that config and target task.
3. **MMDeploy deployment config** matching task, backend, precision, dynamic/static shape, and input shape.

MMDeploy deployment config naming follows this pattern:

```text
{task}/{task}_{backend}-{precision}_{static|dynamic}_{shape}.py
```

Task selection matters:

- Use `detection/detection_*.py` for box-only detection models.
- Use `instance-seg/instance-seg_*.py` for instance segmentation models such as Mask R-CNN.
- TensorRT conversion generally needs a CUDA device.
- Dynamic-shape configs are safer when production input sizes vary.

Converted MMDeploy SDK model directories commonly contain:

```text
deploy.json
detail.json
end2end.onnx
pipeline.json
```

## Backend Model Inference Shape

A typical backend route is:

1. Load deploy config and MMDetection model config with MMDeploy utilities.
2. Build a task processor for the target backend and device.
3. Build the backend model from converted model files such as `end2end.onnx`.
4. Create backend inputs with the configured input shape.
5. Run `model.test_step(...)` under `torch.no_grad()`.
6. Visualize through the task processor to a file, not a GUI, for server use.

## SDK Inference Shape

The MMDeploy SDK route wraps a converted model directory and provides language bindings. In Python, `mmdeploy_python.Detector` accepts a model directory plus device name and id, then returns boxes, labels, and optional masks for an OpenCV image.

Use SDK inference when the target application is not a Python training/research workflow and needs a packaged runtime model.

## TorchServe Overview

Treat TorchServe as a separate service deployment path, not as a drop-in replacement for `DetInferencer`.

Expect to decide and verify:

- model archive structure and handler logic;
- config and checkpoint pairing;
- pre/postprocessing parity with MMDetection test pipeline;
- GPU/CPU container image and CUDA compatibility;
- request/response JSON schema;
- service startup, health checks, batching, and timeout behavior.

Because TorchServe requires external service/container setup, keep runtime skill instructions at the route-selection level unless the user provides a specific serving environment.

## Practical Recommendation

Start with `DetInferencer` for correctness. Move to MMDeploy when latency, backend compatibility, or non-Python embedding is the real requirement. Move to TorchServe only when the requirement is managed HTTP serving rather than local library inference.
