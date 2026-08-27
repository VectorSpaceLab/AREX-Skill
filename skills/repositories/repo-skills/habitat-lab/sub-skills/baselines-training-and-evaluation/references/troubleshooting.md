# Baselines Troubleshooting

Start with no-training checks: run `habitat-baselines --help`, then compose the target config with `scripts/baselines_cli_probe.py load-config`. Only debug trainer/runtime failures after config composition succeeds.

## Import And Install Problems

Symptoms:

- `habitat-baselines: command not found`.
- `No module named habitat_baselines`.
- CLI entry point imports Habitat but not Habitat-Baselines.

Actions:

- Confirm the `habitat-baselines` package is installed, not only `habitat-lab`.
- Prefer editable installs of both the core package and baselines package in development environments.
- Re-run `python -m habitat_baselines.run --help`; if module form works but console script does not, the environment's script directory is not on `PATH`.
- Do not paste local virtualenv or conda paths into public skill content or reusable commands.

## PyTorch, CUDA, And CPU-Only Inspection

Symptoms:

- `torch.cuda.is_available()` is false.
- GPU-GPU tests skip or fail.
- DD-PPO/distributed training hangs or errors.
- Training is extremely slow on CPU.

Actions:

- Separate config/API inspection from real training. CPU PyTorch is enough for `--help`, config composition, and many import checks.
- For real training/eval, verify PyTorch CUDA compatibility, Habitat-Sim CUDA support, GPU memory, and driver/runtime versions.
- Use `habitat_baselines.num_environments=1` and very small `num_updates` only for smoke tests; do not present CPU smoke output as research training.
- For GPU-GPU paths, confirm Habitat-Sim is installed and CUDA-enabled.

## Missing Data, Scenes, And Checkpoints

Symptoms:

- Dataset path assertions or skipped tests.
- Scene files not found.
- Evaluation loops poll forever for checkpoints.
- `eval_ckpt_path_dir` points to a missing file or empty directory.

Actions:

- Inspect `cfg.habitat.dataset.data_path`, `cfg.habitat.dataset.scenes_dir`, and split-specific path templates after composing the config.
- Download or symlink datasets only with user approval.
- For evaluation, choose a checkpoint file when possible rather than an empty directory.
- Set `habitat_baselines.load_resume_state_config=False` when eval-time overrides should not be replaced by the checkpoint's saved config.

## Hydra Config Errors

Symptoms:

- `Could not find ...` config group errors.
- Override parsing errors around lists, quotes, or `+` prefixes.
- Old commands fail with `--exp-config` or `--run-type`.

Actions:

- Convert old `--exp-config` to `--config-name=<relative config path>`.
- Convert old `--run-type eval` to `habitat_baselines.evaluate=True`.
- Use `+group=option` when adding a new config group that is not already in the defaults list.
- Quote list overrides for the shell, for example `habitat_baselines.eval.video_option='["disk"]'`.
- Use the probe script's `load-config --summary` mode to check the final trainer, dataset, checkpoint, and output fields.

## Trainer Schedule Errors

Symptoms:

- Runtime error saying both `num_updates` and `total_num_steps` are specified.
- Runtime error saying neither update/step limit is specified.
- Runtime error saying both `num_checkpoints` and `checkpoint_interval` are specified.

Actions:

- Set exactly one training-duration key: `habitat_baselines.num_updates=<n>` with `habitat_baselines.total_num_steps=-1`, or `habitat_baselines.total_num_steps=<n>` with `habitat_baselines.num_updates=-1`.
- Set exactly one checkpoint cadence key: `habitat_baselines.num_checkpoints=<n>` with `habitat_baselines.checkpoint_interval=-1`, or `habitat_baselines.checkpoint_interval=<n>` with `habitat_baselines.num_checkpoints=-1`.
- For fast smoke tests, prefer small `num_updates`, `total_num_steps=-1`, and `num_checkpoints=1`.

## Multiprocessing, DD-PPO, And VER

Symptoms:

- Worker process crashes without a clear trainer stack trace.
- Distributed process group remains initialized after a failed run.
- DD-PPO does not use the expected number of GPUs.
- VER uses too much memory or underperforms.

Actions:

- Reduce `habitat_baselines.num_environments` and process counts for diagnosis.
- Confirm Slurm or distributed launch environment variables before expecting DD-PPO multi-rank behavior.
- Clean up failed runs before retrying; tests explicitly destroy initialized torch distributed process groups.
- For VER, tune `habitat_baselines.rl.ver.variable_experience`, `num_inference_workers`, and `overlap_rollouts_and_learn` according to policy size, CPU bottlenecks, and straggler severity.

## TensorBoard And Video Output

Symptoms:

- Assertion requiring `tensorboard_dir` or `video_dir`.
- No videos appear during eval.
- Media writer dependency errors.

Actions:

- Set `habitat_baselines.tensorboard_dir` when using TensorBoard output.
- Set `habitat_baselines.video_dir` and include `"disk"` in `habitat_baselines.eval.video_option` for disk videos.
- Keep `habitat_baselines.eval.video_option=[]` during smoke tests when media dependencies or rendering are not the target.
- Verify optional dependencies such as image/video writers only after config and checkpoint paths are correct.
