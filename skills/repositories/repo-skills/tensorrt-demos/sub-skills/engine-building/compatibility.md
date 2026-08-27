# Compatibility matrix and boundaries

The repository is a historical TensorRT example set, not a forward-compatible
engine generator. This matrix separates claims directly evidenced by its
README/source from observations that must be rechecked on a newer stack.

## Evidence-backed historical matrix

| Path | Evidence-backed minimum/target | Important constraints |
|---|---|---|
| GoogLeNet Caffe | README: TensorRT 3.x+; source has `<4`, `<6`, `<7`, and `>=7` branches | Caffe parser, CUDA/C++ headers and libraries; output `prob`; implicit-batch/legacy lifecycle APIs |
| MTCNN Caffe | README: TensorRT 3.x+; source has `<4`, `<6`, `<7`, and `>=7` branches | Use `_relu` models for the documented PReLU workaround; batch maxima 1/256/64 |
| UFF SSD | README: TensorRT 5.x+ Python API; TensorFlow 1.x/UFF; tested around TF 1.12.x and JetPack 4.2+ | `graphsurgeon`, `uff`, `FlattenConcat_TRT`, `GridAnchor_TRT`, `NMS_TRT`; `.bin` is runtime/version bound |
| YOLO DarkNet→ONNX | README: ONNX path and custom plugin are TensorRT 6+ | plugin is `IPluginV2IOExt`; compile CUDA code for target architecture; ONNX package/protobuf versions matter |
| YOLO INT8 | README: TensorRT 6.x+ and CUDA compute capability 6.1+ | representative JPEG calibration set; platform fast INT8; accuracy must be measured |
| YOLO DLA | README: TensorRT 7.x+, tested on Jetson Xavier NX | Xavier-class DLA; fixed profile/strict types/GPU fallback branch; old API rejects DLA |
| MODNet converter | source rejects major <7; README tested TensorRT 7.1/7.2 | InstanceNormalization and dynamic input issue on 7.1; direct converter preferred on 7.2+ |
| Cython `pytrt` | root `setup.py` and `README_x86.md` | hard-coded example TensorRT 7.1.3.4 paths must be changed for target; compile extension against matching headers/libs |

The repository's top-level README also states that TensorRT 5.1.6 was present
on a Jetson Nano example and that the supported Jetson line includes Nano, TX2,
Xavier NX, AGX Xavier, and newer Orin hardware. Hardware support does not imply
that every historical parser/plugin works on every listed device.

## API-era boundaries

### TensorRT 3–5

- Caffe GoogLeNet/MTCNN use `builder->createNetwork()`, `setMaxBatchSize`,
  `setMaxWorkspaceSize`, and `buildCudaEngine` in the source's old branch.
- FP16 selects `setHalf2Mode` for the oldest branch and `setFp16Mode` for newer
  pre-config branches. These names are deprecated/removed in current releases.
- The UFF SSD path is fundamentally a legacy Python API workflow. TensorRT 5
  is the repository's stated minimum because the Python API was not available
  on the older JetPack path.
- YOLO's custom `IPluginV2IOExt` is explicitly documented as TensorRT 6+;
  do not attempt TensorRT 5 without a separately validated plugin port.

### TensorRT 6–7

- This is the repository's main historical operating window. Caffe source
  selects a builder config at major 7; YOLO uses ONNX, `IPluginV2IOExt`, FP16,
  and optional INT8; MODNet is documented for 7.1/7.2.
- YOLO's TensorRT 7 branch creates an explicit-batch network, an optimization
  profile, FP16, optional INT8 calibrator, and optional DLA configuration.
- The MODNet source uses `builder.build_engine(network, config)` and fixed
  `Input` profile dimensions. Its own code has no implemented INT8/DLA path.
- TensorRT 7.1's MODNet dynamic InstanceNormalization problem is worked around
  by the repository's documented custom `onnx-tensorrt` build; TensorRT 7.2 is
  reported to fix it.

### TensorRT 8.0–8.5 (observed compatibility, not a guarantee)

The repository commit contains compatibility edits for major 8 in the custom
plugin (`NOEXCEPT`, `enqueue` signature) and a TensorRT 7.1.3.4-oriented Makefile,
but it does **not** constitute a tested TensorRT 8.5 support matrix. On a
modern 8.5-like installation, treat these as observed source/API limits:

