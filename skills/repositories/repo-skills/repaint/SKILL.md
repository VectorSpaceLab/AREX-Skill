---
name: "repaint"
description: "Routes RePaint inpainting, config, output-layout, and
  jump-schedule workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# RePaint

Use this skill when the task is about the RePaint diffusion inpainting repository: configs, masks, checkpoints, inference runs, output directories, or the resampling schedule.

## What this skill covers

- Running or adapting RePaint-style inpainting with the bundled helper in `sub-skills/inpainting-inference/`.
- Inspecting and tuning jump schedules with the bundled helper in `sub-skills/schedule-visualization/`.
- Choosing the right config family for faces, ImageNet-style content, or Places2-style scenes.
- Diagnosing missing checkpoints, mask polarity mistakes, output-path problems, and schedule-parameter failures.

## When to use each route

### `inpainting-inference`
Use this route when the user asks about:
- `model_path`, `gt_path`, `mask_path`, `paths.srs`, `paths.lrs`, `paths.gts`, or `paths.gt_keep_masks`
- copying or adapting a RePaint config for custom images
- checkpoint placement or dataset/mask layout
- running the inpainting sampler or inspecting its outputs
- troubleshooting config, layout, label, or output-directory problems

### `schedule-visualization`
Use this route when the user asks about:
- `schedule_jump_params`
- `t_T`, `n_sample`, `jump_length`, `jump_n_sample`, `jump2_*`, `jump3_*`, or `start_resampling`
- rendering or comparing schedules
- explaining the speed/quality tradeoff of resampling
- diagnosing schedule assertions or plotting issues

## Read first

- `references/configuration.md` for shared config terms and family mapping.
- `references/troubleshooting.md` for cross-cutting import, runtime, and config failures.
- `references/repo-provenance.md` for the source snapshot and staleness baseline.
- `references/repo-routing-metadata.json` for router placement metadata.

Then read the route-specific files:

- `sub-skills/inpainting-inference/SKILL.md`
- `sub-skills/schedule-visualization/SKILL.md`

## Runtime and install guidance

- Use a Python 3.11 environment with `torch`, `numpy`, `pillow`, `pyyaml`, `blobfile`, `tqdm`, and `matplotlib` available.
- The repository has no packaging metadata, so use the checkout directly instead of expecting an editable install.
- Keep the helper scripts inside this skill tree; do not rely on the original repository's scripts as runtime instructions.
- For a minimal smoke check, import the source packages from the checkout: `conf_mgt`, `guided_diffusion`, and `utils`.

## Typical entry points

- `sub-skills/inpainting-inference/scripts/run_inpainting.py`
- `sub-skills/schedule-visualization/scripts/render_schedule.py`

## Safe defaults

- Treat `download.sh` as reference-only; it performs network downloads and is not a runtime helper.
- Keep `mask_loader: true`, `return_dict: true`, `return_dataloader: true`, and `random_crop: false` for the example inpainting path.
- Use `--dry_run` in the inpainting helper before a heavy sampler run.
- Render schedules before changing a full inpainting config when the request is about speed or harmonization.

## If you are unsure

- If the question mentions output images, model assets, or mask directories, it belongs in `inpainting-inference`.
- If the question mentions resampling counts or schedule plots, it belongs in `schedule-visualization`.
- If the question is only about generic diffusion training or another image-generation library, this skill is not the best fit.
