---
name: motion-tools
description: "Inspect, convert, validate, view, and plot MimicKit motion,
  dataset, viewer, DOF, conversion, and log artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MimicKit Motion Tools

Use this sub-skill when a task is about MimicKit motion artifacts rather than policy training: motion pickle files, motion dataset manifests, GMR or SMPL/AMASS conversion, `view_motion` visualization, character DoF diagnostics, and training-log plots.

## Start here

1. Read [references/motion-format.md](references/motion-format.md) before writing or validating a motion file or dataset YAML.
2. Read [references/conversion-and-visualization.md](references/conversion-and-visualization.md) for bundled converter commands, viewer/DOF workflows, and log plotting.
3. If a workflow fails, route to [references/troubleshooting.md](references/troubleshooting.md) before changing data or configs.

## Bundled helpers

- [scripts/convert_gmr_to_mimickit.py](scripts/convert_gmr_to_mimickit.py) converts GMR pickle data to a MimicKit-compatible motion pickle.
- [scripts/convert_smpl_to_mimickit.py](scripts/convert_smpl_to_mimickit.py) converts SMPL/AMASS `.npz` data to the SMPL humanoid MimicKit motion layout.
- [scripts/plot_training_log.py](scripts/plot_training_log.py) plots text `log.txt`-style training logs to an image using a headless-safe default.

All helpers are self-contained and accept ordinary file paths. When a target MimicKit checkout should be made importable, pass its root explicitly with `--repo-root`; do not rely on the current working directory being the checkout.

## Route elsewhere

- Full train/test runner flags, backend installation, device selection, and simulator choice belong to the sibling `runner-and-backends` sub-skill.
- DeepMimic, AWR, LCP, AMP, ADD, ASE, and other policy-training recipes belong to algorithm sub-skills.
- Score-Matching Motion Prior training belongs to the sibling `smp` sub-skill; this sub-skill only covers generic motion/data conversion and visualization.

## Verification limits to preserve

The generated guidance is backed by source inspection plus lightweight checks: CPU/CUDA torch imports, parser help for the GMR and SMPL converters, source compile checks, and tiny converter fixtures. Simulator-native viewing and DOF-test workflows still require an external supported simulator backend plus downloaded motions/models/assets before they can be fully validated.
