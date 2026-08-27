# Detection troubleshooting

Classify the first failing layer and preserve the complete stderr. Do not hide
a legacy-stack failure by changing imports or copying a prebuilt artifact.

## Import and version gates

### `ModuleNotFoundError: pycuda`, `tensorrt`, or `cv2`

The native demos import these packages before parsing command-line arguments.
Install or activate the target's supported runtime according to its own
provisioning policy, then rerun the planned `--help` check. Do not conclude
that CLI arguments, cameras, or engines are invalid from this error. If the
host is modern Python/TensorRT and no compatible legacy environment exists,
report the environment as blocked.

### Legacy TensorRT API errors

The source explicitly branches between TensorRT pre-7 and 7+ execution APIs
and buffer layouts. YOLO's plugin implementation is based on the historical
`IPluginV2IOExt` path and the README states TensorRT 6+; SSD uses the older UFF
and binding APIs and the README states TensorRT Python API 5.x+. A current
TensorRT release may remove or alter these APIs. Do not patch the skill's
observed contract into a claim of modern support; isolate a compatible target
or record a modernization task separately.

## Plugin and engine failures

### YOLO `failed to load ./plugins/libyolo_layer.so`

The YOLO utility loads the plugin at import time. Verify, in the target runtime,
that the plugin was built for the same architecture, CUDA, and TensorRT ABI,
and that the process working directory resolves the expected relative plugin
path. Also verify the serialized engine belongs to the same plugin/model
configuration. This skill does not build, download, or bundle the `.so`.

### TensorRT cannot deserialize `yolo/<model>.trt`

Check the exact model string, engine path, GPU architecture, TensorRT version,
plugin availability, and whether the engine was built with a compatible
precision/profile. An engine is not portable merely because its filename is
recognized. Keep the engine outside this skill and rebuild only under the
runtime owner's approved conversion workflow.

### SSD `FlattenConcat_TRT` registration message

The README reports this TensorRT 6/JetPack-4.3 message:

```text
[TensorRT] ERROR: Could not register plugin creator: FlattenConcat_TRT in namespace
```

It was described there as a known issue that could probably be ignored, but
that is not a general suppression rule. Check whether the engine actually
loads and inference produces valid records. If deserialization or output shape
fails, classify it as a plugin/ABI incompatibility. For pre-7 TensorRT, the
SSD utility attempts to load the legacy `ssd/libflattenconcat.so` before
initializing TensorRT plugins; verify the matching library in the target
runtime without copying it here.

### `fail to allocate CUDA resources`

This wraps TensorRT context/buffer setup. Check CUDA device visibility, free
memory, engine binding dimensions, PyCUDA context ownership, and TensorRT
version. For async SSD, create the CUDA context in the worker thread that calls
CUDA, as the source does; constructing it only in the parent can fail.

## Input and capture failures

### `no camera type specified!` or `failed to open camera!`

Pass exactly one input selector. The safe checker rejects none or multiple
selectors. For files, confirm the path in the target environment. For USB,
verify `/dev/videoN`, permissions, supported pixel format, and whether the
historical GStreamer path should be disabled for that host. For RTSP, check
URI credentials/network reachability, H.264 payload, GStreamer availability,
latency, and decoder presence. For onboard camera, confirm the Jetson camera
stack and whether `nvcamerasrc` or `nvarguscamerasrc` exists. For `--gstr`,
ensure the string is valid and its `{width}`/`{height}` placeholders are
intentional.

### `H.264 decoder not found!` or onboard source not found

`camera.py` probes `gst-inspect-1.0` for historical `omxh264dec` or
`avdec_h264`, and for onboard sources probes `nvcamerasrc` or
`nvarguscamerasrc`. Those elements are platform/version dependent. Install or
select a target-supported pipeline outside this skill, or mark the source
mode unavailable; do not silently substitute a different decoder and claim
repository equivalence.

### Blank/stale/altered detections on live video

The camera grabber reuses a shared frame. Visualization draws in place. Use
`--copy_frame` for live USB, RTSP, GStreamer, or onboard sources when inference
or display may still be using the prior frame. This adds a copy but prevents
bounding boxes from becoming input pixels on a repeated inference.

### Video ends immediately or loops unexpectedly

A file source returns `None` at EOF. `--video_looping` reopens the same path;
without it, the loop exits. `--do_resize` affects image/video frames; without
it, the first video frame establishes dimensions. Confirm the codec can be
read by OpenCV before diagnosing TensorRT.

## Detection and presentation semantics

### Too many/few boxes

YOLO's effective score is objectness multiplied by class probability and is
filtered at `conf_th`; then per-class NMS uses IoU 0.5. SSD filters each
seven-value record by confidence. For YOLO, verify `--category_num` matches the
engine and class dictionary. For SSD, verify the model suffix selects the
correct COCO or egohands class map. Verify letterbox setting matches engine
preprocessing; a mismatch distorts coordinate mapping. A display result alone
is not an accuracy metric.

### Coordinates or labels are wrong

Confirm input is a BGR `uint8` HWC image. The detectors convert BGR to RGB
internally. Confirm the visualization receives boxes in original-image corner
coordinates and class IDs from the engine. Avoid applying a second resize or
letterbox correction outside the detector.

### Async SSD timeout or shutdown hang

The display waits 20 seconds on the condition variable. Investigate worker
capture, CUDA context creation, engine load, inference, and camera EOF. Stop
and join the worker before releasing the camera. The pipeline keeps only the
latest shared tuple; frame drops are expected and are not necessarily a
failure.

### MJPEG client cannot connect or stream stalls

The server accepts `/mjpg` and `/`, listens on its configured port, and uses a
small two-frame queue. Check bind/port conflicts, firewall, client URL, and
whether the process is still in its inference loop. A full queue drops frames;
it is not a durable buffer. The handler ignores broken pipes from clients that
leave. Do not expose the unauthenticated broad-bind demo to an untrusted
network.

## Historical limits and evidence boundaries

The README's Jetson FPS/mAP tables are historical observations on particular
JetPack/TensorRT releases and are not acceptance targets for another GPU. The
repo also reports a TensorRT 6 FlattenConcat registration issue, YOLO's
TensorRT 6+ plugin requirement, and UFF SSD/TensorFlow 1.x-era conversion
constraints. Modern TensorRT, Python, CUDA, GStreamer, and OpenCV stacks need
separate target verification. If only CLI validation succeeds, report
"arguments valid"—not "inference works."
