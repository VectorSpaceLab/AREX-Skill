# MODNet troubleshooting

Use the first matching symptom. Preserve the command, versions, and full
error in the run record; do not hide a backend or model artifact gap by
switching to an unvalidated path.

## Environment and artifact failures

### `ModuleNotFoundError: torch`, `onnx`, or `onnxruntime`

The export/ONNX environment is incomplete. Use an isolated environment and
compare installed versions with `modnet/torch2onnx/requirements.txt` and the
historical versions in `modnet/README.md`. Do not install into the system
Python merely to make a smoke test pass. If the task is only TensorRT runtime,
ONNX export can be treated as a separate unavailable construction stage, but
record that it was not reproduced.

### `ModuleNotFoundError: tensorrt` or `pycuda`

The TensorRT stages require NVIDIA's runtime and a compatible Python binding;
PyCUDA additionally requires a working CUDA driver/toolchain. CPU ONNX Runtime
is not a substitute for TensorRT parsing, engine building, CUDA buffer
allocation, or engine inference. Classify the native candidate as
`BLOCKED_REQUIRED_BACKEND` and report the exact missing import.

### Checkpoint not found or `load_state_dict` mismatch

`export.py` checks only that the checkpoint path exists, then loads it into
`MODNet()` using the current state-dict structure. Verify that the file is a
full compatible MODNet checkpoint, not an unrelated MobileNetV2 checkpoint,
and that it was obtained from the intended upstream source. Do not guess a
checkpoint filename or silently alter model keys. The model is not bundled by
this skill.

### Engine not found

`utils.modnet.TrtMODNet` opens the literal path `modnet/modnet.engine` relative
to the current working directory. Run `trt_modnet.py` and `test_modnet.py` from
the repository root, or create the engine at that exact path. There is no
engine path argument in the demo. If a task needs a configurable engine path,
write a task-specific wrapper rather than claiming the stock CLI supports it.

## Export and ONNX failures

### CUDA error during export on a CPU host

This is expected from the source implementation: both the `DataParallel(MODNet())`
model and dummy input call `.cuda()`. Do not represent CPU export as supported.
Use a compatible CUDA PyTorch environment or explicitly scope a source
modification as an unverified deviation.

### Export shape or assertion failure

The MODNet HR branch asserts `height % 4 == 0 and width % 4 == 0`. Check that
`--width` and `--height` are positive, use width first on the CLI, and keep the
tensor as `[1,3,height,width]`. For the documented context, use
`--width 512 --height 288`.

### ONNX checker or ONNX Runtime rejects the graph

Check that the exporter and runtime versions are compatible with opset 11 and
that the file is complete. Inspect graph input/output names and shapes rather
than hard-coding a name from a different export. The source test discovers
names but expects the working directory to contain both `image.jpg` and
`modnet.onnx`. A graph that runs on CPU with a different shape must not be
passed to the fixed TensorRT profile without rebuilding/re-exporting.

### ONNX validation window does not appear

`modnet/test_onnx.py` uses `cv2.imshow`, `waitKey`, and `destroyAllWindows`.
Headless environments cannot use that exact visual script. Run an equivalent
CPU ONNX Runtime check that saves or asserts output in a task-owned temporary
location; keep the GUI limitation explicit. Also confirm `cv2.imread('image.jpg')`
did not return `None`.

### Matte is empty, saturated, or has unexpected range

Confirm BGR→RGB conversion, CHW layout, float32 type, and normalization
`(x-127.5)/127.5`. The model's output has a sigmoid in the fusion branch and
should be finite and generally near `[0,1]`. Check that the graph output is not
being interpreted as `[0,255]`; the TensorRT wrapper returns a float matte and
the blender performs the weighted sum itself. Compare CPU ONNX and TensorRT on
the same image after resizing both outputs to the source dimensions.

## TensorRT build failures

### TensorRT major version is below 7

`modnet/onnx_to_tensorrt.py` exits for major version <7 and the runtime module
has the same floor. MODNet InstanceNormalization also needs a sufficiently
recent TensorRT implementation. Upgrade/use a target with a tested compatible
TensorRT rather than deleting the version check.

### `InstanceNormalization does not support dynamic inputs`

