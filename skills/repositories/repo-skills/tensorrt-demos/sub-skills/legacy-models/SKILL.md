---
name: "legacy-models"
description: "Operate the repository's legacy TensorRT Caffe demos: build
  GoogLeNet classification and the three-stage MTCNN face detector, compile the
  pytrt Cython bridge, validate model/label assets, and diagnose version-bound
  runtime failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Legacy Caffe models: GoogLeNet and MTCNN

Use this sub-skill when a task concerns the `googlenet/` or `mtcnn/` demos,
`pytrt.pyx`/`pytrt.pxd`, `trt_googlenet*.py`, `trt_mtcnn.py`, or
`utils/mtcnn.py`. It describes the repository snapshot's legacy Caffe and
TensorRT execution path. It does **not** install packages, download models,
or ship generated engines, shared libraries, Caffe weights, or installers.

The normal working directory for every command below is the repository root.
Run `python3 scripts/validate-legacy-model-assets.py --repo-root .` before a
build. Read [references/workflows.md](references/workflows.md) for the ordered
build/inference procedure, [api-reference.md](api-reference.md) for tensor and
threshold contracts, and [compatibility.md](compatibility.md) before selecting
a TensorRT version.

## Operating boundary

- Treat the checked-out repository and its documented source files as the
  evidence boundary. The checkout may contain large model weights, but this
  skill intentionally references them by path rather than copying them.
- Engine files are TensorRT-version-, platform-, and GPU-dependent outputs.
  Build them on the target and do not reuse an engine from another host unless
  deserialization has been explicitly proven for the exact runtime.
- The Caffe parser and the Cython `pytrt` extension are required for these two
  demos. A CPU-only Python check cannot prove inference readiness.
- Native `--help` is conditional: both demo scripts import `pytrt` at module
  import time, so help succeeds only after a compatible extension has been
  built and its TensorRT/CUDA libraries can load.
- Keep generated `*.engine`, `*.so`, `pytrt.cpp`, and build directories out of
  this runtime skill tree. The supplied validator is read-only.

## Quick decision table

| Need | Entry point | Required generated assets |
|---|---|---|
| Classify an image or stream | `trt_googlenet.py` | `googlenet/deploy.engine`, built `pytrt` |
| Detect faces and landmarks | `trt_mtcnn.py` | `mtcnn/det1.engine`, `det2.engine`, `det3.engine`, built `pytrt` |
| Build GoogLeNet engine | `googlenet/create_engine.cpp` | `deploy.prototxt`, `deploy.caffemodel`, TensorRT Caffe parser |
| Build MTCNN engines | `mtcnn/create_engines.cpp` | three `det*_relu` prototxt/weights, TensorRT Caffe parser |
| Build Python bridge | root `Makefile` → `setup.py` | Cython, NumPy, CUDA/TensorRT headers and libraries |
| Check source/assets without mutation | `scripts/validate-legacy-model-assets.py` | Python standard library only |

If the request is to modernize these demos, export them, or replace Caffe,
stop at the compatibility boundary and describe the migration separately;
do not silently reinterpret a legacy workflow as modern TensorRT support.

## Core workflow

1. **Confirm assets and runtime.** Validate source descriptors and expected
   filenames. Confirm that the target has a matching NVIDIA driver, CUDA,
   TensorRT Caffe parser/runtime, a C++ toolchain, Python 3, NumPy, OpenCV,
   and Cython. For Jetson, identify the JetPack/TensorRT pairing first.
2. **Build engines on the target.** From `googlenet/`, run `make` then
   `./create_engine`; from `mtcnn/`, run `make` then `./create_engines`. The
   programs serialize and immediately deserialize engines and print binding
   information. A successful compiler invocation alone is insufficient.
3. **Build `pytrt`.** From the repository root, run `make PYTHON=python3`.
   This invokes `setup.py build_ext -if`, compiles the Cython module against
   `trtNet.cpp`, and removes only the temporary `build/` directory. The
   resulting extension is generated at the root and is intentionally not part
   of this skill.
4. **Run a low-risk image trial.** Use `--image` with a local image and keep
   the process in a display-capable session. Image input repeats indefinitely;
   press `Esc` to stop. Use `--copy_frame` for live sources if inference can
   outpace capture and the displayed frame is modified in place.
5. **Check outputs.** GoogLeNet must return a `prob` tensor with 1000 scores and
   display top three labels. MTCNN must return `(N,5)` boxes and `(N,10)`
   landmarks, with no NaNs and coordinates clipped to the image bounds. Record
   the exact TensorRT version, GPU, source commit, engine build command, and
   input mode with the result.

## Safety and failure handling

Do not run `install*.sh`, `download_yolo.sh`, `sudo pip`, or network fetches as
part of this workflow. Do not infer that an absent weight is safe to replace
with a random or newer model: descriptor/weight compatibility is required.
Use the read-only validator to distinguish missing assets from a broken build.
For failures, classify them as missing source/weight, toolchain/header/linker,
engine deserialization/version, extension import, input/GStreamer, or model
post-processing. See [troubleshooting.md](troubleshooting.md).

## Difficult synthetic usability cases

1. **MTCNN scale-and-threshold case:** Given a 1920×1080 BGR frame and the
   default `minsize=40`, predict that `TrtMtcnn.detect` rescales to at most
   1280×720, raises the effective minimum size but never below 40, converts
   BGR→RGB, and applies PNet/RNet/ONet thresholds `0.7/0.6/0.7`. Confirm that
   a caller asking for `minsize=32` is rejected rather than silently accepted.
2. **Mixed-runtime asset case:** Given all six Caffe model files and descriptors
   but no generated engines or `pytrt`, use the validator to report source/model
   readiness with generated-runtime warnings; explain why both demo `--help`
   commands remain blocked until a compatible extension and engines exist.
