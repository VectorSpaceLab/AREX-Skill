---
name: "inpainting-inference"
description: "Routes RePaint config selection, custom dataset and mask layout,
  checkpoint placement, inference execution, output inspection, and inference
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# inpainting-inference

Use this sub-skill to run or adapt RePaint's main inpainting workflow.
It covers config choice, dataset and mask layout, checkpoint placement, inference, output inspection, and common runtime failures.

## Use this route for

- Face, ImageNet, and Places2 style inference configs.
- Adapting the example inference pipeline to custom images and masks.
- Checking config, checkpoint, dataset, and output paths before a heavy run.
- Inspecting written outputs under the configured `paths.*` directories.
- Debugging missing checkpoints, bad mask polarity, YAML mistakes, and count mismatches.

## Do not use this route for

- Schedule rendering or resampling tuning. Use `../schedule-visualization/`.
- Low-level diffusion derivations. Keep those in references only.
- Network download automation. `download.sh` is reference-only.

## Read first

- `../../references/configuration.md` for shared config terminology.
- `../../references/troubleshooting.md` for shared failure modes.
- `references/configuration.md` for inpainting-specific config families and key meanings.
- `references/assets.md` for checkpoint and dataset layout.
- `references/workflows.md` for the dry-run and run sequence.
- `references/api-reference.md` for verified helper and upstream signatures.
- `references/troubleshooting.md` for inpainting-specific failures.

## Skill-owned script

- `scripts/run_inpainting.py` — dry-run-capable wrapper adapted from the upstream inpainting sampler.

## Typical workflow

1. Pick the closest base config: face, ImageNet, or Places2.
2. Point `model_path`, `gt_path`, and `mask_path` at your local assets.
3. Run the bundled helper with `--dry_run` to confirm pair counts, mask polarity, and output directories.
4. Fix any layout or config errors before running the sampler.
5. Run the helper without `--dry_run` to execute the bundled sampler path.
6. Inspect `paths.srs`, `paths.lrs`, `paths.gts`, and `paths.gt_keep_masks`.

## Cross-links

- Resampling schedule questions belong to `../schedule-visualization/`.
- Shared terminology belongs to `../../references/configuration.md` and `../../references/troubleshooting.md`.
- If you need schedule tuning details, do not edit this sub-skill; switch routes instead.
