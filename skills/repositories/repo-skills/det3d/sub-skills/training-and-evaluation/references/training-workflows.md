# Training Workflows

`train.py` loads the config, applies work-directory/resume overrides, initializes
distributed execution when requested, optionally scales `cfg.lr_config.lr_max`
by GPU count, builds the detector and training dataset, and calls
`train_detector`. If the config workflow has two phases, it also builds the
validation dataset.

Before training verify:

- compiled CUDA operators and `spconv` match torch/CUDA;
- dataset info/database files and class order match the config;
- `work_dir` is writable and has checkpoint/log capacity;
- optimizer, LR schedule, epoch count, batch size, and `samples_per_gpu` are
  compatible with GPU memory;
- resume checkpoints contain compatible model keys and optimizer state;
- validation does not use a training transform by accident.

For finetuning, distinguish loading pretrained weights from resuming an exact
optimizer/epoch state. Record every intentional mismatch and inspect missing or
unexpected checkpoint keys rather than silently ignoring them.
