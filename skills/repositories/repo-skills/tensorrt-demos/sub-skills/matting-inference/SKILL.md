---
name: "matting-inference"
description: "Build, validate, and run the repository's MODNet matting pipeline
  from a PyTorch checkpoint through fixed-shape ONNX and TensorRT, then blend
  image, video, camera, and background inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MODNet Matting Inference

Use this skill when the task is to export MODNet, validate its ONNX graph,
build the repository's TensorRT engine, or run `trt_modnet.py` for image/video/
camera matting. The procedures are grounded in this repository at
`modnet/`, `trt_modnet.py`, `test_modnet.py`, and the MODNet-related files under
`utils/`.

This is an operating skill, not a model distribution. The skill does **not**
bundle the MODNet PyTorch checkpoint, a generated TensorRT engine, or the
third-party `modnet/onnx-tensorrt` submodule. Obtain model weights separately
under their upstream license (the README identifies the pretrained MODNet
weights as CC BY-NC-SA 4.0), and keep generated artifacts outside the skill
bundle. The repository checkout may contain `modnet/modnet.onnx`, but a runtime
must not assume that artifact is present in every checkout.

## Fast route

Run commands from the repository root unless a step explicitly says `cd modnet`.
The intended fixed-shape route is:

1. Obtain a compatible MODNet checkpoint, preferably the portrait matting
   checkpoint named in `modnet/README.md`.
2. Export a batch-1 ONNX model with width `512`, height `288`:

   ```bash
   cd modnet
   python -m torch2onnx.export --width 512 --height 288 \
       /path/to/modnet_webcam_portrait_matting.ckpt modnet.onnx
   cd ..
   ```

3. Validate the ONNX graph on CPU with ONNX Runtime; see
   [workflows.md](references/workflows.md).
4. Build an FP16 TensorRT engine with dimensions matching the ONNX export:

   ```bash
   cd modnet
   python onnx_to_tensorrt.py --width 512 --height 288 \
       modnet.onnx modnet.engine
   cd ..
   ```

   The script's CLI defaults are `640x480`, so do not rely on its defaults for
   the `512x288` export. Also inspect the input name before building: the
   exporter writes `input` (lowercase), while this historical builder passes
   `Input` (uppercase) to `profile.set_shape`. If TensorRT rejects `Input` as
   an unknown profile tensor, make the minimal local source correction to use
   the actual input name (`input`), then rerun the build. Do not silently use a
   profile shape or input name that differs from the ONNX graph.
5. From the repository root, run an input mode such as:

   ```bash
   python3 trt_modnet.py --image modnet/image.jpg
   ```

   `utils.modnet.TrtMODNet` loads `modnet/modnet.engine` by this exact
   repository-relative path; `trt_modnet.py` has no `--engine` option.

## Pipeline contract

### PyTorch to ONNX

`modnet/torch2onnx/export.py` constructs `MODNet()` with the MobileNetV2
backbone, loads the checkpoint into a CUDA `DataParallel` wrapper, switches to
evaluation mode, and calls `torch.onnx.export` with opset 11, input name
`input`, and output name `output`. The exported batch is fixed at 1 and the
export dimensions are fixed. The model implementation asserts that its input
height and width are divisible by 4; keep that invariant for custom dimensions.

The documented `512x288` context means **width 512, height 288**, and therefore
the tensor shape is `[1, 3, 288, 512]` (NCHW). Do not reverse width and height.
The exporter creates its dummy tensor as uniform values in `[-1, 1]` on CUDA;
it is not a CPU-only exporter. The checkpoint must match this repository's
MODNet architecture/state-dict keys. `backbone.py` has a separate optional
MobileNetV2 pretrained-checkpoint path, but the export script loads the supplied
MODNet checkpoint directly and does not invoke that path.

### ONNX validation

