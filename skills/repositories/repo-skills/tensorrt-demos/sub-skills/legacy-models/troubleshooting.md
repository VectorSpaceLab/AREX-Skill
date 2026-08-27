# Troubleshooting legacy-models

Classify the first failing boundary before changing code. Keep the complete
command, source commit, TensorRT/CUDA versions, architecture, and error text.

## Asset and path failures

**Symptom:** validator reports a missing descriptor or weight, or a builder
reports it cannot open a Caffe file.

- Run the validator from the repository root and inspect the exact relative
  path. `create_engine` and `create_engines` locate files relative to their
  current directory, so invoke them inside `googlenet/` and `mtcnn/`.
- Required weights are `googlenet/deploy.caffemodel` and
  `mtcnn/det1_relu.caffemodel`, `det2_relu.caffemodel`, `det3_relu.caffemodel`.
- Do not substitute `det1.prototxt` for `det1_relu.prototxt`, or arbitrary
  weights from another MTCNN distribution. The ReLU workaround and tensor
  names are part of the engine contract.
- The label file must contain 1000 tab-delimited ImageNet rows. A missing or
  reordered file can make otherwise valid classification scores misleading.

**Symptom:** engine exists but Python cannot find it.

- `trt_googlenet.py` expects `googlenet/deploy.engine`; MTCNN expects all three
  paths under `mtcnn/`. Run from the repository root, or patch all path logic
  consistently and retest.
- Generated engines are intentionally absent from source control and this
  skill. Rebuild locally rather than searching the skill tree for binaries.

## C++ build, parser, and linker failures

**Symptom:** `NvInfer.h`, `NvCaffeParser.h`, CUDA, cuDNN, or `-lnvparsers` is
missing.

- Confirm the selected TensorRT package actually includes the Caffe parser.
  Recent installations may not. This is a required-backend block, not a Python
  import problem.
- Set `TARGET=x86_64` or `TARGET=aarch64` explicitly and pass the CUDA/TensorRT
  include and library variables supported by `common/Makefile.config`.
- Verify `CUDA_INSTALL_DIR`, `CUDNN_INSTALL_DIR`, `TENSORRT_INCS`, and
  `TENSORRT_LIBS`; the repository defaults include a historical
  `<TENSORRT_ROOT>` path.
- If an API symbol or type is missing, compare the compiler's
  `NV_TENSORRT_MAJOR` with the guarded code in the builder and `trtNet.*`.
  Do not remove a version guard merely to make compilation proceed.

**Symptom:** undefined references to CUDA/TensorRT symbols.

- Check that headers and libraries come from the same installation and
  architecture. Inspect `ldd` on the generated executable/extension.
- Ensure runtime loader paths expose the matching TensorRT and CUDA libraries.
  Avoid globally replacing system libraries; use a target-local environment or
  reviewed `LD_LIBRARY_PATH` for diagnosis.

## Engine creation and deserialization failures

**Symptom:** parser returns null, `assert(blobNameToTensor != nullptr)` fires,
or a requested output cannot be marked.

- Check the prototxt/weight pair and parser logs first. GoogLeNet must expose
  `prob`; MTCNN must expose `prob1`, regression outputs, and ONet landmarks as
  listed in [api-reference.md](api-reference.md).
- Ensure the Caffe parser supports the graph's layer set and the MTCNN ReLU
  workaround. A newer or original PReLU graph is not interchangeable.
- Keep the builder and parser from one TensorRT installation. Rebuild after a
  major-version change.

**Symptom:** builder writes an engine but its verification deserialization
fails, or Python reports a version/serialization error.

- Treat the engine as invalid for that runtime. Rebuild on the target with the
  target's TensorRT and GPU rather than suppressing the assertion.
- Check architecture, GPU compute capability, TensorRT major, CUDA runtime,
  and whether the runtime can load all linked libraries.
- A successful file write is not a successful engine; the C++ programs' final
  binding checks are the intended gate.

