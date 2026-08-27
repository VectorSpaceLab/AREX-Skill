---
name: second-pytorch
description: "Guide historical SECOND and PointPillars LiDAR 3D detection
  workflows for KITTI and NuScenes, including data contracts, configuration,
  geometry, evaluation, guarded training/inference, and the web viewer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SECOND PyTorch

Use this repo skill for source-grounded work involving the deprecated
`traveller59/second.pytorch` 1.6.0-alpha-era codebase: KITTI/NuScenes LiDAR
3D detection, VoxelNet/SECOND, PointPillars, voxel and box geometry, text
protobuf configs, evaluation, and the historical KITTI web viewer.

## First decision: historical code or maintained replacement?

The repository is explicitly deprecated. For new detector development, prefer
OpenPCDet or MMDetection3D. Use this skill when a historical config, checkpoint,
experiment, data artifact, or compatibility question requires this code's
contracts. Read [repo-provenance.md](references/repo-provenance.md) before
assuming this skill matches a checkout, and read
[compatibility.md](references/compatibility.md) before importing the detector.

## Runtime boundary

- The checkout has no `pyproject.toml`, `setup.py`, requirements file, or
  supported modern package install. Use a private isolated environment and an
  explicitly supplied checkout only when the historical runtime is truly needed.
- The executable, verified portion of this graph is CPU-safe/static: dataset
  layout validation, config/schema reasoning, NumPy geometry, and safe helper
  probes.
- Full sparse detector construction, GPU NMS, training, evaluation, checkpoint
  restoration, and viewer checkpoint inference are **legacy-backend guarded**.
  Current `spconv` 2.x APIs are not interchangeable with the source's old
  symbols. A successful Torch CUDA smoke or `spconv` import is not detector
  verification.
- Do not download datasets/checkpoints, start a service, launch the Qt viewer,
  run full training/evaluation, or mutate data as a skill smoke test.

Read [troubleshooting.md](references/troubleshooting.md) for cross-cutting
failures before changing dependencies, paths, or config files.

## Public environment setup

There is no supported package installer for this source tree. For the verified
CPU-safe/static routes, create an isolated Python 3.10+ environment and install
only the public scientific/runtime dependencies needed by the selected helper,
for example `numpy`, `scipy`, `numba`, `scikit-image`, `Pillow`, `protobuf<4`,
`fire`, and optional `nuscenes-devkit` or `flask-cors`. The bundled geometry and
layout helpers use standard Python/NumPy and do not require the detector stack.

For model work, install a separately reproducible legacy Torch/spconv/Numba
combination and run the backend probe. Do not install the newest `spconv` and
assume compatibility; the source expects old symbols that current 2.x wheels
may not expose. Never mutate an existing environment or use a CUDA import as a
substitute for the gate in [compatibility.md](references/compatibility.md).

## Route by task

| Request signal | Read next |
|---|---|
| KITTI/NuScenes root, infos, reduced clouds, ground-truth database, sweeps, custom dataset, voxel/preprocess layout | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| train/evaluate, VoxelNet, PointPillars, checkpoint, config selection, fp16, multi-GPU, spconv/Numba compatibility | [training-and-inference](sub-skills/training-and-inference/SKILL.md) |
| boxes, corners, yaw, camera/lidar conversion, anchors, encoding, IoU/NMS, KITTI AP, NuScenes results | [geometry-and-evaluation](sub-skills/geometry-and-evaluation/SKILL.md) |
| KITTI web viewer, Flask/CORS, browser/backend URLs, point-cloud or detection payloads, buildNet/inference UI | [visualization-and-serving](sub-skills/visualization-and-serving/SKILL.md) |

Cross-route requests should start with data preparation, then configuration and
training/inference, while geometry/evaluation owns box conventions and metrics.
The viewer is a guarded consumer of the same data and checkpoint contracts.

## Minimal safe checks

Run the bundled helpers from their linked sub-skills before any user-controlled
workflow. They are self-contained and do not require the original checkout:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_layout.py --help
python sub-skills/geometry-and-evaluation/scripts/geometry_smoke.py
python sub-skills/training-and-inference/scripts/check_legacy_backend.py
python sub-skills/visualization-and-serving/scripts/check_viewer_deps.py --json
```

The geometry helper should finish with `geometry smoke: PASS`. The other probes
are diagnostic; missing optional components or legacy symbols must be reported,
not silently substituted.

## Public contract reminders

- Internal LiDAR boxes normally use `[x, y, z, w, l, h, yaw]`; KITTI camera
  boxes use a different dimension/order convention. Never swap dimensions by
  visual intuition.
- KITTI preparation expects `training/` and `testing/` trees with matching
  image, calibration, point-cloud, and (for training) label stems. NuScenes
  preparation depends on version metadata, samples, sweeps, and a matching
  velocity/non-velocity dataset class.
- Historical config field names such as `kitti_root_path` and
  `kitti_info_path` are used by both dataset families. Keep dataset class,
  info files, feature width, box dimensionality, and class order consistent.

## Handoff

A useful result reports the selected route, source/skill provenance, validated
layout/config/geometry observations, exact generated output paths, backend gate
status, and any unverified legacy limitation. Do not claim a metric, detector
run, or viewer inference result from a static or CPU-safe check alone.
