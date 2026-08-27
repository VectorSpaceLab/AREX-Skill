---
name: inference
description: "Run YOLOv3 inference through detect.py, PyTorch Hub, and
  DetectMultiBackend with correct sources, weights, labels, and outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Inference Sub-skill

Read this when the task involves `detect.py`, PyTorch Hub, `hubconf.py`, `DetectMultiBackend`, image/video/stream sources, custom weights, saved labels, crops, class filtering, confidence thresholds, NMS, or inference troubleshooting.

## Use

- For CLI detection workflows, read `references/workflows.md` and use `scripts/yolov3_inference_smoke.py` for a deterministic local model probe before weight downloads.
- For Python/PyTorch Hub loading, read `references/api-reference.md` and use `scripts/yolov3_hub_smoke.py` with `--no-pretrained` for offline checks.
- For inference failures, read `references/troubleshooting.md`.

## Important facts

- Official model names are `yolov3`, `yolov3-spp`, and `yolov3-tiny`; PyTorch Hub functions are `yolov3`, `yolov3_spp`, `yolov3_tiny`, and `custom`.
- `detect.py --weights yolov3-tiny.pt` may download release weights when absent.
- `--save-txt` writes normalized YOLO label text; add `--save-conf` for confidences and `--save-crop` for crops.
- Use `--device cpu` for portable correctness smokes; use CUDA only after verifying the target environment.
