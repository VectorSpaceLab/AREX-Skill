# Training Config Reference

## Purpose

Use this reference to understand what the experiment JSON configs require and how the bundled training runner validates them.

## Shared Config Structure

Common top-level sections:

- `network.arch`: usually `Custom`, which resolves to the selected experiment directory's model definition.
- `hp`: inference/tracking hyperparameters such as `instance_size`, `base_size`, `out_size`, `seg_thr`, `penalty_k`, `window_influence`, and `lr`.
- `lr`: scheduler type and learning-rate ranges. Base/SiamRPN configs use log schedule with warmup.
- `loss.weight`: `[cls, loc, mask]` for SiamMask or `[cls, loc]` for SiamRPN.
- `anchors`: stride, ratios, scales, and rounding; defaults are stride 8, ratios `[0.33, 0.5, 1, 2, 3]`, scales `[8]`.
- `train_datasets` and optional `val_datasets`: dataset roots, annotation JSONs, sizes, counts, and augmentation settings.

## Dataset Fields

Each dataset row normally contains:

- `root`: path to preprocessed crop data, usually relative to the experiment directory.
- `anno`: path to generated training/validation JSON, usually relative to the experiment directory.
- `num_use`: optional number of samples to use from that dataset.
- `frame_range`: temporal window for positive pairs.
- `mark`: sometimes supplied in dataset code to distinguish mask-capable datasets such as COCO/YouTube-VOS.

Use the training runner's dry-run output to spot missing `root`/`anno` paths before starting GPU work.

## Family-Specific Signals

| Family | Config signals | Data emphasis | Notes |
| --- | --- | --- | --- |
| SiamMask base | `loss.weight` has three values and nonzero cls/loc/mask weights | YouTube-VOS, VID, COCO, DET plus VID validation | Produces base checkpoints used before refine training. |
| SiamMask refine/sharp | `loss.weight` often `[0, 0, 36]`; search size can be smaller for refine training | YouTube-VOS and COCO | Train with a base checkpoint as `--pretrained`. |
| SiamRPN ResNet | `loss.weight` has two values | YouTube-VOS, VID, COCO, DET plus VID validation | Box-only; downstream tracking does not use mask/refine. |

## Validation Strategy

Before `--run`:

1. Run the data-preparation layout checker for `--dataset training`.
2. Run the training helper in dry-run mode; it parses config JSON, prints dataset roots/annotations, and reports missing paths.
3. Confirm checkpoint/pretrained paths relative to the experiment directory.
4. Confirm GPU selection with `--gpu` and the root CUDA probe.
5. Reduce `--batch` or workers for smaller GPUs or memory-constrained hosts.

## Config Gotchas

- Config paths are relative to the experiment directory when native scripts run.
- `load_config` mutates parser args by setting `args.arch` from `network.arch`.
- Missing `loss`/`lr`/`clip` fields get defaults, but missing `train_datasets` paths are fatal later.
- Refine training freezes feature/RPN components and trains mask/refine components; using a wrong base checkpoint can silently produce poor masks.
