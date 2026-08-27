# Evaluation Workflows

## When to read

Read this when planning suite-level TUM-RGBD, 7-Scenes, EuRoC, or ETH3D runs.

## Source-script behavior distilled

Each upstream evaluation shell script has two phases:

1. Run `python main.py` for every sequence in headless mode with `--no-viz` and
   a suite-specific `--save-as` path.
2. Run `evo_ape tum <groundtruth> <trajectory> -as` for every sequence.

TUM, 7-Scenes, and EuRoC also support `--no-calib`. The `--print` flag skips
phase 1 and prints/runs only the metric commands. ETH3D supports `--print` but
not `--no-calib`.

## Bundled planner examples

Print calibrated TUM commands:

```bash
python sub-skills/evaluation/scripts/plan_evaluation.py --suite tum
```

Print no-calibration EuRoC commands:

```bash
python sub-skills/evaluation/scripts/plan_evaluation.py --suite euroc --no-calib
```

Print metrics only after previous runs:

```bash
python sub-skills/evaluation/scripts/plan_evaluation.py --suite 7-scenes --metric-only
```

Execute only after explicit approval:

```bash
python sub-skills/evaluation/scripts/plan_evaluation.py --suite tum --sequence rgbd_dataset_freiburg1_room --execute
```

## Config mapping

| Suite | Calibrated config | No-calib config | Save-as prefix |
| --- | --- | --- | --- |
| TUM | `eval_calib.yaml` | `eval_no_calib.yaml` | `tum/calib/<seq>` or `tum/no_calib/<seq>` |
| 7-Scenes | `eval_calib.yaml` | `eval_no_calib.yaml` | `7-scenes/calib/<seq>` or `7-scenes/no_calib/<seq>` |
| EuRoC | `eval_calib.yaml` | `eval_no_calib.yaml` | `euroc/calib/<seq>` or `euroc/no_calib/<seq>` |
| ETH3D | `eth3d.yaml` | not supported by source script | `eth3d/<seq>` |

## Recommended evaluation discipline

- Start with one sequence before launching the full suite.
- Use `--metric-only` when trajectory logs already exist.
- Keep dataset, checkpoints, and logs on fast storage.
- Treat full-suite downloads and runs as expensive network/GPU work requiring
  explicit user approval.
