# Workflow Map

## Purpose

Read this when you want the quickest route from a user request to the right sub-skill.

## High-level map

| User request | Read |
| --- | --- |
| "Prepare the dataset", "convert TuSimple labels", "fix config overrides" | `sub-skills/data-and-config/SKILL.md` |
| "Train the model", "resume checkpoint", "multi-GPU launch" | `sub-skills/training/SKILL.md` |
| "Evaluate a checkpoint", "score TuSimple", "build CULane evaluator", "make a demo video" | `sub-skills/evaluation-and-visualization/SKILL.md` |
| "Export TorchScript", "benchmark speed", "LibTorch/OpenCV deployment" | `sub-skills/export-and-speed/SKILL.md` |

## Shared facts

- The repo uses CULane and TuSimple as the main dataset families.
- The training, evaluation, demo, and speed scripts call `.cuda()` directly in the source.
- CULane scoring requires a separate evaluator binary built with a C++ toolchain and OpenCV C++ headers/libs.
- The repo's public scripts are script-style entry points rather than an installable package with console scripts.

## Common routing advice

- If the request mixes data prep and training, start with `data-and-config`, then move to `training`.
- If the request mixes evaluation with export or speed, split the task: first score or visualize in `evaluation-and-visualization`, then export or benchmark in `export-and-speed`.
- If the user asks for a single command but the repo needs a dataset, checkpoint, or evaluator binary, route to the sub-skill that owns the missing prerequisite and keep the dependency explicit.
