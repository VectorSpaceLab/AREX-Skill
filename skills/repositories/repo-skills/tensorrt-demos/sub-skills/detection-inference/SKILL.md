---
name: "detection-inference"
description: "Run and troubleshoot the repository's TensorRT YOLOv3/YOLOv4 and
  UFF SSD object-detection demos across files, streams, cameras, asynchronous
  pipelines, visualization, and MJPEG output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TensorRT detection inference

Use this skill when the task is to run, adapt, or diagnose the repository's
YOLOv3/YOLOv4 or UFF SSD inference examples. It covers the inference and
presentation path only; engine conversion, model downloads, training, and mAP
evaluation are outside this skill. Keep experiment logs and review artifacts
outside this runtime skill directory.

## Applicability and hard gates

- **YOLO:** `TrtYOLO` consumes a serialized engine named by the model under the
  runtime's `yolo/` artifact directory and loads the `yolo_layer` TensorRT
  plugin before constructing CUDA buffers. The model string describes a
  YOLOv3/YOLOv4 family and input size, for example `yolov4-416` or
  `yolov3-tiny-288`; custom names are possible if their engine and class count
  match. The plugin is not bundled here and must be built/provided by the
  runtime owner.
- **SSD:** `TrtSSD` consumes a serialized UFF-derived engine under the runtime's
  `ssd/` artifact directory. The demo's supported model names are
  `ssd_mobilenet_v1_coco`, `ssd_mobilenet_v1_egohands`,
  `ssd_mobilenet_v2_coco`, `ssd_mobilenet_v2_egohands`,
  `ssd_inception_v2_coco`, and `ssdlite_mobilenet_v2_coco`.
- Both paths require a working TensorRT Python API, CUDA/PyCUDA context, and
  OpenCV. An input parser or this skill's argument checker cannot prove that an
  engine, plugin, camera, decoder, or CUDA device is usable.
- The evidence is historical repository behavior. The README reports YOLO
  inference with the custom plugin from TensorRT 6+ and UFF SSD with the
  TensorRT Python API from TensorRT 5.x+; it also reports tested Jetson Nano,
  TX2, Xavier NX, and selected x86 NVIDIA systems. Do not infer modern-stack
  compatibility from those claims.
- Stop and preserve the exact error when a modern TensorRT/PyCUDA/OpenCV stack
  cannot deserialize a legacy engine or load its plugin. Do not copy a binary,
  installer, engine, or shared library into this skill.

## Fast routing

1. Identify the detector and its engine artifact before choosing an input.
2. Validate exactly one input mode with the bundled dependency-free checker:

   ```bash
   python3 scripts/validate-input-mode.py --detector yolo \
     --model yolov4-416 --image /path/to/image.jpg
   ```

   The checker validates only command arguments; it does not read the image,
   open a device, import TensorRT, or check an engine/plugin.
3. Run the matching native demo from its normal demo runtime environment. The
   native entrypoints import CUDA/TensorRT before argparse help can execute, so
   `--help` is a dependency smoke check rather than a pure parser check.
4. If the display is not needed, use a video-writer or MJPEG variant rather
   than removing inference code. Record detector, model, input mode, input
   dimensions, confidence threshold, letterbox mode, and TensorRT version.

See [references/workflows.md](references/workflows.md) for complete recipes,
[references/api-reference.md](references/api-reference.md) for contracts, and
[references/troubleshooting.md](references/troubleshooting.md) for failure
classification.

## Native entrypoints and detector contracts

### YOLOv3/YOLOv4 — `TrtYOLO`

- The interactive entrypoint accepts `--model` (required), `--category_num`
  (default 80), `--conf_thresh` (default 0.3), and `--letter_box`.
- `TrtYOLO.detect(img, conf_th=0.3, letter_box=None)` accepts a BGR `uint8`
  image shaped `(height, width, 3)` and returns `(boxes, scores, classes)`.
  Boxes are integer `(x1, y1, x2, y2)` corners clipped to the original image;
  scores are confidence products; classes are numeric class IDs.
- Preprocessing resizes to the engine input, converts BGR to RGB, transposes
  to CHW, and scales to `[0, 1]`. Letterbox mode preserves aspect ratio with
  gray padding and reverses the offset during postprocessing; use it only when
  the engine/task expects that behavior.
- Postprocessing concatenates the plugin outputs, filters on
  `box_confidence * class_probability >= conf_th`, applies per-class NMS at
  IoU 0.5, maps coordinates back to the source image, and clips them. A
  non-positive category count is rejected by the interactive entrypoint.
- The code selects `execute_async` for TensorRT versions before 7 and
  `execute_async_v2` for TensorRT 7+, while buffer allocation distinguishes
  implicit and explicit batch dimensions. This is a compatibility clue, not a
  guarantee for current TensorRT APIs.

### UFF SSD — `TrtSSD`

- `trt_ssd.py` selects one of the six model names above and uses a fixed
  `(300, 300)` input. Its interactive loop uses confidence `0.3`; the class API
  exposes `detect(img, conf_th=0.3)` for another threshold.
- SSD preprocessing resizes BGR to 300x300, converts to RGB, changes HWC to
  CHW, scales to `[-1, 1]`, and runs the serialized UFF/TensorRT engine.
- SSD postprocessing reads seven-value detection records, ignores records
  below `conf_th`, scales normalized `(xmin, ymin, xmax, ymax)` to the original
  image, and returns corner boxes, confidences, and integer classes.
