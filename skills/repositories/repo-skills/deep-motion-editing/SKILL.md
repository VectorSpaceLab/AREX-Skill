---
name: deep-motion-editing
description: "Guides DeepMotionEditing BVH animation, skeleton-aware motion
  retargeting, motion style transfer, and Blender visualization workflows for
  research use."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Deep Motion Editing

Use this repo skill when a task names Deep Motion Editing, BVH motion editing,
skeleton-aware retargeting, unpaired motion style transfer, OpenPose motion
style, Mixamo BVHs, or Blender rendering/skinning. It is a script-oriented
research checkout, not a conventional installable Python package. Read
[`references/repo-provenance.md`](references/repo-provenance.md) before
assuming the skill matches a new checkout.

## Start safely

This source snapshot has no `setup.py`, `pyproject.toml`, requirements file, or
console entry point; do not invent `pip install deep-motion-editing`. For the
selected Python workflows, install only the route dependencies in a disposable
environment, for example:

```bash
python -m pip install "numpy<2" scipy pyyaml tqdm torch
# Add these only for training/logging/probe work:
python -m pip install tensorboardX tensorboard matplotlib scikit-learn
```

Use Python 3.7+ as documented by the project. CUDA is recommended for model
inference/training; CPU is useful for format checks but is only a partial
neural substitute. Use Blender 2.80-era or a tested newer Blender for `bpy`
workflows; ordinary Python cannot import `bpy`. Keep datasets, checkpoints,
OpenPose outputs, FBX assets, and generated results outside the skill tree. Do
not download or overwrite them implicitly. Run the read-only environment probe
  [`scripts/check_environment.py`](scripts/check_environment.py) before a new
  task. Read [`references/troubleshooting.md`](references/troubleshooting.md)
  for legacy imports, paths, optional dependencies, and backend failures.

## Route to the focused workflow

| User intent | Read next |
|---|---|
| BVH parsing/writing, topology, JSON validation, kinematics, cleanup | [`sub-skills/animation-data/SKILL.md`](sub-skills/animation-data/SKILL.md) |
| Mixamo/custom data, intra/cross retargeting, evaluation, training | [`sub-skills/motion-retargeting/SKILL.md`](sub-skills/motion-retargeting/SKILL.md) |
| 3D/2D style transfer, normalization, Xia/BFA preparation, training | [`sub-skills/motion-style-transfer/SKILL.md`](sub-skills/motion-style-transfer/SKILL.md) |
| Blender BVH load/render, FBX skinning or conversion | [`sub-skills/blender-visualization/SKILL.md`](sub-skills/blender-visualization/SKILL.md) |

The central cross-workflow contract is: validate BVH hierarchy and frame data
first, preserve source inputs, write new outputs, then validate the result
before neural comparison or rendering. Sibling routes link to each other when
a task crosses that boundary.

## Verification boundary

A parser/help check does not reproduce a paper result. Meaningful neural runs
need the correct pretrained checkpoints, normalization files, dataset layout,
model configuration, and a suitable backend. Blender routes additionally need
a Blender executable and compatible FBX assets. This generated skill was built
from a 2021 source snapshot and intentionally omits large binaries and
external data; those limitations are recorded in the references and external
verification artifacts, not hidden.
