# Pose compatibility and readiness

Return to [SKILL.md](../SKILL.md) for routing. This page separates the
verified core facts from the optional detector requirements; detailed failure
responses are in [troubleshooting.md](troubleshooting.md).

## Current boundary

The prepared installation demonstrated that the torch CUDA core works. It did
**not** demonstrate detector execution. Lightweight MMCV was available without
its compiled `mmcv._ext` operations. An attempt to build `mmcv-full==1.7.2`
from source failed because `thrust/complex.h` was unavailable. The final core
prefix excludes full-MMDetection/MMCV ops. Consequently:

- ST-GCN success, torch CUDA availability, or a native ST-GCN/NMS import does
  not prove that MMDetection can initialize or execute.
- Cascade-RCNN and HTC workflows remain optional and unresolved.
- Do not run a detector or video workflow merely because the core checker or a
  recognition smoke passes.
- The readiness checker reports capability and returns nonzero only when
  `--require-detector` is supplied and detector readiness is absent.

## Required layers for the optional path

A usable image/video pose run needs all of these layers aligned:

1. **Python/package layer:** importable `torch`, `mmcv`, and `mmdet`; the
   detector API must expose `mmdet.apis.init_detector` and
   `mmdet.apis.inference_detector`.
2. **Compiled operator layer:** MMCV must expose `mmcv._ext`, and the
   MMDetection/MMCV versions must be mutually compatible. A lightweight MMCV
   package that imports but lacks `_ext` is insufficient.
3. **Package-native layer:** importable mmskeleton pose APIs and its NMS/native
   components, with a pose estimator configuration that matches the installed
   package era.
4. **Hardware layer:** a supported CUDA torch build, visible GPU(s), enough
   memory for the detector/HRNet combination, and a worker count appropriate
   to available memory. The documented historical environment used PyTorch
   1.2.0 with CUDA 9.2 or 10.0, but those versions are historical guidance,
   not a modern compatibility guarantee.
5. **Artifact layer:** a detector config and matching checkpoint, an HRNet
   config and matching checkpoint, and readable input images/videos. Remote
   `mmskeleton://` aliases resolve to downloads; they are not local weights.
6. **I/O layer:** OpenCV/MMCV video decoding and encoding support when using
   demos or dataset building, plus writable output directories.

## Supplied model pairings

The regular pose configuration pairs a Cascade-RCNN detector config with the
`mmdet/cascade_rcnn_r50_fpn_20e` alias and an HRNet pose config with the
`pose_estimation/pose_hrnet_w32_256x192` alias. The HD configuration replaces
the detector with the matching HTC config and alias while retaining HRNet.
Use config files supplied by the caller or a compatible package distribution;
do not mix detector config and checkpoint families without checking the
model's expected architecture.

The detector configs use old MMDetection-era model definitions, data pipeline
fields, and checkpoints. A current MMDetection/MMCV release may reject them or
require migration. Treat version compatibility as an explicit prerequisite,
not as something this sub-skill silently fixes.

## Checker contract

`scripts/check_pose_readiness.py` is safe to invoke from arbitrary cwd because
it imports packages only and does not resolve or execute source-repository
configs. It accepts `--device DEVICE` (`auto`, `cpu`, `cuda`, or a CUDA index
such as `cuda:0`) and `--require-detector`. It reports:

- torch version and CUDA build;
- requested device, CUDA availability, device count/name when possible;
- MMCV version and whether `mmcv._ext` imports;
- whether `mmdet.apis` imports and exposes the required detector functions.

It does not download checkpoints, allocate a model, decode a video, or run a
detector. Without `--require-detector` it exits zero even when the optional
stack is missing, making it suitable for inspection. With the flag it exits
nonzero if torch/CUDA, MMCV custom ops, or required MMDetection APIs are
unavailable. A passing report still means only that the import/capability gate
was observed; it is not a detector inference verification.
