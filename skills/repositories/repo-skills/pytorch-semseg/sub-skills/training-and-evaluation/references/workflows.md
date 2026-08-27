# Training and Validation Workflows

This reference distills the repository training and validation scripts into a
safe operating checklist. It is self-contained for future use; do not rely on
opening the original source files to understand the workflow.

## Safety contract

The bundled helpers under `scripts/` only build commands and emit warnings. They
never execute training or validation. Full runs are dataset-bound, can be long
running, can use substantial CPU/GPU memory, and training writes TensorBoard logs,
copied configs, logger files, and best-checkpoint files under a `runs/` tree.

Before a full run, confirm all of the following:

- The config has already passed schema and path review through `data-and-configs`.
- Dataset roots and split files/images are available on the machine that will run the command.
- For validation, the checkpoint exists and matches the selected model and number of classes.
- The Python environment can import PyTorch, torchvision, tqdm, PyYAML, tensorboardX for training, and the repository package modules.
- The user has approved expected compute time, dataset reads, worker processes, and training log/checkpoint writes.

## Training entry point

Canonical command shape:

```bash
python train.py --config CONFIG.yml
```

`train.py` has a built-in default config path, but future agents should prefer
an explicit `--config` because bundled example configs may contain
machine-specific dataset paths and very expensive iteration counts.

Dry-run builder:

```bash
python scripts/build_train_command.py --config CONFIG.yml
```

The builder prints a shell-quoted command and warnings about missing files,
absolute or machine-specific dataset paths, expensive iteration counts, resume
paths, modern PyYAML compatibility, and known legacy key drift. It does not
validate the full schema; route deeper config questions to `data-and-configs`.

## Training loop wiring

The training workflow performs the following steps in order:

1. **Seeds.** Uses `cfg.get("seed", 1337)` for `torch.manual_seed`,
   `torch.cuda.manual_seed`, NumPy, and Python `random`. It does not set
   deterministic cuDNN flags or a DataLoader worker seed function.
2. **Device.** Selects `cuda` when `torch.cuda.is_available()` is true,
   otherwise `cpu`.
3. **Augmentations.** Reads `training.augmentations` if present and creates a
   composed augmentation object for the training loader only.
4. **Loaders.** Uses `get_loader(data.dataset)`, then constructs train and val
   dataset objects with `data.path`, `train_split`, `val_split`, and
   `(img_rows, img_cols)`. The train loader uses augmentations; the validation
   loader inside training does not.
5. **DataLoader.** Uses `training.batch_size` and `training.n_workers` for both
   train and validation DataLoaders. Training shuffles; validation does not.
6. **Classes and metrics.** Takes `n_classes` from the training dataset and
   creates `runningScore(n_classes)` plus an `averageMeter` for validation loss.
7. **Model.** Calls `get_model(cfg["model"], n_classes)`, moves it to the
   selected device, then wraps it with `torch.nn.DataParallel` using the current
   CUDA device count.
8. **Optimizer.** Calls `get_optimizer(cfg)` and passes all
   `training.optimizer` fields except `name` to the optimizer constructor.
9. **Scheduler.** Calls `get_scheduler(optimizer, training.lr_schedule)`. The
   scheduler is stepped once per training iteration before the forward pass.
10. **Loss.** Calls `get_loss_function(cfg)` and invokes the returned loss as
    `loss_fn(input=outputs, target=labels)`.
11. **Resume.** If `training.resume` is not null and points to a file, loads
    `model_state`, `optimizer_state`, `scheduler_state`, and `epoch`, then
    resumes from that iteration. If the file is absent, the script logs the
    absence and starts from scratch.
12. **Training iteration.** Moves images/labels to the device, runs forward,
    backward, optimizer step, and periodic train-loss logging.
13. **Periodic validation.** At `training.val_interval` and at the final
    iteration, evaluates on the validation DataLoader, updates `runningScore`,
    logs validation loss and metrics, and resets validation meters.
14. **Best checkpoint.** When `Mean IoU : \t` is at least the previous best,
    saves a checkpoint dictionary in the current TensorBoard run directory as
    `<arch>_<dataset>_best_model.pkl`.

