---
name: pytorch-yolo-v3
description: "Route pytorch-yolo-v3 Darknet cfg, image detection, video camera
  demo, preprocessing, NMS, and legacy PyTorch YOLOv3 troubleshooting tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# pytorch-yolo-v3

Use this repo skill when a user is working with the legacy `pytorch-yolo-v3` source repository for PyTorch YOLOv3 object detection: Darknet cfg parsing, local YOLO weights, still-image detection, OpenCV video/camera demos, preprocessing, postprocessing, confidence/NMS behavior, or repository-specific errors.

## First checks

- This is a script-oriented source repository, not an installable package in the inspected baseline. Expect a local user checkout/source tree plus Python dependencies rather than package metadata or console entry points.
- The detector needs local Darknet weights for full inference. Do not download `yolov3.weights` automatically.
- Prefer bundled dry-run or smoke helpers before loading weights, writing detections, opening GUI windows, or touching a camera.
- Training/fine-tuning is out of scope for this baseline; the README says the repository contains the detection module only.

For a safe root preflight, run:

```bash
python scripts/check_environment.py
python scripts/check_environment.py --repo-root <repo-root> --check-files
```

This checks dependencies and optional checkout imports without weights, downloads, GUI, camera, video, or inference.

## Route by task

| User task or signal | Read |
| --- | --- |
| Parse or validate Darknet cfg files; inspect `Darknet`; understand `load_weights`/`save_weights`; debug `Something I dunno`, unsupported `region`/`reorg`, class-count/filter mismatch, or names files | [sub-skills/model-and-config/SKILL.md](sub-skills/model-and-config/SKILL.md) |
| Run still-image or image-directory detection; build a safe detection command; debug preprocessing, `write_results`, confidence/NMS, no detections, output naming, image extension handling, or CPU/CUDA image inference | [sub-skills/image-detection/SKILL.md](sub-skills/image-detection/SKILL.md) |
| Use or debug `video_demo.py`, `cam_demo.py`, or `video_demo_half.py`; handle OpenCV display/camera/video input, half precision, ignored `--video`, or headless-server issues | [sub-skills/video-camera-demos/SKILL.md](sub-skills/video-camera-demos/SKILL.md) |
| Install/import/dependency issues, missing weights, source-checkout assumptions, CUDA expectations, or cross-cutting stop conditions | [references/troubleshooting.md](references/troubleshooting.md) |
| Decide whether this skill is stale for a current checkout | [references/repo-provenance.md](references/repo-provenance.md) |

## Operating workflow

1. Identify the user's intended workflow: cfg/model inspection, image detection, or video/camera demo.
2. Check whether the request requires unsafe or expensive effects: weight download, full inference, output writes, GUI display, webcam/video capture, or checkout modification. Ask before doing those effects.
3. Use the nearest bundled helper in dry-run/smoke mode:
   - `scripts/check_environment.py` for root dependency/import checks.
   - `sub-skills/model-and-config/scripts/inspect_darknet_config.py` for cfg/names/static model compatibility.
   - `sub-skills/image-detection/scripts/check_image_pipeline.py` for no-weight preprocessing/postprocessing checks.
   - `sub-skills/image-detection/scripts/run_image_detection.py` for a validated dry-run launcher around still-image detection.
   - `sub-skills/video-camera-demos/scripts/check_video_demo_args.py` for parser/source checks.
   - `sub-skills/video-camera-demos/scripts/run_video_demo.py` for a validated dry-run launcher around video/camera demos.
4. Only execute full detector/demo commands after the user supplies local inputs and approves side effects.

## Key repository facts

- Core modules: `darknet`, `util`, `preprocess`, and `bbox`.
- Main still-image entrypoint: `detect.py`; the generated skill wraps it through `sub-skills/image-detection/scripts/run_image_detection.py`.
- Video/camera entrypoints: `video_demo.py`, `video_demo_half.py`, and `cam_demo.py`; the generated skill wraps/preflights them through the video-camera sub-skill scripts.
- Supported constructible cfg in the inspected baseline: `cfg/yolov3.cfg`. Other bundled cfgs parse but contain unsupported YOLOv2-style `region` and/or `reorg` blocks.
- Default COCO names file has 80 classes; VOC names file has 20 classes and does not match unmodified `cfg/yolov3.cfg`.
- Input resolution must be greater than 32 and divisible by 32.

## Do not use this skill when

- The user is asking for Ultralytics/YOLOv5/YOLOv8, MMDetection, Detectron2, or another modern detector framework.
- The task is training, fine-tuning, evaluation benchmarking, ONNX/TensorRT export, deployment serving, or dataset labeling unless the user explicitly ties it to this repository and accepts that the baseline skill does not cover it.
- The user only needs generic OpenCV image/video handling without this repository's YOLOv3 scripts, cfgs, weights, or failure modes.