- The loader registers TensorRT plugins and, for TensorRT versions before 7,
  loads the legacy FlattenConcat shared library. A warning such as
  `Could not register plugin creator: FlattenConcat_TRT` is a known historical
  TensorRT 6-era observation in the README; treat it as a compatibility
  signal and verify actual deserialization/inference rather than suppressing
  it.

## Input modes and frame ownership

The shared camera layer supports these modes. Pass one, not several; its
implementation resolves them in this order: image, video, RTSP, USB, custom
GStreamer, onboard camera.

| Mode | Native arguments | Behavior and important options |
|---|---|---|
| Image | `--image FILE` | Reads one image and repeats a copy on every `read()`. `--do_resize` resizes it to `--width`/`--height`. |
| Video | `--video FILE` | Reads sequentially with OpenCV. `--video_looping` reopens it at EOF; `--do_resize` resizes frames. |
| RTSP | `--rtsp URI` | Builds an H.264 GStreamer pipeline, with `--rtsp_latency` in milliseconds (default 200). Requires an available `omxh264dec` or `avdec_h264`. |
| USB | `--usb N` | Opens `/dev/videoN`; the historical default uses a GStreamer `v4l2src` pipeline at the requested `--width`/`--height`. |
| GStreamer | `--gstr STRING` | Opens a caller-supplied GStreamer string and formats `{width}` and `{height}` placeholders. |
| Onboard | `--onboard N` | Opens the Jetson onboard camera via the available legacy `nvcamerasrc` or `nvarguscamerasrc` pipeline; the selector value is not used to choose a sensor in this implementation. |

`--width` and `--height` default to 640x480. For RTSP, USB, GStreamer, and
onboard sources they become pipeline dimensions; for image/video they affect
resizing only when `--do_resize` is set. Live sources use a background grab
thread. `Camera.read()` returns a shared live frame by default, so detection
code that draws in place can feed its overlay back into the next inference.
Use `--copy_frame` for live sources when inference/display can outpace frame
arrival or when the frame is modified in place. Image reads are already copied.

## Async pipeline and CUDA context

`trt_ssd_async.py` is a producer/consumer pipeline, not a generic async API:

1. The main thread opens `Camera`, initializes the PyCUDA driver, and creates a
   condition variable.
2. A child `TrtThread` creates its CUDA context **inside the child thread**,
   constructs `TrtSSD`, reads frames, calls `detect`, stores the latest image
   and result tuple in shared variables, and notifies the main thread.
3. The main thread waits up to 20 seconds, draws boxes/FPS, displays the frame,
   and stops/join the child on exit.

Preserve this context ownership rule when adapting the pipeline. A timeout is
an actionable capture/inference/CUDA-thread failure, not an empty detection.
The shared-slot design favors the newest result and can drop intermediate
frames; it does not provide ordered delivery or backpressure. The YOLO
interactive and MJPEG examples are synchronous loops. `trt_yolo_cv.py` is a
synchronous file-to-file writer and uses a fixed 0.3 confidence threshold.

## Visualization and network output

`BBoxVisualization.draw_bboxes(img, boxes, confs, clss)` draws each corner box
in a deterministic per-class color and labels it with the class name and
confidence to two decimal places. `show_fps` overlays an exponentially
smoothed FPS value in the interactive loops. `open_window` creates a resizable
OpenCV window; ESC exits and F toggles fullscreen. Drawing mutates the image
in place, which is why `--copy_frame` matters for live camera sources.

`trt_yolo_mjpeg.py` uses the same YOLO detector and camera arguments, draws
boxes/FPS, and sends each frame to `MjpegServer` (default port 8080). The
server publishes multipart JPEG at `/mjpg` or `/`, keeps a queue of at most two
frames, and drops a frame when the queue is full. It is an unauthenticated
HTTP stream: bind it only on a trusted interface/network, choose a permitted
port, and shut it down in `finally`. A disconnected client can produce a
broken-pipe path that the handler intentionally ignores.

## Evidence basis

This operating contract is distilled from `README.md`, the `trt_yolo.py`,
`trt_yolo_cv.py`, `trt_yolo_mjpeg.py`, `trt_ssd.py`, and `trt_ssd_async.py`
entrypoints, and the implementation modules `utils/camera.py`,
`utils/display.py`, `utils/visualization.py`, `utils/yolo_with_plugins.py`,
`utils/ssd.py`, and `utils/mjpeg.py`. The README's Jetson/TensorRT version
notes and benchmark values are historical observations; source behavior and
limits take precedence over undocumented assumptions. No source checkout path,
engine, plugin, model, binary, or installer is part of this skill.

## Verification and limits

Use the bundled checker first, then run native help candidates and record
whether the failure is parser, dependency, backend, plugin, artifact, or input:

```bash
python3 scripts/validate-input-mode.py --help
python3 scripts/validate-input-mode.py --detector yolo --model yolov4-416 \
  --image /path/to/image.jpg
python3 scripts/validate-input-mode.py --detector ssd \
  --model ssd_mobilenet_v1_coco --video /path/to/video.mp4
```

The planned native candidates are `trt_yolo.py --help` and `trt_ssd.py --help`.
On a host without PyCUDA, they fail before argparse with `ModuleNotFoundError`;
that is an environment gate, not evidence that the flags are invalid. On a
host with imports but without the legacy plugin, YOLO can fail while importing
`yolo_with_plugins.py`. The observed repository limits include TensorRT 6+
for the YOLO plugin, TensorRT 5.x+ and legacy UFF/TensorFlow-era tooling for
SSD, and a README-reported TensorRT 6 FlattenConcat plugin registration issue.
Modern TensorRT, CUDA, Python, GStreamer, or OpenCV behavior must be verified
on the target rather than extrapolated from historical JetPack results.
