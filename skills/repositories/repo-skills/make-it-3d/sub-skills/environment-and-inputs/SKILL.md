---
name: environment-and-inputs
description: "Prepare and diagnose Make-It-3D CUDA dependencies, model assets,
  Hugging Face access, DPT weights, and alpha-mask reference images before
  training."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Environment and Inputs

Use this sub-skill before any Make-It-3D training/refinement run, or when a user reports setup, dependency, model asset, credential, or image-format failures. This route owns the prerequisites that determine whether the later training commands are safe to run.

## What This Sub-Skill Covers

- CUDA/PyTorch/tiny-cuda-nn/raymarching/PyTorch3D/DPT/Stable Diffusion/CLIP/BLIP2 dependency readiness.
- DPT depth model weights and Hugging Face or local cache/token requirements.
- Reference image alpha-channel validation and practical foreground-mask checks.
- Choosing when to pass `--text` to avoid BLIP2 captioning.
- Setup failures that would make `main.py` fail before training.

Route coarse-stage command tuning to [coarse-training](../coarse-training/SKILL.md) and refine/test/mesh export commands to [refinement-and-export](../refinement-and-export/SKILL.md).

## Required Reads and Scripts

- Read [references/dependency-map.md](references/dependency-map.md) when selecting package versions or explaining old README pins on a modern host.
- Read [references/input-formats.md](references/input-formats.md) when validating or preparing the reference image and prompt.
- Read [references/troubleshooting.md](references/troubleshooting.md) for missing module, DPT weight, Hugging Face, CUDA extension, and alpha-mask failures.
- Run [scripts/validate_alpha_input.py](scripts/validate_alpha_input.py) on a candidate `--ref_path` image.
- For broad environment diagnostics, use the root [../../scripts/make_it_3d_env_check.py](../../scripts/make_it_3d_env_check.py).

## Setup Decision Workflow

1. **Ask for or infer the user's target machine constraints.** GPU model, driver/toolkit, Python version, torch version, network permissions, and whether model weights are already cached all matter.
2. **Check CUDA first.** A successful CPU import is not enough for Make-It-3D's main path. The source sets `opt.cuda_ray = True`, so raymarching CUDA support must be treated as a real requirement.
3. **Check import-time blockers before running `main.py`.** In this source, `main.py` can fail at import time if PyTorch3D or other refine dependencies are missing, even if the user only wants `--help`.
4. **Check model assets.** DPT hybrid weights are expected at `dpt_weights/dpt_hybrid-midas-501f0c75.pt` by the main pipeline. Stable Diffusion and BLIP2 need cache/network/token unless already available.
5. **Validate the alpha input.** If the image lacks alpha, stop and ask the user to create an alpha PNG or accept that the repo's input assumptions need a deliberate source patch.
6. **Pass a prompt when possible.** Recommend `--text "..."` for reproducibility and to avoid BLIP2 download/memory cost.

## Quick Checks

```bash
python /path/to/skill/scripts/make_it_3d_env_check.py --repo-root /path/to/Make-It-3D --dpt-weights /path/to/Make-It-3D/dpt_weights/dpt_hybrid-midas-501f0c75.pt
python /path/to/skill/sub-skills/environment-and-inputs/scripts/validate_alpha_input.py --image /path/to/ref_alpha.png
```

The second command should report a present alpha channel and nonzero foreground coverage. If it fails, fix the image before constructing coarse training commands.
