# SDK Workflows

MMDeploy SDK runtime use begins after conversion has produced an **SDK model
package**. The package combines backend artifacts with metadata needed by SDK
preprocessing, inference dispatch, and postprocessing. Runtime APIs are thin
FFI wrappers around that package; they are not raw backend-engine loaders.

## Conversion Handoff And `--dump-info`

The conversion workflow must finish with SDK metadata enabled:

```bash
python <deployment-cli> \
  <deploy-config.py> \
  <model-config.py> \
  <checkpoint.pth> \
  <sample-input> \
  --work-dir <sdk-model-dir> \
  --device <cpu-or-cuda-device> \
  --dump-info
```

The `--work-dir` value becomes the SDK `model_path`. The SDK model path is the
**directory**, not the single backend artifact inside it. If conversion produced
only `end2end.engine`, `end2end.onnx`, `end2end.xml`, or another backend file,
regenerate with `--dump-info` before using `mmdeploy_runtime` task classes.

Expected directory shape is documented in
[Model directory](model-directory.md). The most important runtime files are:

- `deploy.json` — declares SDK task class and backend model file names.
- `pipeline.json` — declares preprocessing, inference, and postprocessing
  pipeline steps.
- `detail.json` — records conversion/config/backend provenance.
- Backend artifacts — for example `.onnx`, `.engine`, `.xml`/`.bin`,
  `.param`/`.bin`, `.dlc`, `.rknn`, `.om`, `.mlpackage`, or TVM library files.

## Python API Pattern

Python SDK demos all follow the same shape: import a task class from
`mmdeploy_runtime`, load an image/video with a normal media library, create the
runtime handle with the SDK model directory and device, then call the handle.

```python
import cv2
from mmdeploy_runtime import Detector

img = cv2.imread('input.jpg')
if img is None:
    raise RuntimeError('failed to load input.jpg')

detector = Detector(model_path='sdk_model_dir', device_name='cuda', device_id=0)
bboxes, labels, masks = detector(img)
```

Constructor argument rules:

- `model_path` is the SDK model directory or zip model, not a raw engine file.
- `device_name` is usually `"cpu"` or `"cuda"`; keep `device_id` numeric.
- Do not pass a converter API `backend_files` list to an SDK task class.
- Choose the task class from the model's SDK task, not from the backend file
  extension.

### Python Demo Task Coverage

| Python demo name | Runtime classes | Notes |
| --- | --- | --- |
| `image_classification.py` | `Classifier` | Single image classification. |
| `object_detection.py` | `Detector` | Bounding boxes, labels, optional masks for instance segmentation. |
| `image_segmentation.py` | `Segmentor` | Pixel mask visualization. |
| `image_restorer.py` | `Restorer` | Super-resolution/restoration output image. |
| `ocr.py` | `TextDetector`, `TextRecognizer` | Text detection and recognition can be used together. |
| `pose_detection.py` | `PoseDetector` | Takes image plus a bounding box. |
| `det_pose.py` | `Detector`, `PoseDetector` | Composite detection then pose estimation. |
| `pose_tracker.py` | `PoseTracker` | Requires detection and pose model directories plus tracker state. |
| `rotated_object_detection.py` | `RotatedDetector` | Rotated boxes. |
| `video_recognition.py` | `VideoRecognizer` | Video frame sampling then action recognition. |
| `pipeline.py` | `Model`, `Device`, `Context`, `Pipeline` | Custom SDK pipeline composition. |

## C API Pattern

The C API has two creation styles:

1. Task-specific convenience constructors such as
   `mmdeploy_classifier_create_by_path(model_path, device_name, device_id,
   &handle)`.
2. Explicit model/context constructors such as `mmdeploy_model_create_by_path`,
   `mmdeploy_context_create_by_device`, and task `*_create_v2` functions. Use
   the explicit style when adding a profiler or other context object.

Minimal classifier-style flow:

