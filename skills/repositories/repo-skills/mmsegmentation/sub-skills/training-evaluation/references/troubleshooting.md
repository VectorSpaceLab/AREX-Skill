# Training and Evaluation Troubleshooting

Use this reference to diagnose MMSegmentation training/testing failures without guessing or launching expensive jobs unnecessarily.

## Fast Triage

Ask for or inspect:

- exact command, including config, checkpoint, launcher, `--cfg-options`, and environment variables;
- whether the user intended resume, fine-tune, validation, test, TTA, visualization, or output formatting;
- the relevant `work_dir`, latest checkpoint name, and JSON log path;
- the first stack trace frame from project/MMEngine code and the first user-facing error message;
- whether CUDA/NPU/distributed/Slurm is involved.

Prefer preflight first:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --work-dir work_dirs/debug
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --out work_dirs/format_results
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/analyze_mmseg_log.py LOG.json --keys loss mIoU
```

## Resume vs Fine-Tune Mistakes

Symptom: the run restarts from iteration 0 when the user expected continuation.

Checks:

- Did the command include `--resume`?
- Does `work_dir` contain the intended latest checkpoint or metadata?
- Did the user set only `load_from=...`?

Fix:

- For interrupted-run continuation, use `--resume` and the same `work_dir`.
- For a specific resume checkpoint, use `--resume --cfg-options load_from=CHECKPOINT`.
- For fine-tuning, use `load_from=CHECKPOINT` without `--resume`; iteration starts from 0 by design.

Wrapper examples:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --resume --work-dir work_dirs/expected_run
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --resume --cfg-options load_from=CHECKPOINT --work-dir work_dirs/expected_run
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --cfg-options load_from=CHECKPOINT --work-dir work_dirs/finetune_run
```

Symptom: optimizer/scheduler state is wrong after fine-tuning.

Fix: do not use `--resume`; use `load_from` only, and adjust the schedule/learning rate in config as needed.

## Missing or Wrong Checkpoint

Symptom: testing fails before `runner.test()` or reports missing checkpoint.

Checks:

- The second positional argument to the testing workflow must be an existing checkpoint file.
- Training checkpoints are usually under `work_dirs/<config-basename>/` unless `--work-dir` or `cfg.work_dir` changed it.
- A symlinked `work_dirs` tree must resolve on the machine that runs the command.

Fix:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG path/to/checkpoint.pth
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --resume --work-dir work_dirs/expected_run
```

Do not pass a directory where the testing workflow expects a file.

## Dataset Path and Annotation Failures

Symptom: file-not-found, empty dataset, missing annotations, or hidden-test failures.

Boundary: dataset/config authoring belongs to `data-configuration`, but training/evaluation troubleshooting should identify whether the launch mode is wrong.

Checks:

- If labels exist, evaluator should not be `format_only=True` unless the user only wants saved predictions.
- If labels do not exist, remove annotation loading from the test pipeline and set evaluator `format_only=True` with `output_dir`.
- Verify that every distributed/Slurm node sees the same data paths.
- For Cityscapes official formatting, use `CityscapesMetric(format_only=True, keep_results=True, output_dir=...)`.

## Output Directory, `format_only`, and `keep_results`

Symptom: predictions are not saved.

Checks:

- `--out OUTPUT_DIR` sets `cfg.test_evaluator.output_dir=OUTPUT_DIR` and `keep_results=True`.
- Direct config formatting needs `test_evaluator.output_dir` set.
- `IoUMetric` and `DepthMetric` save outputs when `output_dir` is not `None`.

Symptom: no metrics are reported.

Checks:

- `format_only=True` intentionally skips evaluation and returns an empty metric dict.
- Hidden-test workflows should not expect metrics without ground truth.

Symptom: Cityscapes format-only construction fails.

Fix:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT --format-only --keep-results --cfg-options test_evaluator.output_dir=work_dirs/cityscapes_submit
```

`CityscapesMetric` asserts that `keep_results=True` when `format_only=True`.

## Visualization Hook Missing or Headless Display

Symptom: `VisualizationHook must be included in default_hooks`.

Fix: add or restore `default_hooks.visualization` with the segmentation visualization hook in the config, or avoid `--show`/`--show-dir` for configs that intentionally omit visualization.

Symptom: display/window error on server.

Fix: prefer `--show-dir DIR` instead of `--show`. `--show` requires an interactive display; `--show-dir` saves rendered outputs through the visualizer.

