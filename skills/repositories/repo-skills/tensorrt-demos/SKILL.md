---
name: "tensorrt-demos"
description: "Guide TensorRT demo construction, GPU inference, matting, legacy
  Caffe models, and COCO evaluation for the tensorrt_demos repository with
  explicit version, hardware, artifact, and safety gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tensorrt_demos

Use this repo skill when a task involves the public `jkjung-avt/tensorrt_demos`
workflows: converting Caffe, TensorFlow/UFF, DarkNet, or MODNet models to
TensorRT; running YOLO/SSD/MODNet/GoogLeNet/MTCNN demos; compiling the custom
YOLO plugin or `pytrt`; or evaluating detector mAP on COCO-format data.

This is a legacy, GPU-first operating graph. The source documents tested
Jetson Nano/TX2/Xavier NX and selected x86 NVIDIA systems, with TensorRT
requirements spanning roughly 3.x–7.x depending on the demo. Do not infer that
serialized engines, plugins, Caffe/UFF parsers, CUDA pipelines, or CLI imports
work on a current machine merely because Python or TensorRT imports succeed.
Confirm the target JetPack/TensorRT/CUDA/GPU combination before changing files
or building artifacts.

## Route by task

- **YOLO or SSD image/video/camera inference:** read
  [`detection-inference`](sub-skills/detection-inference/SKILL.md). It covers
  input modes, `TrtYOLO`/`TrtSSD`, async behavior, visualization, and MJPEG.
- **Engine conversion, plugin compilation, FP16/INT8, DLA, or build planning:**
  read [`engine-building`](sub-skills/engine-building/SKILL.md). It owns
  model/artifact naming, preflight, compatibility, and non-mutating validators.
- **MODNet export, ONNX validation, TensorRT matting, backgrounds, or video
  output:** read [`matting-inference`](sub-skills/matting-inference/SKILL.md).
- **COCO mAP for SSD/YOLO:** read [`evaluation`](sub-skills/evaluation/SKILL.md).
- **GoogLeNet Caffe classification, MTCNN face detection, or the Cython
  `pytrt` bridge:** read [`legacy-models`](sub-skills/legacy-models/SKILL.md).

Cross-workflow tasks should follow this order: environment/version and artifact
preflight → engine-building or legacy build → inference → evaluation. Keep
engine files, model weights, calibration images/caches, generated plugins,
compiled extensions, video outputs, and experiment logs outside this skill.

## Installation and minimal check

There is no supported pure-CPU install for the full graph. On Jetson, use the
TensorRT/PyCUDA/OpenCV versions supplied by the target JetPack release. On
x86_64, install a TensorRT distribution and CUDA/PyCUDA variant compatible with
the driver and GPU, then add only the selected workflow's Python packages
(typically NumPy, OpenCV, ONNX, `pycocotools`, and `progressbar2`; legacy SSD
may additionally need TensorFlow 1/UFF/GraphSurgeon). Keep these packages in a
new isolated environment; do not mutate a user-owned or system Python. For a
non-legacy x86 inspection environment, the ordinary Python-side additions are:

```bash
python -m pip install "numpy<2" opencv-python onnx pycocotools progressbar2
```

Install TensorRT and PyCUDA separately using the vendor/JetPack-supported
variant for the target; do not blindly install the newest wheel or combine
incompatible CUDA major versions. Add `Cython` only when building `pytrt`, and
add TensorFlow 1/UFF/GraphSurgeon only in a separately verified legacy SSD
environment.

Run the bundled diagnostic before selecting a workflow:

```bash
python3 scripts/check-runtime-prerequisites.py
# On an approved GPU host, also probe CUDA device visibility:
python3 scripts/check-runtime-prerequisites.py --cuda
```

A zero exit status means the listed imports/probe completed; it does not prove
that a repository plugin, serialized engine, camera, legacy parser, or model is
usable. The target needs a compatible NVIDIA driver/GPU, CUDA runtime/toolkit,
TensorRT libraries and Python bindings, OpenCV, and often PyCUDA. SSD adds
legacy UFF/GraphSurgeon/TensorFlow 1.x concerns; YOLO adds ONNX and the custom
`YoloLayer_TRT` plugin; GoogLeNet/MTCNN add Caffe parser, C++ headers, and the
Cython extension. MODNet's checkpoint is upstream-licensed and its TensorRT
engine is target-specific. Prefer isolated environments and read-only
preflight. Do not run network downloads, `sudo`, apt/pip system installers,
symlink/patch scripts, or builders implicitly.

The generated skill bundles safe argument/config/data validators. Run them
before a real build or evaluation; they do not initialize CUDA, open cameras,
load models, compile code, or prove engine correctness. A successful static
check is not a runtime/backend check.

## Minimal checks

For dependency-free routing, run the helper linked by the selected sub-skill.
For a target backend, separately verify driver visibility, GPU compute
capability, TensorRT/PyCUDA imports, plugin availability, engine deserialization,
and representative output. Select a GPU with free memory; context creation can
fail with `out of memory` even when other GPUs on the host are healthy.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting failure classification and [`references/repo-provenance.md`](references/repo-provenance.md)
before refreshing claims against another checkout. The source repository is
not a runtime dependency of this generated graph.
