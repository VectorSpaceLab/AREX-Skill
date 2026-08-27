---
name: tensorflow-yolov4-tflite
description: "Guides TensorFlow YOLOv3/YOLOv4 conversion, inference, training
  data, evaluation, TensorRT, and Android TFLite workflows for
  hunglc007/tensorflow-yolov4-tflite."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tensorflow-yolov4-tflite

Use this repo skill when the user needs operational guidance for the
`hunglc007/tensorflow-yolov4-tflite` project: YOLOv3/YOLOv4 and tiny variants
implemented in TensorFlow 2, Darknet `.weights` conversion to SavedModel,
TFLite or TF-TRT export, image/video detection, COCO/VOC annotation preparation,
training, mAP/FPS checks, or the bundled Android TFLite demo.

## First checks

1. Confirm the user is working with a target checkout of this repository or a
   project copied from it. The source scripts use repository-relative paths such
   as `./data/classes/coco.names`; run commands from the target checkout root or
   pass absolute paths where a flag supports them.
2. Read [references/repo-provenance.md](references/repo-provenance.md) when
   checking whether this skill matches a checkout before refreshing it.
3. Read [references/compatibility.md](references/compatibility.md) before
   installing dependencies. The upstream pins are old: TensorFlow 2.3 era,
   Python 3.8 is the safest reconstruction target, modern protobuf must often
   be pinned below 3.20, and GPU/TensorRT needs a matching CUDA 10.x-era stack.
4. Run [scripts/check_environment.py](scripts/check_environment.py) against the
   user's target checkout for a non-destructive import/config/backend probe.

Minimal environment probe after installation:

```bash
python - <<'PY'
import tensorflow as tf, cv2
from core.config import cfg
from core import utils
print("tensorflow", tf.__version__)
print("opencv", cv2.__version__)
print("class_file", cfg.YOLO.CLASSES)
print("classes", len(utils.read_class_names(cfg.YOLO.CLASSES)))
print("gpus", tf.config.experimental.list_physical_devices("GPU"))
PY
```

If this fails, go to [references/troubleshooting.md](references/troubleshooting.md)
before changing the task plan.

## Route by task

- **Convert models or export formats**: use
  [sub-skills/model-conversion/SKILL.md](sub-skills/model-conversion/SKILL.md)
  for Darknet `.weights` to TensorFlow SavedModel, TFLite float32/float16/int8,
  TF-TRT conversion, supported flags, artifact checks, and conversion failures.
- **Run detection, evaluation, or benchmarks**: use
  [sub-skills/inference-evaluation/SKILL.md](sub-skills/inference-evaluation/SKILL.md)
  for image/video inference, TFLite inference, mAP file generation, FPS tests,
  thresholds, output files, and post-processing checks.
- **Prepare data or train**: use
  [sub-skills/training-data/SKILL.md](sub-skills/training-data/SKILL.md) for
  COCO/VOC annotation formats, class/anchor config, dataset validation, training
  stages, freeze layers, checkpoints, and dataset-related errors.
- **Use the Android demo**: use
  [sub-skills/android-deployment/SKILL.md](sub-skills/android-deployment/SKILL.md)
  for TFLite asset placement, Gradle/TFLite versions, YOLOv4 classifier
  constants, GPU/NNAPI delegate choices, and Android build/run troubleshooting.

## Repo operating model

- This is a script-style repository, not an installable Python distribution.
  Future agents should install the dependencies in an isolated environment and
  add the target checkout root to `PYTHONPATH` when running scripts from another
  working directory.
- `core.config.cfg` owns the default class file, anchors, strides, train/test
  annotation paths, thresholds, image size, batch size, and epoch counts.
- The main Python entry points are `save_model.py`, `convert_tflite.py`,
  `convert_trt.py`, `detect.py`, `detectvideo.py`, `evaluate.py`,
  `benchmarks.py`, and `train.py`. The sub-skills distill their flags and safe
  command-building steps; do not assume a command is safe to run until weights,
  datasets, output paths, and backend requirements are checked.
- Full YOLOv4 weights, COCO datasets, TensorRT conversion, Android builds, and
  training are network-, data-, hardware-, or time-intensive. Treat them as
  explicit user-approved actions, not default verification steps.

## Bundled helpers

- [scripts/check_environment.py](scripts/check_environment.py): safe environment
  and target-checkout probe shared by all workflows.
- [sub-skills/model-conversion/scripts/plan_conversion.py](sub-skills/model-conversion/scripts/plan_conversion.py):
  generates conversion command plans without running TensorFlow conversion.
- [sub-skills/inference-evaluation/scripts/plan_inference.py](sub-skills/inference-evaluation/scripts/plan_inference.py):
  generates inference/evaluation/benchmark command plans and validates common
  option combinations.
- [sub-skills/training-data/scripts/validate_annotation_line.py](sub-skills/training-data/scripts/validate_annotation_line.py):
  validates converted COCO/VOC annotation-line syntax using tiny examples.
- [sub-skills/android-deployment/scripts/check_android_assets.py](sub-skills/android-deployment/scripts/check_android_assets.py):
  checks Android asset naming, labels, and model-file presence for a target app.

## Do not use this skill when

- The user is asking about a different YOLO implementation such as Darknet,
  Ultralytics, MMDetection, YOLOP, or DeepStream-Yolo and does not need this
  repository's TensorFlow/TFLite scripts.
- The task is only generic object-detection theory, annotation labeling policy,
  or Android camera app development unrelated to this repo's TFLite assets.
- The user wants Creator-mode skill production or refresh work; route that to
  the appropriate Creator workflow instead of using this operating skill.
