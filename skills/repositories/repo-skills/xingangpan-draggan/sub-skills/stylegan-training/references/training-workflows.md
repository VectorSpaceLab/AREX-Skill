# StyleGAN-Human Training Workflows

## Preflight

Before constructing a command, confirm:

1. SHHQ-1.0 access is approved for the intended non-commercial research use.
2. The data path is a directory or zip in the format accepted by the StyleGAN dataset loader.
3. The GPU count, total batch, per-GPU memory, storage, and wall-clock budget are known.
4. The output directory is new or intentionally resumable.
5. The selected environment matches the source’s older StyleGAN2/3 and CUDA assumptions.
6. The execution root is complete. The StyleGAN-Human `training_scripts/sg2` and `training_scripts/sg3` files are modified entry/network files; they may need to be applied to a full StyleGAN2-ADA or StyleGAN3 training tree that also has `dnnlib/`, `training/`, `metrics/`, and `torch_utils/`. Use the builder warning and `--training-root <prepared-root>` to avoid treating patch files as a complete training install.

The builder does not inspect image contents. Use `--validate-data-path` for an existence check only:

```bash
python sub-skills/stylegan-training/scripts/build_training_command.py \
  --repo-root /path/to/DragGAN --version sg2 \
  --data data/SHHQ-1.0 --outdir training_results/sg2 \
  --validate-data-path
```

## SG2-ADA recipe

The README paper-scale recipe is conceptually:

```text
python <StyleGAN-Human SG2 train entry point> \
  --outdir training_results/sg2 \
  --data data/SHHQ-1.0 \
  --gpus 8 --aug noaug --mirror 1 --snap 250 \
  --cfg shhq --square False
```

Build an explicit command for a smaller debug run:

```bash
python sub-skills/stylegan-training/scripts/build_training_command.py \
  --repo-root /path/to/DragGAN --version sg2 \
  --data data/SHHQ-1.0 --outdir training_results/debug-sg2 \
  --gpus 1 --batch 4 --kimg 10 --aug noaug \
  --mirror 1 --square False --snap 1 --dry-run-flag
```

Important SG2 options:

- `--cfg shhq` selects the rectangle-oriented SHHQ base configuration.
- `--square False` preserves the 1024x512 human-image geometry.
- `--mirror 1` enables horizontal dataset flips; use only if appropriate for the data.
- `--aug noaug` follows the README recipe; `ada` or `fixed` changes the augmentation policy.
- `--snap` controls snapshot cadence in ticks; `--kimg` bounds total training duration.
- `--batch` and `--gamma` override config defaults for a controlled small run.

## SG3 recipe

The README paper-scale recipe is conceptually:

```text
python <StyleGAN-Human SG3 train entry point> \
  --outdir training_results/sg3 --cfg stylegan3-r \
  --gpus 8 --batch 32 --gamma 12.4 \
  --mirror 1 --aug noaug --data data/SHHQ-1.0 \
  --square False --snap 250
```

Use the builder to adapt it:

```bash
python sub-skills/stylegan-training/scripts/build_training_command.py \
  --repo-root /path/to/DragGAN --version sg3 \
  --data data/SHHQ-1.0 --outdir training_results/debug-sg3 \
  --gpus 1 --batch 4 --gamma 12.4 --cfg stylegan3-r \
  --aug noaug --mirror 1 --square False --snap 1 --kimg 10 \
  --dry-run-flag
```

SG3 requires `--cfg`, `--data`, `--gpus`, `--batch`, and `--gamma`. It also exposes capacity, learning-rate, augmentation, metrics, snapshot, precision, and worker controls. Change those only with a reason and record them with the run.

## Dry run and resume

Use `--dry-run-flag` to ask the underlying training script to print its resolved training options and exit. The command builder itself never invokes that script. Review the printed dataset resolution, image shape, batch, GPU count, augmentation, support-root warnings, and output path before removing the dry-run flag.

For a resume, use `--resume <compatible-pickle>` and keep the result directory tied to the source run. Do not resume a square model with rectangle data or silently change the generator family/config.

## Output expectations

Training writes a run directory containing an options/config record, logs, snapshots, and network pickles. Snapshot frequency is not image generation frequency. Keep a manifest with the data version, source checkpoint/resume, command, GPU count, seed, and environment version.
