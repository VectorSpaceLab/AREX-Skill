---
name: schedule-visualization
description: "Explain, render, and tune RePaint jump schedules without running
  full inpainting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Schedule Visualization

Use this sub-skill when the task is to inspect, explain, plot, compare, or tune the RePaint diffusion schedule in `schedule_jump_params`.

## Route here for

- Explaining `t_T`, `n_sample`, `jump_length`, `jump_n_sample`, `jump2_*`, `jump3_*`, and `start_resampling`.
- Rendering a schedule plot or JSON/CSV schedule summary with the bundled headless helper.
- Estimating schedule-driven runtime changes by comparing reverse denoise steps and forward undo steps.
- Explaining how the schedule list feeds the diffusion sampling loop and why resampling makes the noise level move up and down.
- Diagnosing schedule assertions, invalid schedule arguments, missing `matplotlib`, and headless plotting errors.

## Do not handle here

- Dataset layout, masks, checkpoint placement, `gt_path`, `mask_path`, `model_path`, and full config setup: route to [inpainting-inference](../inpainting-inference/).
- Full inpainting execution and output image inspection: route to [inpainting-inference](../inpainting-inference/).
- Shared installation, import, Python, Torch, or runtime-environment issues: use root [troubleshooting](../../references/troubleshooting.md) first, then return here for schedule-specific failures.
- Training or finetuning diffusion models: out of scope for this repo skill.

## Operating workflow

1. Identify whether the user wants a quick explanation, a rendered plot, a config edit, or a speed/quality tradeoff.
2. For concepts and parameter meanings, read [schedule reference](references/schedule-reference.md).
3. For runnable recipes, use [workflows](references/workflows.md) and the bundled [`scripts/render_schedule.py`](scripts/render_schedule.py) helper.
4. For function signatures, CLI flags, helper outputs, and source-to-helper provenance, use [API reference](references/api-reference.md).
5. If plotting or validation fails, use [troubleshooting](references/troubleshooting.md) before changing model/data settings.
6. When schedule edits will be applied to a real inpainting run, hand off to [inpainting-inference](../inpainting-inference/) for asset checks, config execution, and output validation.

## Bundled helper

- [`scripts/render_schedule.py`](scripts/render_schedule.py): self-contained headless renderer adapted from RePaint's schedule helper. It can read a RePaint-style YAML config or explicit CLI parameters, writes a PNG plot by default, and can also write JSON/CSV summaries for comparison without a GUI.

Start with [workflows](references/workflows.md) for commands, then use [schedule reference](references/schedule-reference.md) to interpret the resulting plot and counts.
