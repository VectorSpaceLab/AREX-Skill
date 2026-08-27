---
name: evaluation
description: "Guides MASt3R-SLAM benchmark dataset manifests, evaluation command
  planning, headless suite runs, output paths, and evo_ape metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# evaluation

Use this sub-skill when the task is about TUM-RGBD, 7-Scenes, EuRoC, or ETH3D
benchmark workflows: dataset acquisition planning, sequence lists, headless
suite runs, `--no-calib` variants, trajectory output paths, or `evo_ape` metrics.

## Triggers

- "run MASt3R-SLAM evaluation"
- "download TUM/EuRoC/ETH3D/7-Scenes"
- "what sequences are in eval_tum.sh"
- "compute APE/evo metrics"
- "print the eval commands"
- "metric-only after a previous run"
- "where are logs for calibrated vs no-calib runs"

## Prerequisites

- Environment, CUDA backend, and checkpoints are owned by
  [setup-and-backends](../setup-and-backends/SKILL.md).
- Single-sequence runtime command details are owned by
  [run-slam](../run-slam/SKILL.md).
- Benchmark runs are long, GPU-heavy, and data-heavy. Print commands and ask for
  approval before executing downloads or full-suite runs.

## First reads and scripts

- [references/evaluation-workflows.md](references/evaluation-workflows.md) for
  suite command shapes and calibration variants.
- [references/dataset-layouts.md](references/dataset-layouts.md) for dataset
  manifests and expected directory layouts.
- [references/metrics-and-outputs.md](references/metrics-and-outputs.md) for
  log/trajectory/groundtruth and `evo_ape` path rules.
- [references/troubleshooting.md](references/troubleshooting.md) for missing
  data/logs/metrics issues.
- [scripts/plan_evaluation.py](scripts/plan_evaluation.py) to reproduce the
  upstream `eval_*.sh` command plan safely.
- [scripts/plan_downloads.py](scripts/plan_downloads.py) to print dataset
  download manifests without performing network actions.

## Safe workflow

1. Print the download plan:

   ```bash
   python sub-skills/evaluation/scripts/plan_downloads.py --suite tum --commands
   ```

2. Print the evaluation plan:

   ```bash
   python sub-skills/evaluation/scripts/plan_evaluation.py --suite tum --no-calib
   ```

3. Verify checkpoints, datasets, and available runtime budget.
4. Execute only the approved subset, usually one sequence first.
5. Run metric-only mode when trajectories already exist instead of rerunning
   SLAM.

## Important suite differences

- TUM, 7-Scenes, and EuRoC support both calibrated and no-calibration variants
  in the upstream scripts.
- ETH3D uses the `eth3d.yaml` evaluation config and does not expose `--no-calib`
  in the upstream eval script.
- All evaluation scripts run `main.py` in single-threaded, headless mode and
  then call `evo_ape tum ... -as`.

## Boundary decisions

This sub-skill adapts the upstream shell scripts into print-first Python
planners. It should not auto-download archives or run multi-hour evaluations
unless the user explicitly approves that side effect.
