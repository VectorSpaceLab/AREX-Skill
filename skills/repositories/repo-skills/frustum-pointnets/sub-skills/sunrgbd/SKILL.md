---
name: sunrgbd
description: "Navigate the beta SUN RGB-D preparation, one-hot training,
  testing, visualization, and 3D AP evaluation code included with Frustum
  PointNets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SUN RGB-D

Use this route only for the repository's supplementary SUN RGB-D pipeline. The
source labels it a beta release and does not provide a turnkey raw-data setup:
it expects the external SUNRGBD V1 dataset/toolbox, MATLAB extraction, a
manually organized training tree, generated pickle assets, and detector boxes.

## Route

1. Read [data and workflows](references/data-and-workflows.md) and run
   `python scripts/check_sunrgbd_inputs.py --help` before preprocessing.
2. Treat MATLAB/toolbox extraction as an external prerequisite. Do not copy the
   vendored toolbox binaries into an operating environment.
3. Generate/validate the appropriate training or detector-frustum pickle.
4. Route TensorFlow setup to `../runtime-and-custom-ops/SKILL.md` and shared
   training decisions to `../training/SKILL.md`.
5. Use the one-hot test path with `--dump_result`, then read
   [evaluation](references/evaluation.md) before computing 3D AP.

Visualization is optional, GUI-dependent, and not a verification gate. No raw
SUN RGB-D preparation, long training, or AP benchmark was executed while this
skill was created. Read [troubleshooting](references/troubleshooting.md) for
missing external assets, Python-2 pickle issues, class/schema mismatch, and
headless Mayavi failures.