- `IPluginV2IOExt` is a legacy interface. The plugin's `supportsFormatCombination`
  accepts only linear `FLOAT`; it does not declare half or INT8 plugin formats.
  A network-level FP16/INT8 flag therefore cannot make this plugin itself run in
  those formats; TensorRT may retain float boundaries, reject a tactic, or fail
  to build depending on graph and version.
- The plugin's C++ serialization and creator registration are version/ABI
  sensitive. Rebuild `libyolo_layer.so` against the exact TensorRT headers and
  libraries used to build and load the engine. A plugin `.so` from TensorRT 7.1
  is not a portable TensorRT 8.5 artifact.
- Builder API names changed over this era. The repository uses
  `builder.max_workspace_size` in old paths, `config.max_workspace_size` in its
  middle branch, and `config.set_memory_pool_limit(...)` only in the `>=10`
  branch. Do not assume the TensorRT 8.5 Python bindings accept every spelling;
  check the installed API and adapt in a reviewed compatibility patch.
- `config.set_flag(BuilderFlag.FP16)`, `GPU_FALLBACK`, `STRICT_TYPES`,
  `default_device_type`, and `DLA_core` are version-sensitive properties. In
  particular, strict type semantics and deprecated flags can differ. Verify
  with the installed binding rather than suppressing `AttributeError`.
- The repository's serialized `.engine`, `.trt`, and `.bin` outputs are not
  forward-compatible deployment packages. Rebuild under the target runtime.
- UFF, GraphSurgeon, the Caffe parser, `FlattenConcat_TRT`, and TensorRT's
  legacy Python classes may be absent or unsupported in 8.5. Modern ONNX APIs
  do not automatically replace the graph rewrites and plugins in this code.
- MODNet's direct script has an explicit `trt.__version__[0] < '7'` guard but
  no tested 8.5 claim. ONNX parser support for InstanceNormalization, profile
  names, and the `build_engine` return/serialization behavior must be checked
  on the installed version.

When the target is TensorRT 8.5, the correct conclusion after static inspection
is **"requires target-stack validation"**, not "supported" or "unsupported".
Record the exact builder warnings/errors and the adapted source revision.

### TensorRT 9–10+

The YOLO source has a `>=10` builder-config branch using
`set_memory_pool_limit` and `build_serialized_network`, but this is a source
observation, not a successful repo test. TensorRT 10 also removes or changes
several legacy parser/plugin APIs. Do not infer that the branch works merely
because it exists. The repository's `engine.serialize()` call after the
`>=10` branch may itself require review, as the branch deserializes a serialized
engine into an engine object first.

## Hardware and precision gates

| Capability | Required observation | If absent |
|---|---|---|
| CUDA/plugin compilation | `nvcc`, CUDA headers/libs, host compiler, target compute capability | do not run `make`; report build blocked |
| FP16 | builder reports fast/native FP16 or a reviewed fallback | build FP32 or stop; do not call it FP16 |
| INT8 | fast INT8 support plus representative calibration images | skip INT8; do not reuse an unrelated cache |
| DLA | compatible Xavier-class Jetson and available core(s) | skip DLA; GPU fallback is not DLA execution |
| Caffe | TensorRT Caffe parser and matching `nvparsers`/headers | legacy Caffe path blocked |
| UFF SSD | matching UFF/GraphSurgeon/TensorFlow 1 and custom plugins | UFF path blocked; do not substitute modern TF silently |
| YOLO plugin | loadable `YoloLayer_TRT` creator with exact ABI | YOLO ONNX conversion may succeed, engine build must stop |
| MODNet | TensorRT 7+ ONNX parser and compatible InstanceNorm/profile behavior | use documented 7.1 workaround or stop |

## Version evidence that must be recorded

For reproducibility, capture:

```text
TensorRT Python/C++ version:
CUDA toolkit version and path:
NVIDIA driver version:
GPU model and compute capability:
cuDNN/cuBLAS versions:
Python, NumPy, ONNX, protobuf, PyCUDA versions:
UFF/GraphSurgeon/TensorFlow versions (SSD only):
compiler/nvcc flags and plugin hash:
model/cfg/ONNX/calibration hashes:
```

If the host has multiple GPUs or a CUDA device visible through a container,
record `CUDA_VISIBLE_DEVICES` and verify that the reported compute capability
matches the device used for compilation and build.
