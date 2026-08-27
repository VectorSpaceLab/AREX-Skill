---
name: "engine-building"
description: "Build and diagnose TensorRT engines for the repository's Caffe
  GoogLeNet and MTCNN, TensorFlow UFF SSD, DarkNet YOLO, and ONNX MODNet
  workflows, including the legacy API boundaries, custom plugin, FP16/INT8
  calibration, and Jetson DLA paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TensorRT engine building

Use this sub-skill when a Researcher needs to **prepare inputs, choose a
version-compatible path, or build/inspect** one of the engines in this
repository. It is an operating guide, not a promise that a serialized engine
is portable: TensorRT engines and custom CUDA plugins are tied to the TensorRT,
CUDA, driver, GPU architecture, and sometimes OS/runtime that built them.

## Safety and decision gate

- This skill is intentionally **non-mutating by default**. Reading files,
  `--help`, `scripts/validate-engine-build-inputs.py`, and
  `scripts/check_cuda_arch.py` do not build, download, install, create symlinks,
  patch system packages, or overwrite engines.
- Building is an explicit action. Before it, confirm the target TensorRT major
  version, CUDA/toolkit and driver availability, GPU compute capability, model
  artifact provenance, output paths, and whether an existing engine may be
  replaced.
- Do not run `yolo/download_yolo.sh`, `ssd/install.sh`, `*/install_pycuda.sh`,
  or the README's `wget`, `apt`, `pip`, `ln -s`, `patch`, and `sudo` commands as
  an implicit prerequisite. Acquire or install dependencies through the
  operator's approved, isolated process and record versions.
- Prefer a new output filename or a clean, dedicated build directory. Never
  use a source checkout as a scratch area without an explicit overwrite plan.
- Use `--verbose`/`-v` only when diagnosing; it can expose useful parser and
  tactic errors but does not make an unsupported API compatible.

## Choose the workflow

| Input/model family | Repository entry point | Outputs and fixed facts |
|---|---|---|
| Caffe GoogLeNet | `googlenet/Makefile`, `googlenet/create_engine.cpp` | `deploy.engine`; parses `deploy.prototxt` + `deploy.caffemodel`, marks `prob`, max batch 1, deserializes and expects 2 bindings |
| Caffe MTCNN | `mtcnn/Makefile`, `mtcnn/create_engines.cpp` | `det1.engine`, `det2.engine`, `det3.engine`; uses the `_relu` prototxt/model pairs and max batches PNet 1, RNet 256, ONet 64 |
| TensorFlow frozen graph → UFF SSD | `ssd/build_engine.py`, `ssd/build_engines.sh` | `TRT_<model>.bin` (temporary `<model>.uff`); fixed input `(3,300,300)`, `Input`, `NMS`; legacy TensorFlow/UFF/GraphSurgeon plus FlattenConcat plugin |
| DarkNet YOLO → ONNX → TensorRT | `yolo/yolo_to_onnx.py`, `yolo/onnx_to_tensorrt.py` | `<model>.onnx`, then `<model>.trt`; uses cfg-derived shape/classes/anchors and the `YoloLayer_TRT` plugin, final output `detections` |
| YOLO reduced precision / accelerator | `yolo/onnx_to_tensorrt.py`, `build_int8_engines.sh`, `build_dla_engines.sh` | INT8 uses `calib_images/` and `calib_<model>.bin`; DLA names use `--dla_core`; both are explicit variants, not defaults |
| ONNX MODNet → TensorRT | `modnet/onnx_to_tensorrt.py` | `python3 onnx_to_tensorrt.py [options] input.onnx output.engine`; fixed batch 1, default profile `(1,3,480,640)`, FP16 + GPU fallback; source explicitly raises for INT8 and DLA |

For detailed command sequences and artifact checks, read
[references/workflows.md](references/workflows.md). For version/API and
hardware gates, read [compatibility.md](compatibility.md). For failures, read
[references/troubleshooting.md](references/troubleshooting.md).

## Common preflight

1. Identify the actual `python3`, `nvcc`, TensorRT Python package, TensorRT
   headers/libraries, CUDA driver, and GPU. Do not infer them from a path in
   this checkout. `plugins/gpu_cc.py` is a useful native CUDA probe; the
   bundled `scripts/check_cuda_arch.py` is a dependency-free diagnostic and
   does not build anything.
