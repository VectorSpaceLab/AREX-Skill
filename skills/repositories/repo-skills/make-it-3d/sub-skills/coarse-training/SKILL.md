---
name: coarse-training
description: "Build, tune, and troubleshoot Make-It-3D coarse-stage NeRF
  optimization commands for frontal and full-360 single-image 3D creation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Coarse Training

Use this sub-skill when a user wants to run or adapt the Make-It-3D coarse stage: the initial frontal-view optimization and the follow-up full 360-degree optimization. Use [environment-and-inputs](../environment-and-inputs/SKILL.md) first if dependencies, DPT weights, Hugging Face cache, or the alpha input are not confirmed.

## What This Sub-Skill Covers

- Constructing README-backed `python main.py` commands for the two coarse phases.
- Important CLI flags and defaults from `main.py`.
- Choosing `--text`, `--guidance`, `--sd_version`, `--need_back`, `--fp16`, `--backbone`, and camera ranges.
- Understanding coarse-stage outputs under `results/<workspace>`.
- Troubleshooting long/stretched geometry, missing captions, OOM, and default-backbone failures.

Refinement, test rendering, and mesh export are owned by [refinement-and-export](../refinement-and-export/SKILL.md).

## Required Reads and Scripts

- Read [references/workflow.md](references/workflow.md) for the two-stage run sequence and output expectations.
- Read [references/cli-reference.md](references/cli-reference.md) for flags, defaults, and source quirks.
- Read [references/troubleshooting.md](references/troubleshooting.md) for geometry and training failures.
- Run [scripts/build_training_commands.py](scripts/build_training_commands.py) to generate safe, copyable commands.

## Command Construction Pattern

```bash
python /path/to/skill/sub-skills/coarse-training/scripts/build_training_commands.py \
  --workspace NAME \
  --ref-path REF_ALPHA.png \
  --text "a short object prompt"
```

The helper prints:

1. **Frontal phase:** `--phi_range 135 225 --iters 2000`.
2. **Full-360 phase:** `--phi_range 0 360 --albedo_iters 3500 --iters 5000 --final`.

By default it includes `--text` when provided so BLIP2 captioning is not triggered. Add `--need-back` for explicit back-view prompt conditioning, `--fp16` if mixed precision is desired and supported, and `--vanilla-backbone` to emit `--backbone vanilla` when tiny-cuda-nn is unavailable and the user accepts slower training.

## Operating Checklist

Before running the generated commands:

- Alpha image validated.
- DPT hybrid weights present at the expected path or source patched intentionally.
- CUDA torch allocation works.
- Raymarching extension can import/build in the active environment.
- tiny-cuda-nn installed unless `--backbone vanilla` is intentionally used.
- Stable Diffusion or CLIP guidance assets are available.
- Workspace name is unique or the user intentionally wants to resume/overwrite `results/<workspace>`.

After the frontal phase, inspect logs and intermediate renders before expanding to 360 degrees. After the full-360 phase with `--final`, expect test render output and optionally mesh save if `--save_mesh` is also set and export dependencies are installed.
