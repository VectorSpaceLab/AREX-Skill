# Train/Test Workflows

## Training semantics

Training loads one YAML config, applies optional `--set` overrides, builds a dataloader/model/optimizer, writes config/logs/checkpoints/tensorboard under:

```text
output/<config-group>/<config-name>/<extra_tag>/
```

Key train arguments:

- `--cfg_file`: required config YAML.
- `--batch_size`: total batch size. In distributed mode it must be divisible by GPU count and is divided per GPU.
- `--epochs`: override `OPTIMIZATION.NUM_EPOCHS`.
- `--workers`: dataloader workers.
- `--extra_tag`: output run tag; defaults to `default`.
- `--ckpt`: resume from a checkpoint with optimizer state when possible.
- `--pretrained_model`: load weights before training.
- `--launcher`: `none`, `pytorch`, or `slurm`.
- `--sync_bn`: convert batch norm to synchronized batch norm.
- `--merge_all_iters_to_one_epoch`: repeat the dataset to compress epochs.
- `--use_amp`: enable mixed precision, also enabled when `OPTIMIZATION.USE_AMP` is true.
- `--set`: trailing config overrides using OpenPCDet's type-checked config updater.

At the end of training, the script evaluates recent checkpoints through the same evaluation utility used by the test workflow.

## Evaluation semantics

Evaluation loads one YAML config and either a single checkpoint or a directory of checkpoints.

Key test arguments:

- `--cfg_file`: required config YAML.
- `--ckpt`: checkpoint path for single-checkpoint evaluation.
- `--eval_all`: repeatedly evaluate all checkpoint files under `--ckpt_dir` or the run's checkpoint directory.
- `--ckpt_dir`: explicit checkpoint directory for `--eval_all`.
- `--eval_tag`: result subdirectory tag.
- `--save_to_file`: write prediction/result files.
- `--infer_time`: sets `CUDA_LAUNCH_BLOCKING=1` to measure latency but can slow evaluation.
- `--max_waiting_mins`: how long repeated evaluation waits after first eval.

Evaluation output lives under the config/run output directory's `eval/` subtree and contains logs, per-epoch folders, tensorboard summaries for repeated evaluation, and optional result files.

## Distributed launchers

The repository's shell launchers are thin wrappers around the train/test scripts. For future tasks, reconstruct commands with the bundled command builder and adapt to the user's cluster.

- PyTorch distributed launcher: set visible GPUs, launch one process per GPU, pass `--launcher pytorch`.
- SLURM launcher: pass `--launcher slurm` and ensure the cluster sets rank/world-size environment variables expected by the utility initializer.
- Use unique `--tcp_port` values when running multiple jobs on one node.

## Checkpoint handling

- `--ckpt` in train resumes optimizer state when present.
- If `--ckpt` is omitted, training scans the run checkpoint directory for the latest loadable checkpoint.
- `--pretrained_model` loads weights but does not resume optimizer/training state.
- Test mode loads checkpoints to CPU first for distributed test when requested by the script.

## Safe verification candidates

After skill generation, low-cost final checks can include:

```bash
python tools/train.py --help
python tools/test.py --help
python scripts/summarize_openpcdet_config.py --cfg <small-config.yaml>
```

Do not run actual train/test without user-approved dataset, checkpoint, GPU, runtime, and time budget.