`modnet/test_onnx.py` is a small visual check. From `modnet/`, it reads
`image.jpg`, resizes it to `(512, 288)`, converts BGR to RGB, transposes to
CHW, casts to `float32`, and normalizes with `(pixel - 127.5) / 127.5`. It
creates an ONNX Runtime session without requesting CUDA and displays the
single output as a grayscale OpenCV window. The script discovers the graph's
input and output names at runtime. It does not save a result or assert a
metric, and it requires a GUI; treat a successful session plus a plausible
matte as the source-level acceptance signal, not as a benchmark.

For a headless or auditable check, use ONNX Runtime CPU to reproduce the same
preprocess, assert that the graph accepts `[1,3,288,512]`, assert one output
with a single-channel spatial matte, and record finite output values. Keep this
check separate from TensorRT: CPU ONNX validation proves graph execution and
pre/postprocessing, not CUDA/TensorRT parity.

### ONNX to TensorRT

`modnet/onnx_to_tensorrt.py` requires TensorRT 7 or newer, parses the ONNX graph
with the explicit-batch API, forces batch 1, allocates a 1 GiB workspace,
enables GPU fallback and FP16, and creates a fixed optimization profile. The
profile must agree with the graph's actual input tensor name and shape. The
script writes a serialized engine only after `build_engine` returns a non-None
engine.

The `--int8` and `--dla_core` flags exist in the parser but the implementation
raises `RuntimeError('INT8 not implemented yet')` or
`RuntimeError('DLA_core not implemented yet')`; they are not supported paths
for MODNet in this repository. Use the default FP16 route. The generated
engine is hardware/runtime-specific and must be rebuilt when the TensorRT,
CUDA, GPU/Jetson target, or relevant engine-building inputs change.

#### TensorRT 7.1 versus 7.2+

The repository README reports that TensorRT 7.1 fails on MODNet's
`InstanceNormalization` with an error like:

```text
UNSUPPORTED_NODE: ... InstanceNormalization does not support dynamic inputs!
```

TensorRT 7.2 fixes the issue for the standard Python builder route. On 7.2 or
later, use `modnet/onnx_to_tensorrt.py` after matching dimensions and correcting
the historical profile-name mismatch if needed. On 7.1, the documented
workaround is to fetch and build the `onnx-tensorrt` submodule locally, patch
its old CMake requirement as described in [workflows.md](references/workflows.md),
and invoke its `onnx2trt` binary with `-d 16 -v`. This is a version-bound
third-party build, not a bundled dependency; record the exact TensorRT,
onnx-tensorrt, compiler, and CUDA versions. Do not claim that the workaround
works on an untested modern combination.

### TensorRT runtime and matting

`utils/modnet.py` implements `TrtMODNet` for TensorRT 7+ and PyCUDA. It
initializes built-in TensorRT plugins, deserializes
`modnet/modnet.engine`, and expects exactly two bindings in order: `input` and
`output`. It requires float input/output bindings, input shape `[1,3,H,W]`,
and output shape `[1,1,H,W]`. The engine's H/W are used as the inference input
shape; the returned matte is resized back to the original frame's H/W.

Each frame is processed as follows:

1. Resize BGR input to the engine's `(W,H)` with `cv2.INTER_AREA`.
2. Convert BGR to RGB, transpose HWC to CHW, cast to `float32`.
3. Normalize each channel with `(x - 127.5) / 127.5`.
4. Copy the contiguous tensor to a pagelocked CUDA buffer and run
   `execute_async_v2`.
5. Reshape the output to the engine output's last two dimensions and resize it
   to the original frame shape.

`trt_modnet.py` blends the original BGR frame and a background using
`img * matte + bg * (1 - matte)`. The runtime therefore expects a matte whose
values behave like `[0,1]`; do not convert it to `[0,255]` before blending.
The source docstring's phrase “0 or 255 pixels” is stale relative to this
blend formula. `pycuda.autoinit` creates a CUDA context at import time, so help
or runtime checks can fail before argument parsing when PyCUDA/CUDA is absent.

## Input, background, demo, and recording behavior

`trt_modnet.py` combines `Camera`, `Background`, `BackgroundBlender`, and an
optional writer:

- `--image FILE`: read a still image repeatedly. Without `--do_resize`, its
  native dimensions become the output dimensions.
- `--video FILE`: read a video. `--video_looping` reopens it at EOF;
  `--do_resize --width W --height H` resizes frames to the requested output.
- `--rtsp URI`: open an RTSP H.264 stream through a detected GStreamer decoder;
  `--rtsp_latency` defaults to 200 ms.
- `--usb ID`: open `/dev/videoID`; the source defaults to a GStreamer USB path.
- `--gstr TEMPLATE`: format a GStreamer string with `{width}` and `{height}`.
- `--onboard ID`: select the Jetson onboard camera. The ID is parsed but the
  legacy pipeline itself does not interpolate it.
- `--width`/`--height`: default to `640x480`; live sources use these values,
  while image/video behavior depends on `--do_resize` as above.
- `--copy_frame`: copy live capture frames before processing. This avoids
  reusing a capture-owned array when inference or overlays outlive the read.
- `--background FILE`: a lowercase `.jpg` or `.png` is resized and repeated; a
  lowercase `.mp4` or `.ts` is read and looped; an empty value produces a black
  background. Other suffixes raise `ValueError`, and unreadable image/video
  sources fail during construction or reads.
- `--demo_mode`: changes the blender only. It cycles every 360 frames through
  black-background reveal, black background, replacement-background reveal,
  replacement background, original-background reveal, and original background.
  The sequence is documented precisely in [api-reference.md](api-reference.md).
- `--create_video NAME`: writes every blended frame. `utils/writer.py` tries a
  Jetson GStreamer/H.264 transport stream and otherwise uses OpenCV `mp4v`.
  The implementation appends `.ts` or `.mp4` to `NAME`; pass a basename rather
  than an already suffixed filename.

The display loop stops when the window closes, a source returns `None`, or ESC
is pressed. `F` toggles fullscreen. The writer and camera are released on
normal completion; headless operation is not implemented by the demo itself.

## Required checks before handing off a run

- Confirm the checkpoint, ONNX, and engine paths and record their provenance;
  never infer that a missing artifact can be downloaded automatically.
- Confirm ONNX input/output names and fixed shape. For the documented export,
  expect `input`, `output`, batch 1, and `[1,3,288,512]` input.
- Run the CPU ONNX check independently of the GPU engine check.
- Run the TensorRT builder with a profile name that exists in the parsed graph,
  dimensions matching the exported graph, and no unsupported `--int8` or
  `--dla_core` flags.
- Confirm the deserialized engine has exactly the two expected bindings and
  that a CUDA inference returns a finite matte at the original frame size.
- For video/camera runs, verify the selected source, background dimensions,
  writer output suffix, and a clean ESC/window-close shutdown.
- Use the bundled safe validator before execution when only configuration
  review is possible:

  ```bash
  python3 skills/disco/tensorrt-demos/sub-skills/matting-inference/scripts/validate-matting-config.py \
      --onnx modnet/modnet.onnx --engine modnet/modnet.engine \
      --export-width 512 --export-height 288
  ```

The validator performs no model import, CUDA initialization, file download,
subprocess execution, or file mutation. It checks configuration semantics only.
For detailed failure recovery, use [troubleshooting.md](troubleshooting.md).

## Source evidence

This skill was distilled from `modnet/README.md`, the complete
`modnet/torch2onnx/` exporter/model implementation, `modnet/test_onnx.py`,
`modnet/onnx_to_tensorrt.py`, `trt_modnet.py`, `test_modnet.py`, and the
MODNet runtime helpers `utils/modnet.py`, `utils/background.py`,
`utils/writer.py`, `utils/camera.py`, and `utils/display.py`. Repository-level
MODNet instructions and compatibility claims were cross-checked against the
MODNet section of `README.md`. The generated skill intentionally excludes the
uninitialized `modnet/onnx-tensorrt` source and all model/engine binaries.
