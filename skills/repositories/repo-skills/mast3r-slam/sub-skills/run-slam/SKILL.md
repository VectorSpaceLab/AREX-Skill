---
name: run-slam
description: "Guides MASt3R-SLAM runtime commands for videos, RGB folders, live
  cameras, benchmark sequences, configs, calibration, visualization, and
  outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# run-slam

Use this sub-skill when the user wants to run MASt3R-SLAM on a concrete input or
needs help choosing runtime flags, config files, calibration, headless mode, or
output paths.

## Triggers

- "run MASt3R-SLAM on a video"
- "process an RGB image folder"
- "use RealSense or webcam"
- "which config/calibration file should I use"
- "why did load_dataset choose the wrong format"
- "where are trajectory or PLY outputs saved"
- "run headless/no visualization"

## Prerequisites

Before any real run, make sure `setup-and-backends` has verified:

- CUDA torch and `mast3r_slam_backends` import.
- Three MASt3R checkpoint assets in the runtime checkpoint directory.
- Editable MASt3R-SLAM install, or a user-provided checkout containing the
  runtime launcher.

## First reads and scripts

- [references/cli-reference.md](references/cli-reference.md) for verified flags.
- [references/configuration.md](references/configuration.md) for YAML templates
  and config inheritance.
- [references/data-formats.md](references/data-formats.md) for dataset/video/live
  input layouts.
- [references/workflows.md](references/workflows.md) for concrete run recipes.
- [references/troubleshooting.md](references/troubleshooting.md) for runtime
  failures.
- [scripts/write_config_templates.py](scripts/write_config_templates.py) to write
  bundled `base`, `calib`, `eval_*`, `eth3d`, and `intrinsics` templates.
- [scripts/validate_inputs.py](scripts/validate_inputs.py) to classify and check
  a dataset path.
- [scripts/run_mast3r_slam.py](scripts/run_mast3r_slam.py) to build a safe
  dry-run command and optionally execute it.

## Recommended runtime flow

1. Generate config templates if you are not using an existing checked-out config:

   ```bash
   python sub-skills/run-slam/scripts/write_config_templates.py --output-dir <config-dir>
   ```

2. Validate the input path:

   ```bash
   python sub-skills/run-slam/scripts/validate_inputs.py --dataset <dataset-or-video>
   ```

3. Build the command without executing it:

   ```bash
   python sub-skills/run-slam/scripts/run_mast3r_slam.py \
     --repo-root <MASt3R-SLAM-checkout> \
     --dataset <dataset-or-video> \
     --config <config-dir>/base.yaml \
     --no-viz \
     --dry-run
   ```

4. Only after confirming GPU, checkpoints, input data, and expected runtime,
   rerun with `--execute`.

## Boundary decisions

- This sub-skill owns single-run command construction and input validation.
- It routes benchmark-suite loops and metrics to
  [evaluation](../evaluation/SKILL.md).
- It routes install/CUDA/checkpoint failures to
  [setup-and-backends](../setup-and-backends/SKILL.md).

## Common choices

- Use `--no-viz` in headless containers, CI, SSH sessions, or benchmark loops.
- Use a no-calibration config for unknown intrinsics; use a calibration config
  plus `--calib` only when you have valid width/height/intrinsics.
- Use `--save-as <name>` when you need deterministic output paths under `logs/`.
- For videos, install `torchcodec` only if MP4 decoding speed is the blocker;
  OpenCV fallback remains available.