## AMP and Optimizer Wrapper Failures

Symptom: `--amp` assertion complains about optimizer wrapper type.

Cause: the training workflow only converts `OptimWrapper` to `AmpOptimWrapper`. It warns if the config is already `AmpOptimWrapper` and asserts for other wrapper types.

Fix options:

- Remove `--amp` if the config already uses a custom AMP/mixed-precision wrapper.
- Change config `optim_wrapper.type` to `OptimWrapper` before using the CLI `--amp` shortcut.
- Configure `AmpOptimWrapper` directly in the config when advanced behavior is needed.

## CUDA Unavailable and CPU Limitations

Symptom: CUDA is unavailable, training is extremely slow, or CUDA-only ops fail.

Checks:

- Installed inspection may show a CPU-only torch build or unavailable CUDA.
- Single-process CPU training/testing can follow the same wrapper shape, but full training is usually too slow for routine verification.
- Some models/operators may require compiled MMCV ops or CUDA-specific support.

Fix options:

```bash
CUDA_VISIBLE_DEVICES=-1 python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_test_wrapper.py CONFIG CHECKPOINT
CUDA_VISIBLE_DEVICES=-1 python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --work-dir work_dirs/cpu_debug
```

For GPU workflows, install a CUDA-compatible PyTorch/MMCV stack before blaming config or MMSegmentation code.

## Missing MMCV Ops

Symptom: import failure such as `ModuleNotFoundError: No module named 'mmcv._ext'`.

Cause: some MMSegmentation imports require compiled MMCV ops. This is an environment/build issue, not a training command issue.

Fix options:

- Use help/preflight tools that avoid heavy MMSegmentation imports when possible.
- Install a compatible `mmcv` build for the local PyTorch/CUDA/CPU stack.
- Avoid model families or utilities that require unavailable custom ops until the environment is repaired.

## Distributed Port and Launcher Failures

Symptom: `RuntimeError: Address already in use`.

Fix: choose a unique wrapper `--port`, `PORT`, `MASTER_PORT`, or `env_cfg.dist_cfg.port` value.

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --distributed --gpus 4 --port 29501
MASTER_PORT=29501 python skills/mmsegmentation/sub-skills/training-evaluation/scripts/mmseg_train_wrapper.py CONFIG --slurm --partition PARTITION --job-name JOB --gpus 4
```

Symptom: hang or missing ranks.

Checks:

- Use `--launcher pytorch` only under the distributed wrapper or equivalent launcher.
- Use `--launcher slurm` only under Slurm allocation/wrapper.
- Verify `--nnodes`, `--node-rank`, `--master-addr`, `--port`, `--gpus`, and `--gpus-per-node`.
- Confirm every node has equivalent data/checkpoint/config paths.

## TTA Failures

Symptom: `--tta` fails due to missing config keys.

Cause: the testing workflow expects `cfg.tta_pipeline` and `cfg.tta_model`.

Fix: select a TTA-ready config or add the required TTA config fields. Do not use `--tta` as a generic accuracy flag on configs that do not define TTA.

## Log Analysis Failures

Symptom: upstream log analysis fails because `seaborn` is missing.

Fix: use the bundled analyzer for summaries and optional matplotlib-only plotting:

```bash
python skills/mmsegmentation/sub-skills/training-evaluation/scripts/analyze_mmseg_log.py log.json --keys loss mIoU --plot-out plot.png
```

Symptom: metrics appear at unexpected steps.

Cause: validation JSON records may omit a step or use `step=0`; the parser associates such records with the previous training step.

## Long or Expensive Runs

Do not use full model training, distributed testing, Slurm launch, or 200-iteration benchmarks as routine validation. Safer alternatives:

- CLI help checks.
- wrapper dry-runs and config existence checks.
- `--max-iters 1` or config overrides that bound loops when a real run is approved.
- tiny JSON log fixture with the bundled analyzer.
- selected metric unit tests when the environment has required dependencies.

## Proposed Difficult Usability Cases

- Interrupted run vs fine-tune: given a work directory with a latest checkpoint and a separate pretrained checkpoint, produce the correct commands for true resume, specific-checkpoint resume, and fine-tuning, and explain why optimizer state differs.
- Hidden-test offline formatting: given a test split with no labels, produce a safe wrapper command and evaluator overrides that save PNG predictions, skip metric computation, and preserve Cityscapes outputs when applicable.
