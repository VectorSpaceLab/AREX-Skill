# Evaluation Troubleshooting

## When to read

Read this when suite downloads, benchmark runs, trajectory logs, or `evo_ape`
metrics fail.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `evo_ape` cannot open the trajectory file | SLAM run did not finish, `--save-as` differs from expected path, or metric-only mode ran too early | Use `plan_evaluation.py` to print the expected `logs/.../<seq>.txt` path and verify the file exists. |
| `evo_ape` cannot open groundtruth | Dataset layout or bundled groundtruth path is wrong | Check suite-specific groundtruth rules in `metrics-and-outputs.md`. |
| ETH3D with `--no-calib` is requested | Upstream ETH3D eval script has no `--no-calib` branch | Explain the limitation; use `eth3d.yaml` unless the user explicitly designs a custom no-calib run through `run-slam`. |
| Evaluation starts a visible window | `--no-viz` missing | Use the bundled planner, which includes `--no-viz` for run commands. |
| Suite run takes too long or exhausts memory | Full suites are GPU-heavy and data-heavy | Run one sequence first, increase `dataset.subsample`, or use metric-only mode when logs exist. |
| Dataset download fails | Network, storage, URL, or license issue | Print the commands with `plan_downloads.py`, confirm storage/network, and retry only approved archives. |
| A no-calib run still behaves calibrated | Wrong config template or old generated file reused | Generate fresh templates and ensure `eval_no_calib.yaml` sets `use_calib: False`. |

## Before escalating

1. Print the exact suite commands with `plan_evaluation.py`.
2. Validate the dataset path with `run-slam/scripts/validate_inputs.py`.
3. Confirm checkpoints and CUDA with `setup-and-backends`.
4. If only metrics fail, inspect trajectory and groundtruth files before rerunning
   the expensive SLAM phase.
