# PartNet part-segmentation reference

## Scope and preparation boundary

The documented experiment uses PartNet v0 fine-grained semantic part
segmentation, normally level 3, one category at a time. PartNet access and
release files are controlled outside this skill. Do not download, request
access, unpack archives, or use an externally hosted checkpoint from a bundled
command. Prepare the files through an approved process, then validate the
layout below.

The command shapes below target an independently staged implementation. Replace
the neutral entrypoint and resource placeholders only; never open or run a file
from an original source checkout. The bundled smoke in the parent skill remains
the only direct executable.

The loader's default arguments are `dataset=sem_seg_h5`, category `Bed`,
level `3`, and phase `train`. It expects the raw dataset marker to exist under
`<data_dir>/raw/sem_seg_h5`; if it is absent, the source raises a preparation
error rather than providing a safe public download path.

## Category and level mapping

The integer passed to `--category` indexes this exact list:

```text
0 Bag                 1 Bed                 2 Bottle
3 Bowl                4 Chair               5 Clock
6 Dishwasher          7 Display             8 Door
9 Earphone            10 Faucet             11 Hat
12 Keyboard           13 Knife              14 Lamp
15 Laptop             16 Microwave          17 Mug
18 Refrigerator       19 Scissors           20 StorageFurniture
21 Table               22 TrashCan           23 Vase
```

The default is `--category 1`, which maps to `Bed`. The source configuration
notes that the paper experiment used level 3 and a subset of category ids:
`1, 2, 4, 5, 6, 7, 8, 9, 10, 13, 14, 16, 18, 20, 21, 22, 23`. A category id
outside the list is invalid; a category that has no prepared level-3 files is a
data-preparation failure, not a reason to change the model class count.

## Raw and processed layout

For the `sem_seg_h5` path, the raw files are expected in a category-level
folder such as:

```text
<data_dir>/raw/sem_seg_h5/Bed-3/
    train-*.h5
    test-*.h5
    val-*.h5
```

The processing code searches each split with the corresponding prefix and
reads HDF5 keys `data` and `label_seg`. `data[:, :3]` becomes `pos` and
`label_seg` becomes integer `y`. The processed output is organized as:

```text
<data_dir>/processed/sem_seg_h5/level_3/Bed-3/
    train.pt
    test.pt
    val.pt
```

The category name and level are part of the processed path. If raw data is
replaced or the category/level changes, remove or regenerate only the matching
processed record through the approved preparation workflow; do not reuse a
checkpoint from another category or level without an explicit compatibility
check.

## Train and test configuration

Reference train shape:

```bash
<partnet-entrypoint> --phase train --category 1 --level 3 \
  --data_dir <prepared-partnet-root>
```

Reference alternate convolution:

```bash
<partnet-entrypoint> --phase train --category 1 --conv mr \
  --data_dir <prepared-partnet-root>
```

Reference test shape:

```bash
<partnet-entrypoint> --phase test --category 1 --level 3 \
  --n_blocks 28 --n_filters 64 \
  --pretrained_model <partnet-checkpoint> \
  --data_dir <prepared-partnet-root> --test_batch_size 1
```

Source parser flags and defaults:

| Group | Flags |
|---|---|
| Dataset | `--data_dir`, `--dataset sem_seg_h5`, `--category 1`, `--level 3`, `--in_channels 3`, `--batch_size 6`, `--test_batch_size 10`, `--data_augment` |
| Model | `--k 9`, `--block res|plain` (dense is not implemented by this PartNet architecture), `--conv edge|mr` in this dense model, `--act relu|prelu|leakyrelu`, `--norm batch|instance`, `--n_filters 64`, `--n_blocks 28`, `--dropout .5`, `--use_dilation`, `--epsilon .2`, `--stochastic`, `--bias` |
| Runtime/checkpoint | `--phase train|test`, `--use_cpu`, `--pretrained_model`, `--multi_gpus`, `--seed` |
| Training | `--total_epochs 500`, `--iter -1`, `--lr_adjust_freq 50`, `--lr .005`, `--lr_decay_rate .9`, `--exp_name`, `--root_dir` |

The CLI converts the numeric category to its name before creating the dataset.
It uses `DenseDataLoader`; inputs are `[B,3,N,1]`, outputs are
`[B,n_classes,N]` log-probabilities, and training uses `NLLLoss`. The training
code clips labels above `n_classes-1` as a legacy safeguard; do not use this to
hide a wrong category or corrupted label mapping.

For test mode, supply a checkpoint and the same category, level, `k`, block,
convolution, filters, and blocks used to train it. The source creates result
folders relative to the checkpoint directory. An absolute checkpoint path is
less ambiguous than relying on the entrypoint's current directory, but the
checkpoint itself must have been provisioned separately.

## Evaluation and metrics

The test path computes:

- **part mIoU**: aggregate intersection/union by part class and average the
  non-background entries (`part_intersect[1:] / part_union[1:]`);
- **shape mIoU**: average per-shape IoU over classes present in that shape.

Do not compare a PartNet part mIoU with S3DIS semantic mIoU. Both are pointwise
IoU-like measures but have different label spaces and averaging conventions.
A meaningful evaluation requires a matching category/level checkpoint and the
prepared test split.

## Optional OBJ export and visualization

The optional `<partnet-eval-entrypoint>` runs a test loader with batch size 1
and writes prediction and ground-truth `.obj` files containing point
coordinates and RGB class colors. It is optional and not a verification
prerequisite. Keep output in an explicitly chosen result directory and confirm
labels are within the color table before opening files.

The optional `<visualizer-entrypoint>` takes this command shape:

```text
<visualizer-entrypoint> --dir_path <result-root> \
  --category <integer> --obj_no <integer> \
  --folders <comma-separated-result-folders>
```

It expects `<dir_path>/<folder>/<Category>/<Category>_<obj>_pred.obj` and the
corresponding ground-truth OBJ. Visualization imports VTK, creates an
interactive window, and is deliberately outside the bundled smoke and core
workflow. Do not invoke it in a headless or untrusted environment; use a
non-interactive point/label inspection instead.

## Checkpoint compatibility checklist

Before evaluation, compare the checkpoint metadata or naming convention with:

- category id and resolved name (for example `1` / `Bed`);
- segmentation level (`L3` in the documented naming convention);
- `block`, `conv`, `n_blocks`, `n_filters`, `k`, dropout, and training batch
  convention;
- number of output parts and whether class 0 is background;
- dense input channel count (`3` for the default semantic path).

The documented checkpoint naming resembles
`PartnetSemanticSeg-Bed-L3-res-edge-n28-C64-k9-drop0.5-lr0.005_B6-val_best_model.pth`.
Treat names as hints only: inspect the actual state dict and class count where
possible. Do not fetch externally hosted checkpoint artifacts from this skill.
