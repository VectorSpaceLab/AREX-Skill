# Training CLI reference

Use this reference when constructing or reviewing Pytorch-UNet training commands. The repository's public training surface is the `train.py` script in a Pytorch-UNet checkout. This generated skill bundles `scripts/training_cli_wrapper.py` so future agents can preview or intentionally execute that script against a user-provided checkout instead of depending on the checkout used during skill generation.

## Safe wrapper usage

Preview a training command without running training:

```bash
python scripts/training_cli_wrapper.py --repo-root "$REPO_ROOT" -- --epochs 5 --batch-size 1 --learning-rate 1e-5 --scale 0.5 --validation 10 --classes 2
```

Run parser help through the wrapper when a safe CLI check is needed:

```bash
python scripts/training_cli_wrapper.py --repo-root "$REPO_ROOT" --execute -- -h
```

Execute real training only after the user approves data access, W&B behavior, checkpoint writes, backend use, and runtime cost:

```bash
python scripts/training_cli_wrapper.py --repo-root "$REPO_ROOT" --execute --wandb-mode offline -- --epochs 5 --batch-size 1 --learning-rate 1e-5 --scale 0.5 --validation 10 --classes 2
```

`$REPO_ROOT` should point to the user's Pytorch-UNet checkout containing `train.py`, `unet/`, and `utils/`.

## Verified parser contract

The training CLI description is:

```text
Train the UNet on images and target masks
```

Verified options accepted by the underlying `train.py` parser:

| Option | Default | Meaning |
| --- | --- | --- |
| `--epochs E`, `-e E` | `5` | Number of training epochs. |
| `--batch-size B`, `-b B` | `1` | Batch size for training and validation dataloaders. |
| `--learning-rate LR`, `-l LR` | `1e-5` | RMSprop learning rate. |
| `--load FILE`, `-f FILE` | `False` | Load a model checkpoint state dict before training. |
| `--scale SCALE`, `-s SCALE` | `0.5` | Downscaling factor applied to images and masks. Must satisfy `0 < scale <= 1`. |
| `--validation VAL`, `-v VAL` | `10.0` | Validation percentage from `0` to `100`; code divides by `100` before splitting. |
| `--amp` | off | Enable automatic mixed precision. Most useful on CUDA-capable GPUs. |
| `--bilinear` | off | Construct `UNet(..., bilinear=True)`. Checkpoints must match this setting. |
| `--classes CLASSES`, `-c CLASSES` | `2` | Number of output classes. |
| `-h`, `--help` | n/a | Print parser help. |

## Common argument sets

Short custom-data training arguments:

```bash
--epochs 5 --batch-size 1 --learning-rate 1e-5 --scale 0.5 --validation 10 --classes 2
```

CUDA/AMP-oriented arguments when a compatible GPU is available:

```bash
--epochs 5 --batch-size 2 --scale 0.5 --validation 10 --classes 2 --amp
```

Resume from a checkpoint:

```bash
--load checkpoints/checkpoint_epoch5.pth --epochs 10 --classes 2
```

If the checkpoint was saved with `--bilinear`, include `--bilinear` when loading it. If it was saved with a different class count, use the matching `--classes` value.

## Side effects of real training

A real training run can:

- Scan all masks with multiprocessing to discover `mask_values`.
- Initialize a W&B run with project name `U-Net`, resume mode `allow`, and anonymous mode `must`.
- Split data deterministically using a PyTorch generator seeded with `0`.
- Save checkpoints under `./checkpoints/` as `checkpoint_epoch{epoch}.pth` when `save_checkpoint=True` in `train_model`.
- Use CUDA if `torch.cuda.is_available()`; otherwise CPU.

Do not start training just to inspect flags. Use the bundled dataset validator, environment checker, model smoke check, and wrapper dry run first.

## Relationship to APIs

The underlying CLI constructs:

```python
model = UNet(n_channels=3, n_classes=args.classes, bilinear=args.bilinear)
```

The `train_model` function signature includes additional programmatic parameters not exposed as CLI flags, such as `save_checkpoint`, `weight_decay`, `momentum`, and `gradient_clipping`. If a user needs those, use a Python script or notebook that calls `train_model` directly rather than trying to pass unsupported CLI flags.
