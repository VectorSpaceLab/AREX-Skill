---
name: mast3r-slam
description: "Guides MASt3R-SLAM installation, CUDA backend setup, visual SLAM
  runs on video/live/dataset inputs, and benchmark evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MASt3R-SLAM

Use this repo skill when the task is about the MASt3R-SLAM project: installing
its CUDA-backed package, preparing checkpoints, running dense monocular SLAM on
videos, RGB folders, live cameras, or supported benchmark datasets, or planning
TUM/7-Scenes/EuRoC/ETH3D evaluations.

MASt3R-SLAM is not a CPU-only utility. The primary runtime imports the custom
`mast3r_slam_backends` extension, uses PyTorch CUDA tensors, and `main.py`
selects `cuda:0`. Treat CPU-only checks as helper validation only; do not claim
a full SLAM run is ready until a CUDA build and CUDA smoke check pass.

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) when you
   need to know whether this skill matches the current checkout or should be
   refreshed.
2. For a new machine or broken install, load
   [setup-and-backends](sub-skills/setup-and-backends/SKILL.md).
3. For a concrete run on an input video, RGB folder, benchmark sequence,
   RealSense stream, or webcam, load [run-slam](sub-skills/run-slam/SKILL.md).
4. For benchmark-suite loops, dataset manifests, result logs, or `evo_ape`
   metrics, load [evaluation](sub-skills/evaluation/SKILL.md).
5. Use [references/overview.md](references/overview.md) for a quick architecture
   and workflow map, and [references/troubleshooting.md](references/troubleshooting.md)
   for cross-cutting failure routing.

## Minimal verified environment shape

A working MASt3R-SLAM environment needs all of these classes of dependencies:

- Python 3.11 with PyTorch 2.5.1 on a CUDA build matching the driver.
- A CUDA build toolkit, not only a runtime. `nvcc` and `cuda_runtime.h` must be
  visible when the root package compiles `mast3r_slam_backends`.
- Populated submodules for Eigen and pyimgui before installing `thirdparty/in3d`
  and compiling the root extension.
- Editable installs for the vendored `thirdparty/mast3r`, `thirdparty/in3d`, and
  then the root package with build isolation disabled for extension builds.
- MASt3R metric and retrieval checkpoints before any real SLAM run.

After installation, run the bundled diagnostic rather than guessing:

```bash
python scripts/check_install.py --check-cuda
```

Add `--checkpoint-dir <path>` to validate checkpoint filenames and `--repo-root
<path-to-MASt3R-SLAM-checkout>` when the package is not already installed in the
active Python environment.

## Route map

| Need | Read |
| --- | --- |
| Install order, CUDA/PyTorch/nvcc choices, submodules, checkpoints, import checks | [setup-and-backends](sub-skills/setup-and-backends/SKILL.md) |
| Build a safe command for `main.py`, choose `--no-viz`, `--calib`, `--save-as`, or generate config templates | [run-slam](sub-skills/run-slam/SKILL.md) |
| Validate TUM/EuRoC/ETH3D/7-Scenes/RGB-folder/MP4/webcam/RealSense input layout | [run-slam references/data-formats.md](sub-skills/run-slam/references/data-formats.md) |
| Prepare benchmark dataset download plans without immediately downloading large archives | [evaluation](sub-skills/evaluation/SKILL.md) |
| Recreate `eval_*.sh` behavior, print or run suite commands, compute `evo_ape` metrics | [evaluation references/evaluation-workflows.md](sub-skills/evaluation/references/evaluation-workflows.md) |
| Diagnose `CUDA not found`, missing `mast3r_slam_backends`, OpenGL/RealSense, checkpoints, missing logs, or calibration variants | [references/troubleshooting.md](references/troubleshooting.md) first, then the owning sub-skill troubleshooting file |

## Operating constraints

- Do not run dataset download or checkpoint download commands implicitly; they
  are network and storage side effects. Use the bundled planners to print the
  exact commands and ask before executing them.
- Do not substitute a CPU import, `main.py --help`, or config parser check for a
  full SLAM backend verification. Those are useful helper checks only.
- Do not rely on upstream README/script/config files being opened during future
  tasks. This skill bundles the relevant install sequence, config templates,
  dataset manifests, and command planners.
- Do not use vendored MASt3R/Dust3R demos or training entry points as
  MASt3R-SLAM workflows unless the user explicitly asks for upstream MASt3R
  internals; this repo skill focuses on the SLAM package.

## Quick task recipes

- **Install failed:** load `setup-and-backends`, then run
  `scripts/check_install.py --check-cuda` and follow the symptom-specific
  troubleshooting notes.
- **Run one video or RGB folder:** load `run-slam`, generate or select a config,
  validate the input layout, and use `run_mast3r_slam.py --dry-run` before any
  long execution.
- **Run a benchmark suite:** load `evaluation`, print the suite commands with
  `plan_evaluation.py`, confirm datasets/checkpoints/log destinations, then run
  only the approved sequences.
- **Compute metrics only:** use `evaluation` metric-only guidance; do not rerun
  SLAM when the needed trajectory files already exist.
