---
name: android-deployment
description: "Routes Android TFLite asset, Gradle, classifier, GPU delegate, and
  mobile YOLOv4 deployment workflows for tensorflow-yolov4-tflite."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Android Deployment

Use this sub-skill when the user wants to run or adapt the repository's Android
TFLite demo, replace the `.tflite` asset, update labels, reason about the
`YoloV4Classifier` constants, or troubleshoot Gradle/TFLite delegate issues.

## Before Android work

- Produce and validate a TFLite model through
  [../model-conversion/SKILL.md](../model-conversion/SKILL.md) before replacing
  Android assets.
- Verify the model with Python TFLite inference before debugging Android UI or
  camera code.
- Read [references/android-app.md](references/android-app.md) for Gradle,
  asset, classifier, and delegate facts distilled from the app source.
- Use [scripts/check_android_assets.py](scripts/check_android_assets.py) to
  check model/label asset names and class-count consistency in a target app.

## Main routes

1. **Replace the bundled model**: confirm the asset filename expected by
   `MainActivity` and `DetectorActivity`, copy the validated `.tflite` into the
   app assets directory of the user's target checkout, then run the asset checker.
2. **Update labels/classes**: replace `coco.txt` or change the Java constants so
   the classifier reads the intended label file; class order must match the
   TFLite model output.
3. **Choose delegates**: inspect `YoloV4Classifier` constants for GPU/NNAPI; GPU
   delegate is enabled by source default, NNAPI is disabled.
4. **Build/run the app**: verify Android SDK/Gradle compatibility and be aware
   that the source Gradle file applies a model-download task that fetches a
   default MobileNet zip unless changed.

## Asset checker examples

```bash
python sub-skills/android-deployment/scripts/check_android_assets.py \
  --android-root android \
  --model yolov4-416-fp32.tflite \
  --labels coco.txt \
  --expected-classes 80
```

Use `--assets-dir` instead of `--android-root` if the user has copied the app
layout into another project.

## Handoff to other sub-skills

- If the `.tflite` model is missing or mismatched, return to
  [../model-conversion/SKILL.md](../model-conversion/SKILL.md).
- If Android detections disagree with Python results, compare against
  [../inference-evaluation/SKILL.md](../inference-evaluation/SKILL.md) using the
  same input image, model file, class labels, input size, and thresholds.
- If class IDs are out of range, use
  [../training-data/SKILL.md](../training-data/SKILL.md) to validate the class
  file and data/model class count.

## Stop conditions

Stop before installing Android SDKs, downloading Gradle dependencies, running a
camera app on a device, or replacing production mobile assets unless the user
approves the target project and overwrite policy.