Important training side effects:

- Creates `runs/<config-stem>/<random-run-id>/`.
- Copies the config file into that log directory.
- Writes a timestamped logger file and TensorBoard event files.
- Writes best checkpoints into the same log directory.

## Training examples

Build and inspect a command for an existing config:

```bash
python scripts/build_train_command.py --config configs/experiment.yml
```

Use a specific interpreter or script location without executing anything:

```bash
python scripts/build_train_command.py \
  --python python3 \
  --script train.py \
  --config configs/experiment.yml
```

Only run the printed command manually after resolving warnings. Do not start a
full training run merely to check that a config parses; use `data-and-configs`
for static config validation first.

## Validation entry point

Canonical command shape:

```bash
python validate.py --config CONFIG.yml --model_path CHECKPOINT.pkl \
  --eval_flip --measure_time
```

Validation supports both positive and negative boolean flags:

- `--eval_flip` / `--no-eval_flip`: enables or disables horizontal flip averaging.
- `--measure_time` / `--no-measure_time`: enables or disables per-iteration fps printing.

The source defaults both booleans to true. The dry-run builder prints explicit
boolean flags so the resulting command is unambiguous:

```bash
python scripts/build_validate_command.py \
  --config CONFIG.yml \
  --model_path CHECKPOINT.pkl \
  --no-eval_flip \
  --no-measure_time
```

## Validation loop wiring

The validation workflow performs these steps:

1. **Device.** Selects CUDA if available, otherwise CPU.
2. **Loader.** Uses `get_loader(data.dataset)` and constructs the validation
   dataset with `data.path`, `val_split`, `is_transform=True`, and
   `(img_rows, img_cols)`.
3. **DataLoader.** Uses `training.batch_size` but hard-codes `num_workers=8`.
   This can be excessive on small machines even if the config has a different
   `training.n_workers` value.
4. **Metrics.** Creates `runningScore(n_classes)` from the loader's class count.
5. **Model.** Calls `get_model(cfg["model"], n_classes)`, moves the model to the
   device, loads `torch.load(model_path)["model_state"]` through
   `convert_state_dict`, loads that state into the model, and switches to eval mode.
6. **Flip averaging.** With `--eval_flip`, computes outputs for original images
   and horizontally flipped images, reverses the flipped outputs, averages the
   two output arrays, then takes `argmax` over classes. This roughly doubles
   model compute and memory traffic.
7. **No flip.** With `--no-eval_flip`, takes the class argmax directly from the
   model output tensor.
8. **Timing.** With `--measure_time`, prints fps for each validation batch as
   `batch_size / elapsed_time`. Treat this as an approximate script-level number,
   not a rigorous benchmark.
9. **Metrics.** Updates `runningScore` with ground-truth and predicted labels,
   then prints aggregate score keys and one class-IoU value per class index.

## Checkpoint, log, and metric interpretation

Use [checkpoints-and-metrics.md](checkpoints-and-metrics.md) when you need to
explain checkpoint fields, TensorBoard tags, `convert_state_dict`, aggregate
metric keys, class IoU, fps output, or NaN metrics.

## Skip criteria for expensive runs

Skip or defer full `train.py` when any of these are true:

- Dataset roots, split files, or optional dataset-specific paths are missing.
- The config still contains machine-specific absolute paths that have not been rewritten.
- The config has very large `train_iters`, high `n_workers`, or batch sizes that the user has not approved.
- The run would write logs/checkpoints to a location the user has not approved.
- Training is only needed to validate command syntax; use the dry-run builder and config validator instead.
- Modern dependency compatibility is unresolved, especially PyYAML loader behavior or required imports.

Skip or defer full `validate.py` when any of these are true:

- The checkpoint file is missing or has an unknown format.
- The checkpoint architecture/classes do not match the config.
- The validation dataset path or split is unavailable.
- CPU-only execution would be too slow for the dataset and the user has not approved it.
- The user needs single-image prediction rather than dataset metrics; route to `single-image-inference`.
