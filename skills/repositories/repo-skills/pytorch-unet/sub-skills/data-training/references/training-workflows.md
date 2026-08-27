# Training workflows

Use this reference for practical Pytorch-UNet training setup and recovery decisions.

## 1. Prepare data before training

1. Put input images in `data/imgs/` and masks in `data/masks/`, or adapt the module-level paths if using the code programmatically.
2. Choose the naming convention:
   - Carvana convention: `data/imgs/<id>.<ext>` and `data/masks/<id>_mask.<ext>`.
   - Generic convention: `data/imgs/<id>.<ext>` and `data/masks/<id>.<ext>`.
3. Run the bundled layout validator before training.
4. Confirm the model arguments:
   - `n_channels=3` for RGB, `1` for grayscale.
   - `--classes` equals the number of discovered mask classes.
5. Choose `--scale`; start with `0.5` unless the user requires full resolution.

## 2. Validate a dataset safely

Use the bundled helper from this sub-skill:

```bash
python scripts/validate_dataset_layout.py --images data/imgs --masks data/masks --carvana --scale 0.5
```

For generic mask names, omit `--carvana`:

```bash
python scripts/validate_dataset_layout.py --images data/imgs --masks data/masks --scale 0.5
```

The helper prints JSON and does not run training, download data, or touch W&B.

## 3. Run training

Preview the underlying training command with the bundled wrapper first. `$REPO_ROOT` is the user's Pytorch-UNet checkout that contains `train.py`:

```bash
python scripts/training_cli_wrapper.py --repo-root "$REPO_ROOT" -- --epochs 5 --batch-size 1 --learning-rate 1e-5 --scale 0.5 --validation 10 --classes 2
```

After the user approves training cost, W&B behavior, checkpoint writes, and backend use, add `--execute`:

```bash
python scripts/training_cli_wrapper.py --repo-root "$REPO_ROOT" --execute --wandb-mode offline -- --epochs 5 --batch-size 1 --learning-rate 1e-5 --scale 0.5 --validation 10 --classes 2
```

For CUDA with mixed precision, include `--amp` in the forwarded training arguments:

```bash
python scripts/training_cli_wrapper.py --repo-root "$REPO_ROOT" --execute --wandb-mode offline -- --epochs 5 --batch-size 2 --scale 0.5 --validation 10 --classes 2 --amp
```

The underlying training loop uses:

- `RMSprop` optimizer with learning rate, weight decay, and momentum.
- `ReduceLROnPlateau` scheduler maximizing validation Dice.
- `CrossEntropyLoss` when `model.n_classes > 1` and `BCEWithLogitsLoss` when `model.n_classes == 1`.
- Dice loss in addition to the main loss.
- Periodic validation through `evaluate(model, val_loader, device, amp)`.

## 4. Resume or fine-tune from a checkpoint

Preview or execute resume arguments through the wrapper:

```bash
python scripts/training_cli_wrapper.py --repo-root "$REPO_ROOT" -- --load checkpoints/checkpoint_epoch5.pth --epochs 10 --classes 2
```

The checkpoint is a state dict plus a `mask_values` metadata key. The CLI removes `mask_values` before `model.load_state_dict`. When resuming, match:

- `--classes`
- `--bilinear`
- input channel assumption (`train.py` hard-codes `n_channels=3` in the CLI path)
- any manual architecture changes

If a user needs grayscale training through the CLI, they must adapt the model construction because the CLI currently hard-codes `n_channels=3`.

## 5. Understand W&B behavior

Training calls `wandb.init(project="U-Net", resume="allow", anonymous="must")`. This means:

- An existing `WANDB_API_KEY` can attach the run to an account.
- Without a key, W&B may create an anonymous run.
- Offline, proxied, or firewalled environments can fail or stall on logging unless W&B offline/disabled settings are configured externally.

A validation-only or parser-only check should not start `train_model`, because that initializes W&B.

## 6. Use CUDA and AMP safely

The code chooses `cuda` when `torch.cuda.is_available()` and otherwise CPU. `--amp` enables PyTorch automatic mixed precision in training/evaluation and uses a CUDA GradScaler object with `enabled=amp`.

CUDA is an acceleration path rather than a semantic requirement. CPU checks can validate data layout and model functionality, but realistic training on high-resolution Carvana data is expected to benefit from CUDA and AMP.

## 7. Recover from CUDA out of memory

The CLI catches `torch.cuda.OutOfMemoryError`, empties the cache, calls `model.use_checkpointing()`, and retries training. Before relying on this fallback, also consider:

- Lowering `--batch-size`.
- Lowering `--scale`.
- Enabling `--amp` on compatible GPUs.
- Reducing image dimensions in the dataset.

Checkpointing trades speed for memory and should be treated as a recovery mechanism.

## 8. Data download recipe classification

The original shell helper prompts for Kaggle credentials, installs or upgrades `kaggle`, downloads challenge zip files, unzips them, moves files into `data/imgs` and `data/masks`, and deletes archives. This is useful evidence for the Carvana workflow, but it is not a safe bundled runtime script because it needs credentials, network access, package mutation, archive extraction, and significant disk writes.

For future agents, describe those prerequisites and ask for approval before running an equivalent data acquisition workflow.
