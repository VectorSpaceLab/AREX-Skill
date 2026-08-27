# Evaluation Troubleshooting

## W&B prompts, login errors, or network failures

Symptoms:
- The run asks for W&B login.
- Evaluation stalls or errors before logging metrics.
- The environment has no network access.

Recover:
1. Prefer `WANDB_MODE=disabled python slam.py --config <config> --eval`.
2. If that is not enough, create a config copy with `Results.use_wandb: false`,
   `Results.use_gui: false`, `Results.eval_rendering: true`, and
   `Results.save_results: true`, then run without `--eval`.
3. Do not put credentials in configs or bundled scripts.

## LPIPS or TorchMetrics fails

Symptoms:
- Import errors involving `torchmetrics.image.lpip`.
- Runtime attempts to fetch an AlexNet/LPIPS weight.
- CUDA errors during rendering metric computation.

Likely causes:
- Missing or incompatible `torchmetrics`, `lpips`, or `torchvision`.
- No CUDA device or insufficient VRAM.
- Network is unavailable for a first-time weight/cache fetch.

Recover:
1. Run the root environment checker with `--require-cuda`.
2. Verify `torch`, `torchvision`, `torchmetrics`, and `lpips` are installed in
   the active MonoGS environment.
3. If network/caches are blocked, skip rendering metrics and keep ATE/trajectory
   evaluation only, or pre-stage model weights under user-approved cache policy.

## Empty or invalid ATE trajectory outputs

Symptoms:
- `plot/trj_final.json` is missing or has no keyframes.
- evo reports alignment or empty-trajectory errors.

Likely causes:
- The run did not initialize enough keyframes.
- Dataset ground-truth files are missing or malformed.
- The process was interrupted before final evaluation.

Recover:
1. Validate the config/data with the [`data-and-configs`](../../data-and-configs/SKILL.md) validator.
2. Run a shorter non-eval smoke until initialization/keyframes appear in logs.
3. Re-run evaluation only after the dataset and CUDA path are stable.

## No timestamped result directory appears

Symptoms:
- `Results.save_dir` exists but no new timestamped child appears.
- `config.yml` is absent.

Likely causes:
- `Results.save_results` was false.
- The config lacked `Dataset.dataset_path` or the save-dir bucket could not be
  computed.
- The run crashed before save setup.

Recover:
1. Use `--eval` or set `Results.save_results: true` in a config copy.
2. Ensure offline configs have a valid `Dataset.dataset_path`.
3. Check install/CUDA errors before debugging evaluation logic.