2. Run the safe validator against a **read-only** source tree or an explicit
   build-input directory:

   ```shell
   python3 scripts/validate-engine-build-inputs.py --repo-root . --all
   ```

   Add `--model <name>` for a model-specific report. It checks presence,
   regular-file/symlink status, YOLO cfg shape invariants, calibration image
   count, plugin/source preconditions, and warns on missing optional inputs.
3. Confirm paths and expected names before invoking any builder. A successful
   preflight only proves that inputs are plausible; it does not parse a model,
   compile a plugin, or validate TensorRT execution.
4. Build the custom plugin before YOLO conversion, then verify that the shared
   object is loadable in the same runtime that imports `yolo/plugins.py`. The
   plugin must be compiled for every target GPU architecture or a compatible
   PTX path, and its TensorRT ABI must match the builder/runtime.
5. After each build, verify the output exists, is non-empty, can be deserialized
   by the **same** TensorRT major/minor family, and has the expected bindings or
   I/O names. For accuracy-sensitive detection changes, compare FP32/FP16/INT8
   outputs or mAP; speed alone is not validation.

## Engine-specific operating rules

### Caffe: GoogLeNet and MTCNN

- Build from the respective directory so `locateFile()` and relative model
  paths resolve. `make` compiles against `common/Makefile.config`; check
  `TARGET`, `CUDA_INSTALL_DIR`, `CUDNN_INSTALL_DIR`, TensorRT include paths,
  and libraries before compilation.
- GoogLeNet parses `deploy.prototxt` and `deploy.caffemodel`, marks `prob`,
  selects FP16 when `platformHasFastFp16()` is true, writes `deploy.engine`,
  then immediately deserializes it and prints two bindings.
- MTCNN uses the repository's `det1_relu`, `det2_relu`, and `det3_relu` files;
  the `_relu` conversion is deliberate because the README documents the
  TensorRT 3/4 PReLU workaround. Outputs are `prob1` plus box/landmark heads:
  PNet `prob1,conv4-2`, RNet `prob1,conv5-2`, ONet `prob1,conv6-2,conv6-3`.
  The executable checks 3, 3, and 4 bindings respectively.
- These C++ programs contain both legacy and newer branches, but are not
  generic modern TensorRT samples. Treat Caffe parser availability and
  deprecated `destroy()`/implicit-batch APIs as version gates, not as advice
  to mechanically port every line.

### TensorFlow UFF SSD

- Select one of the model keys declared in `ssd/build_engine.py` (the build
  shell script covers four v1/v2 COCO/EgoHands models; the Python map also
  documents Inception and SSDLite variants). Run from `ssd/` so all paths and
  `libflattenconcat.so` resolution are predictable.
- The script rewrites graph namespaces into `GridAnchor_TRT`, `NMS_TRT`, and
  `FlattenConcat_TRT`, replaces unsupported `AddV2` and `FusedBatchNormV3`,
  removes assertions/identities, and registers `Input` `(1,3,300,300)` and
  `MarkOutput_0`. It uses FP16 and a 256 MiB legacy workspace setting.
- UFF was tested by the repository with TensorFlow 1.12.x/compatible UFF (the
  README explicitly says other versions are not guaranteed). This is a legacy
  path. Do not substitute a current TensorFlow/UFF stack without an isolated
  compatibility test and do not assume an old `.bin` can be deserialized by a
  modern runtime.
- Confirm the `libflattenconcat.so` symlink/SONAME matches TensorRT 5 or 6 as
  applicable. The README records a TensorRT 6 plugin-creator registration
  warning; distinguish a harmless duplicate registration warning from a real
  missing creator or parse failure.

### DarkNet YOLO → ONNX → TensorRT

- Obtain a cfg and matching DarkNet weights through an approved source. The
  conversion script derives classes, anchor masks, input `height/width`, and
  output heads from the cfg; it expects `<model>.cfg` and `<model>.weights` in
  its working directory and writes `<model>.onnx`.
- Run `python3 yolo/yolo_to_onnx.py --help` to confirm the CLI in the active
  environment, then use `-m <model>` only after the matching cfg/weights have
  been validated. The supported naming convention is an architecture plus a
  dimension, such as `yolov4-416` or `yolov4-416x256`; custom classes require
  a matching cfg and postprocessing expectations.
