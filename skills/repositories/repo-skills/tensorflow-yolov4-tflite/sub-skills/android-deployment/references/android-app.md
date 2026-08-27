# Android App Reference

This reference distills the Android app source into the facts future agents need
when adapting a target checkout. It does not require copying the construction
checkout's Android files.

## Gradle and SDK facts

The app module uses:

- Android application plugin plus `de.undercouch.download`.
- `compileSdkVersion 28`, `buildToolsVersion '28.0.3'`, `minSdkVersion 21`,
  `targetSdkVersion 28`.
- Java 1.8 source/target compatibility.
- `aaptOptions { noCompress "tflite" }` so TFLite assets are not compressed.
- TensorFlow Lite dependencies:
  - `org.tensorflow:tensorflow-lite:2.2.0`
  - `org.tensorflow:tensorflow-lite-gpu:2.2.0`

The app applies `download_model.gradle`. That task downloads a default TensorFlow
Lite SSD MobileNet zip from Google storage during assemble tasks. If the user is
shipping a custom YOLOv4 TFLite asset, review this task so it does not overwrite
or confuse assets.

## Default assets and Java constants

The verified snapshot contains these relevant app assets:

- `yolov4-416-fp32.tflite`
- `coco.txt`
- `labelmap.txt`
- `kite.jpg`

`MainActivity` and `DetectorActivity` both define:

```java
private static final int TF_OD_API_INPUT_SIZE = 416;
private static final String TF_OD_API_MODEL_FILE = "yolov4-416-fp32.tflite";
private static final String TF_OD_API_LABELS_FILE = "file:///android_asset/coco.txt";
private static final float MINIMUM_CONFIDENCE_TF_OD_API = 0.5f;
```

When replacing model or labels, update both activities or centralize constants in
the target project. The model's class count and output order must match the label
file.

## `YoloV4Classifier` constants

The classifier uses YOLOv4 full-model defaults:

- `INPUT_SIZE = 416`
- `OUTPUT_WIDTH = {52, 26, 13}`
- `MASKS = {{0, 1, 2}, {3, 4, 5}, {6, 7, 8}}`
- `ANCHORS = {12,16, 19,36, 40,28, 36,75, 76,55, 72,146, 142,110, 192,243, 459,401}`
- `XYSCALE = {1.2f, 1.1f, 1.05f}`
- `NUM_THREADS = 4`
- `isGPU = true`
- `isNNAPI = false`
- `isTiny = false`

Tiny constants exist in the source (`OUTPUT_WIDTH_TINY`, `MASKS_TINY`,
`ANCHORS_TINY`, `XYSCALE_TINY`), but `isTiny` is false by default. A tiny model
asset needs code changes and validation, not only a filename change.

## Input preprocessing and post-processing

- `convertBitmapToByteBuffer` writes RGB float values normalized by 255.0 for
  non-quantized models.
- `YoloV4Classifier.create` accepts `isQuantized`, but the default Java constants
  set quantized false.
- GPU delegate is added when `isGPU` is true; NNAPI delegate is only configured
  on Android P or newer when `isNNAPI` is true.
- NMS uses `mNmsThresh = 0.6f`; `MainActivity` uses confidence threshold 0.5.

## Mobile validation checklist

1. Validate the `.tflite` artifact in Python with a known image.
2. Confirm Java `TF_OD_API_INPUT_SIZE` matches conversion input size.
3. Confirm the asset model filename matches both `MainActivity` and
   `DetectorActivity`.
4. Confirm label file line count equals model class count.
5. Confirm full/tiny constants match the model output layout.
6. Disable or review the Gradle download task if it fetches unrelated models.
7. Test CPU first if GPU delegate crashes; then re-enable GPU/NNAPI deliberately.
