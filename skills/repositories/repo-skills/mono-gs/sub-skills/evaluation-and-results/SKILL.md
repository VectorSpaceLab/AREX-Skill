---
name: evaluation-and-results
description: "Evaluate MonoGS runs, inspect saved result trees, and handle
  W&B-safe metric workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation and Results

Use this sub-skill when the user asks for MonoGS metrics, `--eval`, saved
outputs, ATE/rendering scores, result folders, W&B behavior, or final Gaussian
PLY artifacts.

## Route away

- To choose a monocular/RGB-D/stereo run command before evaluation, use
  [`offline-slam`](../offline-slam/SKILL.md).
- To validate dataset roots or YAML inheritance, use
  [`data-and-configs`](../data-and-configs/SKILL.md).
- To debug CUDA installation, extension imports, or Open3D dependencies, use
  [`environment-setup`](../environment-setup/SKILL.md).
- To operate a RealSense camera or the live GUI, use
  [`live-demo`](../live-demo/SKILL.md).

## Fast path

1. Confirm the SLAM command already works on the selected config; evaluation is
   not a substitute for environment or dataset setup.
2. Decide whether to use the built-in evaluation flag:
   - `python slam.py --config <config> --eval` forces `save_results=True`,
     `use_gui=False`, `eval_rendering=True`, and `use_wandb=True`.
   - If W&B login/network is not available, prefer
     `WANDB_MODE=disabled python slam.py --config <config> --eval`.
   - For a W&B-free custom evaluation, copy the config and set
     `Results.save_results: true`, `Results.use_gui: false`,
     `Results.eval_rendering: true`, and `Results.use_wandb: false`, then omit
     `--eval`.
3. After a run, inspect the timestamped result directory with
   [scripts/summarize_results.py](scripts/summarize_results.py).
4. Read [references/results-and-metrics.md](references/results-and-metrics.md)
   before interpreting ATE, PSNR, SSIM, LPIPS, FPS, or PLY outputs.

## Bundled references

- [Evaluation workflows](references/evaluation-workflows.md) explains built-in
  `--eval`, W&B-safe modes, and evaluation commands.
- [Results and metrics](references/results-and-metrics.md) maps result-tree
  files to MonoGS evaluation code paths.
- [Troubleshooting](references/troubleshooting.md) covers missing metrics,
  W&B prompts, LPIPS downloads, empty trajectories, and rendering failures.
- [scripts/summarize_results.py](scripts/summarize_results.py) summarizes a
  result root without importing the MonoGS checkout.
