---
name: training
description: "Train Transformer translation models with train.py, safe command
  construction, data-mode choices, hyperparameters, scheduler behavior, logs,
  checkpoints, CPU/GPU flags, TensorBoard, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this sub-skill when the task is to plan or debug training with `train.py` without starting an expensive run. It covers the training CLI, data input modes, safe command construction, loss/scheduler smoke checks, logs, checkpoints, device flags, TensorBoard, and recoverable training setup failures.

Do not use this sub-skill to create training data files, translate from a checkpoint, or explain Transformer internals beyond training-facing constructor flags. Route those tasks to the data-preparation, translation, or model-architecture sub-skills.

## Fast routes

- Build a command without running training: use [scripts/build_training_command.py](scripts/build_training_command.py), then confirm the details in [references/cli-reference.md](references/cli-reference.md).
- Validate training helpers and a tiny model/scheduler path before a long run: use [scripts/training_smoke_check.py](scripts/training_smoke_check.py).
- Choose between all-in-one pickle training and BPE-prefix training: read [references/workflows.md](references/workflows.md#data-mode-workflows).
- Recover from missing `-output_dir`, stale README flags, CUDA failures, weight-sharing assertions, or TensorBoard import problems: read [references/troubleshooting.md](references/troubleshooting.md).

## Safe operating pattern

1. Decide the data mode:
   - all-in-one pickle: `-data_pkl DATA.pkl` only;
   - BPE files: `-data_pkl BPE_VOCAB.pkl -train_path TRAIN_PREFIX -val_path VAL_PREFIX` where `.src` and `.trg` files exist for both prefixes.
2. Always include `-output_dir`; `train.py` raises if it is omitted.
3. Prefer `-no_cuda` for CPU-only planning and smoke checks. Omit it only when CUDA is available and desired.
4. Use `scripts/build_training_command.py` to print the exact command. It is safe by default and does not execute training.
5. Run `scripts/training_smoke_check.py --repo-root <checkout>` in an environment with the legacy training dependencies when you need to verify import, loss, model forward, and `ScheduledOptim` behavior.
6. Treat full training as a long-running user action requiring prepared data, a writable output directory, and explicit approval.

## Key runtime facts

- `train.py` uses `torchtext.data.Field`, `Dataset`, `BucketIterator`, and `TranslationDataset`, so it expects the legacy torchtext API rather than modern torchtext datapipes.
- The training loop writes `train.log` and `valid.log` inside `-output_dir`, overwriting existing files with the same names at run start.
- With default `-save_mode best`, the checkpoint is `OUTPUT_DIR/model.chkpt`. With `-save_mode all`, checkpoint files are written in the process working directory, not in `-output_dir`.
- `ScheduledOptim` wraps Adam with the Transformer warmup schedule; it updates the learning rate on every `step_and_update_lr()` call.
- The README examples include a historical `-log` flag, but the current `train.py` parser does not accept it. Omit `-log` from generated commands.
