# Android Deployment Troubleshooting

## App cannot find the model asset

**Symptoms**

- Classifier initialization throws an `IOException`.
- Toast says `Classifier could not be initialized`.
- Android log mentions the expected `.tflite` asset is missing.

**Recovery**

- Check that the target app assets directory contains the exact filename used by
  `TF_OD_API_MODEL_FILE` in both `MainActivity` and `DetectorActivity`.
- Run the bundled asset checker against the target app.
- Ensure Gradle does not overwrite or replace assets with the download task.

## Labels do not match detections

**Symptoms**

- Boxes draw but labels are wrong.
- Class index errors or unexpected class names.
- Custom model predicts classes outside the label-file range.

**Recovery**

1. Count label file lines and compare with the model's output class count.
2. Keep label order identical to the training/conversion class file.
3. Update `TF_OD_API_LABELS_FILE` when changing from `coco.txt` to another asset.
4. Revalidate the same `.tflite` file in Python before blaming Android drawing.

## GPU delegate crashes or app is slow

**Cause**: `YoloV4Classifier` enables GPU delegate by default (`isGPU = true`) and
uses TFLite GPU 2.2.0. Device support varies, especially for select TF ops,
custom ops, or quantized models.

**Recovery**

- Set `isGPU = false` in the target checkout to confirm CPU inference works.
- Try NNAPI only after checking Android version and op support.
- Prefer float32/float16 artifacts before int8 when debugging delegate issues.
- Record device model, Android version, TFLite dependency version, and model
  precision when reporting mobile performance.

## Tiny or custom-size model fails

**Cause**: The Android constants are hard-coded for YOLOv4 full 416x416 by
default. Tiny constants exist, but `isTiny` is false and activity constants still
expect 416 input.

**Recovery**

- Update classifier full/tiny toggle and output width/mask/anchor/XY scale
  constants to match the converted model.
- Update `TF_OD_API_INPUT_SIZE` in both activities when using a non-416 model.
- Validate output tensor shapes with Python TFLite interpreter and mirror those
  shapes in Java post-processing.

## Gradle downloads an unrelated model

**Symptom**: Build logs download a `coco_ssd_mobilenet` zip, or assets after the
build do not match expected YOLO files.

**Cause**: `build.gradle` applies `download_model.gradle`, which downloads a
TensorFlow Lite MobileNet example model by default.

**Recovery**

- Comment out or modify the download task in the user's target checkout when
  shipping a custom YOLO asset.
- Keep `aaptOptions { noCompress "tflite" }`.
- Re-run the asset checker after building.

## Android build tooling is unavailable

**Recovery**

- Do not install Android SDK/Gradle dependencies without user approval.
- First complete static asset/constant validation.
- If the user approves a build, record the Android SDK, Gradle plugin, device or
  emulator, and any dependency updates needed for modern Android tooling.
