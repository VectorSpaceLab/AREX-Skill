---
name: inference
description: "Run DAMO-YOLO image, video, and camera inference with Torch, ONNX,
  or TensorRT engines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# inference

Use this sub-skill when the task is to run or troubleshoot DAMO-YOLO demo inference on images, videos, or a live camera, or when the user needs to choose between Torch, ONNX, and TensorRT runtime engines.

## Route here for

- Image, video, and camera demo workflows with a DAMO-YOLO config and an engine artifact.
- Choosing `.pth`/`.pt`, `.onnx`, or `.trt` inference and explaining required optional runtimes.
- Setting `--device`, `--infer_size`, `--conf`, `--end2end`, output/visualization behavior, and class labels.
- Debugging missing OpenCV, Pillow, torchvision, ONNX Runtime, TensorRT/CUDA Python, invalid input media, or class-name mismatch failures.

## Route elsewhere

- Training, finetuning, optimizers, distributed launch, and checkpoint production: use the training sub-skill.
- COCO evaluation loops, metric reproduction, and multi-GPU dataset inference: use evaluation/training integration guidance rather than this demo route.
- ONNX/TensorRT export implementation, converter internals, TensorRT evaluation, and partial quantization: use the deployment sub-skill.

## Start here

1. Read [engine-and-data-flow.md](references/engine-and-data-flow.md) to choose the runtime engine and understand preprocessing, postprocessing, visualization, class names, and device behavior.
2. Read [demo-workflows.md](references/demo-workflows.md) for concrete image/video/camera commands using the bundled safe helper at [scripts/damo_yolo_safe_demo.py](scripts/damo_yolo_safe_demo.py).
3. If you need to understand why a source file was bundled, adapted, or kept reference-only, read [source-decisions.md](references/source-decisions.md).
4. If anything fails, use [troubleshooting.md](references/troubleshooting.md) before changing configs or reinstalling dependencies.

## Fast command templates

Replace the config, engine, and media paths with user-owned files. Use the resolved path to the bundled `scripts/damo_yolo_safe_demo.py` helper. Keep the config matched to the engine checkpoint/export; if the config reads relative TinyNAS structure files, run from the directory that contains those config-relative assets or make paths absolute in the config.

```bash
# Torch checkpoint on an image; falls back to CPU if CUDA is unavailable.
python sub-skills/inference/scripts/damo_yolo_safe_demo.py image \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo_checkpoint.pth \
  --path /path/to/example.jpg \
  --infer-size 640 640 --device cuda --conf 0.6 --output-dir demo

# ONNX engine on a video; requires onnxruntime.
python sub-skills/inference/scripts/damo_yolo_safe_demo.py video \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo.onnx \
  --path /path/to/input.mp4 \
  --infer-size 640 640 --device cuda --conf 0.6 --output-dir demo

# TensorRT engine from a camera; requires TensorRT + CUDA Python and usually CUDA.
python sub-skills/inference/scripts/damo_yolo_safe_demo.py camera \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo_end2end_fp16_bs1.trt \
  --camid 0 --infer-size 640 640 --device cuda --conf 0.6 --end2end --output-dir demo
```

## Option meanings to preserve

- `--conf` is the visualization/display threshold. NMS thresholds come from the config (`model.head.nms_conf_thre`, `model.head.nms_iou_thre`).
- `--infer_size H W` is the resize/pad target used by Torch and TensorRT engines. ONNX engines may derive the target from the ONNX input shape.
- `--end2end` is only for TensorRT engines exported with NMS included; using it on the wrong `.trt` layout changes the expected output tensors.
- Source-style `--save_result` saves visualizations by default. The bundled helper also supports `--no-save-result` and only opens GUI windows when `--show-window` is explicit.
