# Checkpoints and resume semantics

StyleTTS2 training checkpoints are ordinary PyTorch state dictionaries saved by the stage launchers. The path semantics are config-driven and can be surprising, so resolve them before running a long job.

## Files written by each stage

| Stage | Periodic checkpoint name | Final alias | Other files in `log_dir` |
| --- | --- | --- | --- |
| First stage | `epoch_1st_%05d.pth` when the epoch matches `save_freq` | `log_dir/<first_stage_path>` at the end of training; default key value is `first_stage.pth` | copied config, `train.log`, `tensorboard/` |
| Second stage | `epoch_2nd_%05d.pth` when the epoch matches `save_freq` | None in the source launcher | copied config, `train.log`, `tensorboard/` |
| Fine-tune | `epoch_2nd_%05d.pth` when the epoch matches `save_freq` | None in the source launcher | copied config, `train.log`, `tensorboard/` |
| Fine-tune accelerate | `epoch_2nd_%05d.pth` when the epoch matches `save_freq` | None in the source launcher | copied config, `train.log`, `tensorboard/` |

Each saved state contains at least:

- `net`: one state dict per named model module.
- `optimizer`: the optimizer/scheduler wrapper state.
- `iters`: training iteration counter.
- `val_loss`: validation loss estimate from that save point.
- `epoch`: epoch index used by the launcher.

## Path semantics

- `log_dir` is interpreted by the training process. When using the bundled helper, the process working directory is the repo root, so relative `log_dir` values are relative to that checkout.
- First-stage final output is `log_dir/<first_stage_path>`. If `first_stage_path` is a relative string, it is relative to `log_dir`. If it is absolute, Python path joining treats it as an absolute path.
- `pretrained_model` is passed directly to `torch.load`. With the bundled helper, a relative value is relative to the repo root.
- The second-stage and fine-tune first-stage fallback branch computes `first_stage_path` under `log_dir`; users often fail here by placing `first_stage.pth` somewhere else while leaving `log_dir` unchanged.

## Load paths by workflow

### First stage

If `pretrained_model` is non-empty, first stage calls `load_checkpoint(model, optimizer, pretrained_model, load_only_params=<config value>)`. Use this only for an intentional restart or transfer; otherwise keep `pretrained_model` empty for from-scratch first-stage training.

### Second stage from first-stage checkpoint

When `pretrained_model` is empty or `second_stage_load_pretrained` is false:

1. `first_stage_path` must be non-empty.
2. The source launcher loads `log_dir/<first_stage_path>` with `load_only_params=True`.
3. It ignores these modules while loading: `bert`, `bert_encoder`, `predictor`, `predictor_encoder`, `msd`, `mpd`, `wd`, and `diffusion`.
4. It copies `style_encoder` into `predictor_encoder` after loading.

This is a weight-transfer path from first-stage acoustic/style modules, not a full optimizer resume.

### Second stage or fine-tune from a full pretrained checkpoint

When both `pretrained_model` is non-empty and `second_stage_load_pretrained: true`, the launcher loads `pretrained_model` directly and does not require `first_stage_path`.

This is the expected path for fine-tuning from a LibriTTS-style second-stage checkpoint. The fine-tune config defaults to `load_only_params: true`, which loads weights but resets optimizer and epoch/iteration counters.

## `load_only_params` caveats

The shared `load_checkpoint` helper behaves as follows:

- It loads only matching module names and uses non-strict module loading.
- It skips any module whose name is listed in `ignore_modules`.
- It sets all loaded modules to evaluation mode before the training script later switches needed modules back to train mode.
- If `load_only_params` is `true`, it does not restore optimizer state, epoch, or iteration counters; it returns epoch and iterations as zero.
- If `load_only_params` is `false`, it restores `state["epoch"]`, `state["iters"]`, and the optimizer state. Use this only when resuming the same architecture and optimizer layout.

Practical rules:

- For fine-tuning or changing data/speaker setup, prefer `load_only_params: true`.
- For exact continuation of an interrupted same-stage run, use the latest compatible periodic checkpoint and set `load_only_params: false` only if the optimizer/module layout matches.
- For second-stage training after first-stage, do not expect optimizer resume from `first_stage_path`; that branch intentionally loads only compatible model weights.
- For DataParallel checkpoints, keep the same stage family when resuming if possible. Non-strict loading is forgiving, but it can hide missing or mismatched modules; check logs for which module keys report as loaded.

## TensorBoard and log recovery

- Training logs are written to `log_dir/train.log`.
- TensorBoard event files are under `log_dir/tensorboard/`.
- The source launchers copy the active config into `log_dir`; use that copied config to audit what settings produced a checkpoint.
- If a run crashes after writing a periodic checkpoint, resume from that checkpoint deliberately rather than assuming the final first-stage alias was updated.
