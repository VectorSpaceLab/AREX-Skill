# MASt3R-SLAM Operating Overview

## When to read

Read this when you need a compact map of how the repo fits together before
choosing a sub-skill.

## Project role

MASt3R-SLAM is a CUDA-backed monocular dense SLAM system that uses MASt3R 3D
reconstruction priors for pointmaps, matching, tracking, relocalization, and
local/global optimization. Its public user surface is primarily the root
`main.py` launcher and shell evaluation/download scripts; it is not packaged as
a console-script CLI.

## Runtime architecture

- `main.py` parses `--dataset`, `--config`, `--save-as`, `--no-viz`, and
  `--calib`, loads a YAML config, creates multiprocessing queues, loads the
  dataset, starts visualization unless `--no-viz` is set, loads MASt3R and the
  retrieval model, then runs tracking and backend optimization.
- `mast3r_slam.config` merges YAML configs recursively. Child configs use
  `inherit` to load a parent file and override selected keys.
- `mast3r_slam.dataloader` selects dataset classes by dataset path tokens:
  `tum`, `euroc`, `eth3d`, `7-scenes`, `realsense`, `webcam`, video extensions,
  or a plain RGB image folder.
- `mast3r_slam.mast3r_utils` loads MASt3R checkpoints, registers Dust3R import
  paths through `mast3r.utils.path_to_dust3r`, runs mono/pair inference, and
  performs symmetric/asymmetric matching helpers.
- `mast3r_slam.matching` and `mast3r_slam.global_opt` call the compiled
  `mast3r_slam_backends` extension. This is why CUDA and a working build toolkit
  are required for primary runtime verification.
- `mast3r_slam.tracker` performs frame-to-keyframe matching and pose updates;
  `main.py` switches between init, tracking, relocalization, and termination.
- `mast3r_slam.evaluate` writes trajectory text, reconstruction `.ply`, and
  keyframe image outputs under `logs/` or `logs/<save-as>/`.
- `mast3r_slam.visualization` depends on in3d, imgui, moderngl, GLFW, and bundled
  shader resources under `resources/programs`.

## Skill boundaries

- Use `setup-and-backends` for install order, submodules, PyTorch/CUDA/nvcc,
  checkpoints, and import/backend diagnostics.
- Use `run-slam` for a single run on a video, folder, dataset sequence, live
  RealSense device, or webcam, including configs and input validation.
- Use `evaluation` for benchmark-suite loops, dataset manifests, sequence lists,
  logs, and `evo_ape` metrics.

## Generated replacements for source scripts/configs

The upstream repo has useful shell scripts and YAML configs, but future agents
should not need to reopen them. This skill bundles replacements:

| Upstream artifact family | Bundled replacement |
| --- | --- |
| `config/*.yaml` | `sub-skills/run-slam/scripts/write_config_templates.py` and `references/configuration.md` |
| `main.py` launch patterns | `sub-skills/run-slam/scripts/run_mast3r_slam.py` plus CLI/workflow references |
| Dataset layout checks | `sub-skills/run-slam/scripts/validate_inputs.py` |
| `scripts/eval_*.sh` | `sub-skills/evaluation/scripts/plan_evaluation.py` |
| `scripts/download_*.sh` | `sub-skills/evaluation/scripts/plan_downloads.py` |
| Install/backend checks | `scripts/check_install.py` |

## Backend stance

The installed-package inspection environment verified Python 3.11, PyTorch
2.5.1 with CUDA 12.4, a CUDA toolkit/nvcc path, `mast3r_slam_backends`, core
imports, `main.py --help`, and a tiny config/data-loader smoke. Full SLAM runs
still need checkpoints and real image/video/dataset inputs.