## `pytrt` Cython build/import failures

**Symptom:** `ModuleNotFoundError: pytrt`.

- Build from repository root with the same Python that will run the demo:
  `make PYTHON=python3`.
- Confirm Cython and NumPy are installed in that interpreter. Do not use a
  different `sudo pip` interpreter by accident.
- The generated extension is platform/Python/ABI-specific and must be rebuilt
  after changing Python, CUDA, TensorRT, or architecture.

**Symptom:** Cython cannot find `pytrt`, `numpy/arrayobject.h`, `NvInfer.h`, or
link symbols.

- Verify `setup.py`'s NumPy include discovery and its CUDA/TensorRT include and
  library paths. The checked-in TensorRT 7.1.3.4 paths are examples, not a
  portable default.
- `pytrt.pxd` declares C++ methods from `trtNet.h`; keep declarations and
  implementation signatures aligned. Re-run a clean `make clean` only when
  needed; it removes generated `pytrt.cpp` and `*.so`.

**Symptom:** `import pytrt` fails with a shared-library error.

- Use `ldd pytrt*.so` and identify the missing `libnvinfer`, CUDA, cuDNN, or
  related library. Correct the target-local loader path and retry.
- Do not interpret a successful compilation as proof of runtime compatibility.

## Inference shape and post-processing failures

**Symptom:** `bad dims`, `wrong number of bindings`, or `bad type of binding`.

- Rebuild the engine from the matching descriptors. GoogLeNet requires 2
  bindings and dimensions `(3,224,224)` / `(1000,1,1)`.
- MTCNN requires 3 bindings for PNet/RNet and 4 for ONet. Confirm output names
  and shapes in the C++ builder verification output.
- Ensure `set_batchsize()` is called for RNet/ONet and matches the crop batch.
  The wrapper asserts exact batch agreement.

**Symptom:** `minsize` or scale error in MTCNN.

- `minsize` must be at least 40. The scale factor must not exceed 0.709; the
  public script does not expose factor, so inspect callers before changing it.
- More than nine generated scales indicates an input/pyramid contract problem;
  increase `minsize`, reduce the factor, or preserve the repository's frame
  resize policy instead of increasing the fixed stack blindly.

**Symptom:** no faces, wrong colors, or landmarks outside the frame.

- Confirm the input is OpenCV BGR and that `_detect_1280x720` performs BGR→RGB.
  Do not pre-convert to RGB before passing to `TrtMtcnn.detect` unless the
  wrapper is changed accordingly.
- Verify normalization `(pixel - 127.5) * 0.0078125`, thresholds
  `0.7/0.6/0.7`, and NMS modes/thresholds. Lower thresholds only for a
  documented experiment and record the change.
- Check that large-frame coordinates are restored by the final scale division.

## Input and display failures

**Symptom:** camera is not opened, GStreamer says a decoder/source is absent,
or `Camera.read()` returns `None`.

- Start with `--image` to isolate model/runtime from capture. Image input needs
  a readable OpenCV image and repeats until `Esc`.
- For USB, check `/dev/videoN`, GStreamer availability, and the repository's
  `USB_GSTREAMER` setting. For RTSP, check the URI, H.264 decoder, and
  `--rtsp_latency`. For onboard input, use a Jetson with the matching
  `nvcamerasrc` or `nvarguscamerasrc` element.
- `--gstr` must contain `{width}` and `{height}` placeholders if it expects the
  shared formatter. Use `--do_resize` only when source resizing is intended.
- Use a display-capable session; these demos call OpenCV window APIs and are
  not headless batch programs without additional adaptation.

**Symptom:** live frames are annotated repeatedly or output appears stale.

- Use `--copy_frame` for live USB/RTSP/onboard sources when inference/display
  is faster than capture. This prevents inference from reusing a frame that has
  already been annotated.
- Prefer synchronous GoogLeNet until the async script's uninitialized
  `show_help` branch is patched and verified.
