---
name: inference-evaluation
description: "Routes image/video detection, TFLite inference, mAP evaluation,
  and FPS benchmarking workflows for tensorflow-yolov4-tflite."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference and Evaluation

Use this sub-skill when the user has a TensorFlow SavedModel, TFLite model, or
TF-TRT SavedModel from this repository and wants to run image detection, video
detection, COCO mAP output generation, or FPS benchmarking.

## Before running inference

- If the model artifact does not exist yet, route to
  [../model-conversion/SKILL.md](../model-conversion/SKILL.md).
- Confirm that `--framework`, `--model`, `--tiny`, and `--size` match the
  artifact produced during conversion.
- Run commands from the target checkout root because the repo uses relative
  config/data paths at import time.
- Treat image/video/model/dataset paths as user-provided runtime inputs. Do not
  download weights or COCO data unless the user explicitly approves.

## Main routes

1. **Image detection**: read
   [references/workflows.md](references/workflows.md#image-detection) and use
   [scripts/plan_inference.py](scripts/plan_inference.py) to build a checked
   `detect.py` command.
2. **Video detection**: read
   [references/workflows.md](references/workflows.md#video-detection) before
   using `detectvideo.py`, especially on headless machines.
3. **TFLite inference**: read
   [references/workflows.md](references/workflows.md#tflite-inference) for
   output order and model/tiny caveats.
4. **mAP evaluation**: read
   [references/workflows.md](references/workflows.md#map-evaluation) because
   the source script deletes/recreates output directories and has a config-path
   trap.
5. **FPS benchmarking**: read
   [references/workflows.md](references/workflows.md#fps-benchmarking) and
   verify that the user's backend claim matches the actual environment.

## Command planner

Example image-detection plan:

```bash
python sub-skills/inference-evaluation/scripts/plan_inference.py \
  --action detect-image \
  --framework tf \
  --weights checkpoints/yolov4-416 \
  --input data/kite.jpg \
  --output result.png \
  --model yolov4 --size 416
```

Example TFLite plan:

```bash
python sub-skills/inference-evaluation/scripts/plan_inference.py \
  --action detect-image \
  --framework tflite \
  --weights checkpoints/yolov4-416.tflite \
  --input data/kite.jpg \
  --output result-tflite.png \
  --model yolov4 --size 416
```

Add `--check-paths` when operating inside a real target checkout and you want
missing model/input/annotation files to fail before launching TensorFlow.

## Output checks

- Image detection should write the `--output` image and draw boxes through
  `core.utils.draw_bbox`.
- Video detection writes `--output` only when that flag is supplied; otherwise
  it opens an OpenCV UI window unless disabled.
- Evaluation writes text files under `mAP/predicted` and `mAP/ground-truth`,
  then the mAP tool reads those directories.
- Benchmarking prints per-iteration time, average FPS, and instantaneous FPS;
  discard the first warmup iteration when interpreting results.

## Troubleshooting

Use [references/troubleshooting.md](references/troubleshooting.md) for missing
model files, blank OpenCV inputs, TFLite output-order confusion, mAP directory
side effects, annotation path mismatch, GPU/TensorRT benchmark claims, and
headless display failures.