This is the documented TensorRT 7.1 issue. TensorRT 7.2+ fixes the standard
route. On 7.1, use the source-documented locally built `onnx-tensorrt`
workaround, including the CMake patch, the correct CUDA include path, and
`onnx2trt ... -d 16 -v`. The submodule is not bundled and may be uninitialized.
Record the workaround's versions and treat any other version as unverified.

### Unknown input/profile tensor (`Input` versus `input`)

The exporter names its input `input`; the builder's `profile.set_shape` uses
`Input`. TensorRT names are case-sensitive. Inspect the parsed network or ONNX
metadata and use the actual name. For the included exporter, the minimal
expected correction is lowercase `input`. Then rebuild and verify the engine's
bindings are `input` and `output`.

### Parser errors or build returns `None`

Run with `-v`; preserve each `parser.get_error(...)`. Check that the ONNX file
is the intended generated graph, that its opset and operators are accepted by
the installed TensorRT, and that the profile dimensions exactly match the
fixed graph. Do not use the builder's `640x480` defaults for a `512x288` graph.
Confirm enough GPU memory for the 1 GiB workspace request. A parser success
alone is not an engine success.

### `--int8` or `--dla_core` fails

This is intentional in this source snapshot: INT8 and DLA are parsed but the
MODNet builder raises explicit “not implemented” errors. Remove those flags
for the supported FP16 path. Do not borrow the YOLO INT8/DLA workflow; it is a
different model and builder.

### Engine builds but will not deserialize

TensorRT serialized engines are tied to the build/runtime compatibility and
may depend on GPU architecture. Rebuild with the target's TensorRT/CUDA/GPU
stack. Check `trt.__version__`, CUDA driver visibility, plugin initialization,
and the engine path. Do not assume a successful build on x86_64 is valid on a
Jetson, or vice versa.

## Inference and input failures

### `assert len(engine) == 2` or binding shape assertion

The runtime requires exactly two bindings in order `input`, `output`, both
float, with `[1,3,H,W]` and `[1,1,H,W]`. The engine may have been built from a
wrong graph, a different binding order, dynamic dimensions, or an incompatible
conversion. Inspect the engine/network contract and rebuild a fixed-shape
engine; do not weaken the assertions without a separate validated wrapper.

### Output has a wrong size or blending broadcasts incorrectly

`TrtMODNet.infer` resizes the matte to `img.shape[:2]`. Confirm input is a
three-channel BGR HWC frame and that the background is exactly the camera
output size. The background class resizes still/video backgrounds, but a
custom caller must do this itself. Never blend the raw engine output directly
against a source-resolution frame.

### Camera does not open

Select exactly one supported source. For a file, check path and codec. For a
USB/RTSP/onboard source, check GStreamer elements, device permissions, camera
availability, and requested dimensions. `Camera` starts a reader thread for
live sources; `--copy_frame` is useful when another operation may mutate the
capture-owned array. For headless testing, use a file image/video and a
non-GUI task wrapper; the stock runner always creates an OpenCV window.

### Video stops at the end unexpectedly

Foreground files loop only with `--video_looping`. Background video always
reopens at EOF. A foreground `read()` can still return `None` if reopening or
codec decoding fails; the runner then exits. Check the input codec and path.

### Background rejected

The source checks lowercase suffixes only: `.jpg`, `.png`, `.mp4`, `.ts`.
Use one of those, ensure the still image is readable, and ensure video capture
opens. An empty `--background` is the supported black-background case.

### Recording does not produce the expected filename

Pass a basename to `--create_video`; the writer appends `.ts` when it detects
`omxh264dec`, otherwise `.mp4`. `gst-inspect-1.0` is invoked by the writer and
can itself fail if GStreamer is absent. OpenCV may also lack the requested
codec. The demo does not check `VideoWriter.isOpened()`, so use a wrapper or
inspect the output after a short run.

### `--demo_mode` does not match comments

Use the implementation's half-open frame ranges, not a paraphrase. The final
phase forces `matte[:, :] = 1.0`, showing the original foreground. The blender
mutates the current matte/background inputs during the demonstration; do not
reuse those arrays after blending unless copied.

## Safe stop and evidence rules

Stop rather than retry indefinitely when the missing item is a checkpoint,
engine, CUDA/TensorRT backend, required camera, or third-party submodule. A
safe configuration review can still run with
`scripts/validate-matting-config.py`, but it cannot establish inference
correctness. Keep generated engines, downloaded weights, patched submodules,
logs, and review reports out of the runtime skill tree.
