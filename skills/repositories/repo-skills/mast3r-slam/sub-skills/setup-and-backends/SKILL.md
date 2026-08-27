---
name: setup-and-backends
description: "Helps install, repair, and verify the CUDA-backed MASt3R-SLAM
  environment, third-party editable packages, checkpoints, and backend smoke
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# setup-and-backends

Use this sub-skill when the task is about installing MASt3R-SLAM, fixing the
CUDA build/toolchain, verifying the editable third-party packages, or staging
checkpoints before any real SLAM run.

## Triggers

- "install MASt3R-SLAM"
- "torch import fails"
- "CUDA extension build failed"
- "`mast3r_slam_backends` missing"
- "nvcc not found"
- "where do the checkpoints go"
- "RealSense/OpenGL import or backend issues"

## What this route covers

- Python 3.11 environment creation and the verified CUDA 12.4 install shape.
- Submodule preparation for Eigen and pyimgui.
- Editable installs for `thirdparty/mast3r`, `thirdparty/in3d`, and the root
  package.
- CUDA extension build prerequisites (`nvcc`, `cuda_runtime.h`, `ninja`).
- Checkpoint presence, naming, and download planning.
- Import checks for `mast3r_slam`, `mast3r_slam_backends`, `mast3r`, `in3d`,
  `lietorch`, `pyrealsense2`, and `evo`.

## What this route excludes

- One-off runtime commands for a video, RGB folder, or dataset sequence.
  Route those to [run-slam](../run-slam/SKILL.md).
- Dataset download/evaluation loops and `evo_ape` metrics.
  Route those to [evaluation](../evaluation/SKILL.md).
- Upstream MASt3R or Dust3R training/demos that do not belong to MASt3R-SLAM.

## First reads

- [references/installation.md](references/installation.md)
- [references/backends-and-assets.md](references/backends-and-assets.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/check_install.py](scripts/check_install.py)
- [scripts/checkpoint_manifest.py](scripts/checkpoint_manifest.py)

## Practical workflow

1. Confirm the environment uses Python 3.11 and a CUDA-capable torch build.
2. Run the install sequence in `references/installation.md` or adapt it to the
   current machine manager.
3. Run `scripts/check_install.py --check-cuda`.
4. If checkpoints are missing, use `scripts/checkpoint_manifest.py` to print the
   filenames and download commands.
5. If imports fail, use `references/troubleshooting.md` to map the symptom to
   the right repair step before touching runtime workflows.

## Acceptance bar

Do not hand off this sub-skill as ready until all of these are true:

- `python -m pip check` passes in the target environment.
- `mast3r_slam_backends` imports.
- `torch.cuda.is_available()` is true on the intended GPU host.
- The root package imports from outside the checkout.
- The checkpoint manifest is understood and any missing assets are explicitly
  noted rather than silently skipped.

When the environment is already good, keep the answer short: point to the
checkpoint manifest or the backend diagnostic script instead of repeating the
whole install recipe.
