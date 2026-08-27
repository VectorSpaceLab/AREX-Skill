---
name: frustum-pointnets
description: "Operate the legacy Frustum PointNets code release for KITTI or SUN
  RGB-D data preparation, TensorFlow runtime setup, training, inference, and 3D
  detection evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Frustum PointNets

Use this skill for the CVPR 2018 Frustum PointNets release: a TensorFlow-1
pipeline that lifts image 2D detections into 3D frustums, segments frustum
points, and estimates amodal 3D boxes. It covers KITTI as the primary workflow
and SUN RGB-D as a beta supplement.

## Start safely

This is source code, not an installable Python distribution. Work in an
isolated legacy environment and treat Python/TensorFlow/CUDA versions as part
of the experiment. A reproducible CPU inspection baseline is:

```bash
python -m pip install "tensorflow==1.15.5" "numpy==1.18.5" "scipy==1.4.1" "opencv-python-headless==4.5.5.64" "Pillow==8.4.0" "protobuf==3.20.3"
python -c "import tensorflow as tf; print(tf.__version__)"
```

Use a Python version supported by the selected TensorFlow wheel. For the
repository's unmodified source, prefer its documented Python-2.7/TensorFlow-
1.2/1.4 era; the command above is a Python-3.7 inspection baseline, not an
exact benchmark environment. Run `python sub-skills/runtime-and-custom-ops/scripts/check_legacy_runtime.py --json` from the generated skill root before training or inference.

The source was tested with Python 2.7, TensorFlow 1.2/1.4 GPU, and older CUDA.
A Python 3.7/TensorFlow 1.15 CPU graph baseline was verified during skill
construction, but CUDA and the v2 custom operators were not. Do not treat a
visible GPU or CPU graph as proof of full backend support.

## Route by task

- **Installation, TensorFlow versions, CUDA, compiler or missing `.so` files:**
  read [runtime-and-custom-ops](sub-skills/runtime-and-custom-ops/SKILL.md).
- **KITTI layout, calibration, detector rows or frustum-pickle generation:**
  read [kitti-data-preparation](sub-skills/kitti-data-preparation/SKILL.md).
- **v1/v2 training, hyperparameters, logs, checkpoints or resume:** read
  [training](sub-skills/training/SKILL.md).
- **Checkpoint inference, KITTI result rows, evaluator build or AP:** read
  [inference-and-evaluation](sub-skills/inference-and-evaluation/SKILL.md).
- **SUN RGB-D preparation, one-hot model, result pickle or Python 3D AP:** read
  [sunrgbd](sub-skills/sunrgbd/SKILL.md).

A full path normally composes runtime → data preparation → training → inference
and evaluation. Validate every handoff artifact rather than skipping directly
to a long native command.

## Cross-cutting constraints

- The repository uses direct module imports and unguarded `cPickle` in several
  files. A Python-3 run requires a recorded compatibility port.
- v2 imports custom sampling, grouping, and interpolation operators; missing or
  ABI-incompatible shared objects are a hard block.
- KITTI and SUN RGB-D class maps, box dimensions, pickles, and coordinate
  conventions are not interchangeable.
- Data downloads, multi-gigabyte conversion, long training, GUI visualization,
  and benchmark evaluation require explicit resources and are not smoke tests.
- Use bundled validators/preflights from the owning sub-skill. They are
  non-destructive and do not depend on this repository checkout.

Read [cross-cutting troubleshooting](references/troubleshooting.md) for route-
level failures. Read [provenance](references/repo-provenance.md) before using
this skill with another source revision or refreshing it.
