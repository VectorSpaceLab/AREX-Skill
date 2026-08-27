---
name: inference
description: "Guides YOLOP PyTorch demo inference, checkpoint loading,
  image/video source handling, detection/segmentation postprocessing, and
  visualization troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# YOLOP Inference

Use this sub-skill when the task asks to run YOLOP on images, folders, videos, or streams; load the pretrained `End-to-end.pth` checkpoint; use `hubconf.py`; interpret combined detection/drivable/lane outputs; or debug `tools/demo.py` behavior.

Do not use this sub-skill for full training/evaluation metrics (use `training`), BDD100K layout generation (use `data-preparation`), or ONNXRuntime/TensorRT workflows (use `export`).

## Read first

- [references/workflows.md](references/workflows.md) explains the source demo command, inputs, outputs, preprocessing, NMS, mask overlays, and safe bundled helper.
- [references/model-loading.md](references/model-loading.md) covers `get_net(cfg)`, checkpoint dictionaries, `hubconf.yolop`, and CPU/CUDA device choices.
- [references/troubleshooting.md](references/troubleshooting.md) covers missing weights, unsupported sources, OpenCV/video/camera issues, device errors, and empty detections.
- Run [scripts/run_demo_inference.py](scripts/run_demo_inference.py) for a safer image/folder/video helper with explicit `--repo-root`, `--weights`, `--source`, and `--save-dir`.

## Quick route

```bash
# Source repo command from a YOLOP checkout root
PYTHONPATH=. python tools/demo.py --source inference/images --weights weights/End-to-end.pth --device cpu

# Bundled helper with explicit paths and no checkout-root assumption
python sub-skills/inference/scripts/run_demo_inference.py \
  --repo-root /path/to/YOLOP \
  --weights /path/to/YOLOP/weights/End-to-end.pth \
  --source /path/to/YOLOP/test.jpg \
  --save-dir /tmp/yolop-demo-output \
  --device cpu
```

Use CPU for correctness/debug smokes. Use CUDA only after installing a matching CUDA torch/torchvision pair and verifying device availability.

## Output contract

For every image frame, YOLOP produces:

- Detection boxes after YOLO-style NMS (`xyxy`, confidence, class id).
- Drivable-area segmentation mask, blended green by the demo visualization.
- Lane-line segmentation mask, blended red/blue depending on visualization helper conversion.
- A merged visualization image or video written to the save directory.

## Cross-links

- To validate model architecture before loading weights, use the root `scripts/check_install.py`.
- To export or validate ONNX models, use [../export/SKILL.md](../export/SKILL.md).
- To configure evaluation metrics instead of demo visualization, use [../training/SKILL.md](../training/SKILL.md).
