---
name: model-conversion
description: "Routes Darknet weights, TensorFlow SavedModel, TFLite,
  quantization, and TensorRT conversion workflows for tensorflow-yolov4-tflite."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Conversion

Use this sub-skill when the user needs to convert YOLOv3/YOLOv4 or tiny Darknet
`.weights` files into TensorFlow SavedModel, TFLite, float16/int8 TFLite, or
TF-TRT artifacts with this repository's scripts.

## Before conversion

- Read the root [../../references/compatibility.md](../../references/compatibility.md)
  for TensorFlow 2.3, protobuf, OpenCV, CPU/GPU, and TensorRT compatibility.
- Ensure the target checkout root is the command working directory. The repo's
  config reads relative paths such as `./data/classes/coco.names` at import time.
- Confirm weights provenance and model family: YOLOv4 weights require
  `--model yolov4`; YOLOv3 weights require `--model yolov3`; tiny variants also
  require `--tiny`.
- Decide whether the downstream artifact is ordinary TensorFlow inference,
  TFLite/mobile inference, or TF-TRT. The `save_model.py --framework` value
  changes output tensors and post-processing expectations.

## Main routes

1. **Darknet weights to SavedModel**: read
   [references/workflows.md](references/workflows.md#darknet-weights-to-tensorflow-savedmodel)
   and generate the command with [scripts/plan_conversion.py](scripts/plan_conversion.py).
2. **SavedModel to TFLite**: read
   [references/workflows.md](references/workflows.md#savedmodel-to-tflite)
   for float32, float16, and int8 quantization requirements.
3. **TensorRT / TF-TRT export**: read
   [references/workflows.md](references/workflows.md#savedmodel-to-tf-trt)
   and [references/troubleshooting.md](references/troubleshooting.md#tensorflow-gpu-or-tensorrt-is-not-usable).
4. **Artifact sanity checks**: use the expected outputs in
   [references/cli-reference.md](references/cli-reference.md) before handing an
   artifact to the inference sub-skill.

## Command planner

Run the bundled planner to build safe commands without launching conversion:

```bash
python sub-skills/model-conversion/scripts/plan_conversion.py \
  --task full-tflite \
  --weights data/yolov4.weights \
  --saved-model checkpoints/yolov4-416 \
  --output checkpoints/yolov4-416.tflite \
  --model yolov4 --input-size 416
```

Use `--check-paths` only in a real target checkout when you want the planner to
fail early on missing source weights or representative datasets.

## Handoff to other sub-skills

- After a SavedModel or TFLite model exists, use
  [../inference-evaluation/SKILL.md](../inference-evaluation/SKILL.md) to run
  image/video inference, mAP output generation, or FPS checks.
- If conversion needs a custom dataset or class file, use
  [../training-data/SKILL.md](../training-data/SKILL.md) before changing class
  counts, anchors, or annotation paths.
- For mobile deployment, use
  [../android-deployment/SKILL.md](../android-deployment/SKILL.md) after a
  compatible `.tflite` artifact is produced.

## Stop conditions

Stop and ask the user before downloading large weights, creating a full COCO
representative dataset, installing CUDA/TensorRT, or overwriting existing model
artifacts. Those actions are outside safe planning and can be expensive or
hardware-specific.