```c
mmdeploy_classifier_t classifier{};
int status = mmdeploy_classifier_create_by_path(
    "sdk_model_dir", "cpu", 0, &classifier);
if (status != MMDEPLOY_SUCCESS) {
  /* report the code and stop */
}

mmdeploy_mat_t mat{
    image_data, height, width, 3,
    MMDEPLOY_PIXEL_FORMAT_BGR,
    MMDEPLOY_DATA_TYPE_UINT8};

mmdeploy_classification_t* results{};
int* result_count{};
status = mmdeploy_classifier_apply(classifier, &mat, 1, &results, &result_count);

mmdeploy_classifier_release_result(results, result_count, 1);
mmdeploy_classifier_destroy(classifier);
```

Apply the same lifecycle to detector, segmentor, restorer, text, pose, rotated,
and video recognizer APIs: create, apply, release result buffers, destroy.
Always match the release function to the task family.

## C++ API Pattern

C++ wrappers use RAII-style classes and can attach a `Profiler` through
`Context`:

```cpp
mmdeploy::Context context;
context.Add(mmdeploy::Device{"cuda", 0});

mmdeploy::Model model{"sdk_model_dir"};
mmdeploy::Detector detector{model, context};

auto dets = detector.Apply(image);
```

The examples include single-task wrappers (`Classifier`, `Detector`,
`Segmentor`, `Restorer`, `PoseDetector`, `RotatedDetector`, `VideoRecognizer`),
composite OCR examples, detection-then-pose examples, and `PoseTracker` with a
long-lived tracker state.

## Java And C# Patterns

Java and C# wrappers mirror the task-class model:

- Java demo classes: `ImageClassification`, `ObjectDetection`,
  `ImageSegmentation`, `ImageRestorer`, `Ocr`, `PoseDetection`, `PoseTracker`,
  and `RotatedDetection`.
- C# demo projects: image classification, object detection, image segmentation,
  image restoration, OCR detection/recognition, pose detection, pose tracker,
  and rotated detection.

Both language families require the runtime native libraries and their backend
libraries on the system library path. Build-tool failures are usually not model
errors: Java uses Ant and generated Java SDK classes; C# uses a local or
prebuilt NuGet package plus runtime DLL discovery.

## FFI Task Mapping

| SDK task | Python class | C API prefix | C++ class | Typical demo languages |
| --- | --- | --- | --- | --- |
| Classification | `Classifier` | `mmdeploy_classifier_*` | `mmdeploy::Classifier` | Python, C, C++, Java, C# |
| Object detection | `Detector` | `mmdeploy_detector_*` | `mmdeploy::Detector` | Python, C, C++, Java, C# |
| Instance segmentation | `Detector` | `mmdeploy_detector_*` | `mmdeploy::Detector` | Python, C/C++ detector demos with masks |
| Semantic segmentation | `Segmentor` | `mmdeploy_segmentor_*` | `mmdeploy::Segmentor` | Python, C, C++, Java, C# |
| Super-resolution / restoration | `Restorer` | `mmdeploy_restorer_*` | `mmdeploy::Restorer` | Python, C, C++, Java, C# |
| Text detection | `TextDetector` | `mmdeploy_text_detector_*` | `mmdeploy::TextDetector` | Python, C OCR, C++ OCR, Java, C# |
| Text recognition | `TextRecognizer` | `mmdeploy_text_recognizer_*` | `mmdeploy::TextRecognizer` | Python OCR and combined OCR demos |
| Pose detection | `PoseDetector` | `mmdeploy_pose_detector_*` | `mmdeploy::PoseDetector` | Python, C, C++, Java, C# |
| Rotated detection | `RotatedDetector` | `mmdeploy_rotated_detector_*` | `mmdeploy::RotatedDetector` | Python, C, C++, Java, C# |
| Video recognition | `VideoRecognizer` | `mmdeploy_video_recognizer_*` | `mmdeploy::VideoRecognizer` | Python, C, C++ |
| Pose tracking | `PoseTracker` | task-specific tracker APIs | `mmdeploy::PoseTracker` | Python, C++, Java, C# |
| Custom pipeline | `Pipeline`, `Model`, `Device`, `Context` | pipeline APIs | pipeline/context classes | Python and C API patterns |

If the task class is not present in the installed runtime package, stop and
check whether the package was built with the required SDK task and language API.
Do not emulate missing task postprocessing by feeding raw backend tensors unless
the user explicitly wants to build a custom runtime outside this SDK route.