- Build `plugins/libyolo_layer.so` before the TensorRT step. The Python module
  loads it using a path relative to the `yolo/` working directory, initializes
  TensorRT's plugin registry, looks up `YoloLayer_TRT`, replaces each raw YOLO
  output, and concatenates them as `detections`. The plugin accepts linear
  FLOAT tensors only; it is not an FP16 plugin implementation merely because
  the rest of the builder sets an FP16 flag.
- Run `python3 yolo/onnx_to_tensorrt.py -m <model>` for the repository's
  baseline FP16 path. The script forces batch 1, uses a 1 GiB workspace,
  creates a fixed optimization profile for the cfg shape, and serializes
  `<model>.trt`. TensorRT 7–9 and 10+ use different branches in this checkout;
  inspect the version-specific warnings in `compatibility.md` before running.
- Do not call the download script as part of a routine build. It downloads
  several large DarkNet artifacts and creates derivative cfgs/symlinks; use it
  only as an explicit, reviewed acquisition step.

### YOLO FP16, INT8 calibration, and DLA

- FP16 is the default selected builder mode in the legacy YOLO, GoogLeNet, and
  MTCNN implementations when supported. Check `platform_has_fast_fp16` or the
  corresponding modern capability before claiming a true FP16 build.
- INT8 requires a platform with fast INT8 support and a representative image
  set. The repository calibrator reads `.jpg` files from `calib_images/`,
  resizes BGR→RGB to the cfg shape, transposes to CHW, scales to `[0,1]`, uses
  batch 1, and caches at `calib_<model>.bin`. The README suggests 500 images
  and demonstrates 1,000 COCO `val2017` images; this is guidance, not a proof
  of sufficient coverage for another deployment distribution.
- Check calibration image readability, ordering/reproducibility, class and
  scene coverage, cache ownership, and whether the cache corresponds to the
  exact model/input/preprocessing. Delete or quarantine a stale cache only
  after an explicit decision. INT8 can alter accuracy: the repository reports
  an unresolved poor mAP result for YOLOv4-608 INT8, so always evaluate.
- DLA is an optional Jetson Xavier/NX-era path. The YOLO builder sets default
  device DLA, selects `DLA_core`, enables GPU fallback in its TensorRT 7/8
  branch, and uses strict types; the TensorRT 3–6 branch rejects DLA. DLA
  engine creation is not evidence that inference used the requested core.
  TensorRT 7.1's Python API in the repository could not explicitly select the
  inference core after deserialization. Verify device placement with the
  target runtime's supported API and treat unsupported layers/fallback as
  expected failure modes. The README specifically records `yolov4-tiny-416`
  DLA build failure in the historical test.

### MODNet ONNX → TensorRT

- Use the checked-in `modnet/modnet.onnx` or another approved ONNX with the
  same input contract. The converter requires TensorRT 7+ and sets an explicit
  batch network, batch 1, a named `Input` profile, FP16, GPU fallback, and a
  1 GiB workspace. Defaults are width 640 and height 480; override both
  together when the model and caller agree.
- Invoke `python3 modnet/onnx_to_tensorrt.py --help` first, then provide
  `input_onnx output_engine`. The repository implementation deliberately
  raises `INT8 not implemented yet` and `DLA_core not implemented yet`; do
  not document those flags as working MODNet features.
- TensorRT 7.1 needs the documented private onnx-tensorrt workaround for
  dynamic `InstanceNormalization`; TensorRT 7.2 fixed the issue according to
  the README. Treat the uninitialized `modnet/onnx-tensorrt/` submodule as
  third-party build material, not as a bundled dependency. Prefer TensorRT
  7.2+ for the direct converter after checking ONNX input dimensions.
- Verify the resulting engine with `trt_modnet.py --help` or a controlled
  headless inference harness. The README's demo expects `modnet/image.jpg`,
  but display/video tests are separate from engine creation.

## Completion and handoff

Record, for each engine: source artifact hashes or provenance, TensorRT/CUDA/
GPU versions, exact command and working directory, plugin and calibration
inputs, output path, warnings, deserialization/binding check, and accuracy or
runtime result. Mark a path **blocked** rather than silently falling back when
its required backend, legacy parser, custom plugin, calibration data, or DLA
hardware is unavailable. A partial static/help-only check is not a successful
engine build.
