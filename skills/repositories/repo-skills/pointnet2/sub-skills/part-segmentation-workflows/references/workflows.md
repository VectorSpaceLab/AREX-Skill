# ShapeNetPart Part-Segmentation Workflows

This reference is self-contained for the PointNet++ repository's ShapeNetPart paths. Commands assume they are run from the repository root and that the source checkout still contains `part_seg/`, `models/`, `utils/`, and compiled TensorFlow custom ops. Use the bundled command builder when generating commands for a user.

## Workflow summary

| Workflow | Source entry point | Model | Dataset loader | Category conditioning | Best use |
|---|---|---|---|---|---|
| All-category plain training | `part_seg/train.py` | `pointnet2_part_seg` | `PartNormalDataset(..., split='trainval'/'test')` | No explicit class label; predictions are later restricted to the ground-truth category's part labels for metrics | Reproduce the repository's standard ShapeNetPart segmentation path |
| All-category one-hot training | `part_seg/train_one_hot.py` | `pointnet2_part_seg_msg_one_hot` | `PartNormalDataset(..., return_cls_label=True)` | Yes, per-shape category id is fed into the model and tiled per point | Use the MSG one-hot variant from `command_one_hot.sh` |
| Plain checkpoint evaluation | `part_seg/evaluate.py` | `pointnet2_part_seg` by default | `PartNormalDataset(..., split='test')` | No explicit one-hot input; 12-vote logits are accumulated | Evaluate a plain model checkpoint |
| Single-category visualization | `part_seg/test.py` | Intended for a category-specific legacy path | `PartDataset(..., class_choice=<category>, split='test')` | Category chosen by `--category`, not by a one-hot tensor | Reference for interactive visualization only; patch before running |

## All-category plain training and evaluation

The plain training script builds a TensorFlow 1.x graph whose placeholders are:

- point clouds: `B x N x 6`, with XYZ in columns 0:3 and normals in columns 3:6;
- labels: `B x N`, integer ShapeNetPart labels in the global 0..49 label space.

The source training defaults are `--num_point 2048`, `--batch_size 32`, `--max_epoch 201`, `--learning_rate 0.001`, `--optimizer adam`, `--decay_step 200000`, and `--decay_rate 0.7`. The original `part_seg/command.sh` ran:

```bash
cd part_seg
python train.py --model pointnet2_part_seg --log_dir log --gpu 1 --max_epoch 201 > log.txt 2>&1 &
```

For safer regeneration, run:

```bash
python sub-skills/part-segmentation-workflows/scripts/build_part_seg_command.py train --gpu 0 --log_dir log
```

or, from this sub-skill directory:

```bash
python scripts/build_part_seg_command.py train --gpu 0 --log_dir log
```

The training loop evaluates the test split at the end of every epoch and saves `model.ckpt` under `--log_dir` every 10 epochs. It computes mean loss, point accuracy, average class accuracy, per-category mIoU, mean mIoU across categories, and mean mIoU across shapes. During metric computation it restricts each shape's logits to the valid part-label list for the ground-truth category using `seg_classes` from the dataset loader.

Standalone evaluation uses `part_seg/evaluate.py` and defaults to a 12-vote accumulation (`VOTE_NUM = 12`) over the test split:

```bash
python scripts/build_part_seg_command.py evaluate --gpu 0 --model_path log/model.ckpt --log_dir log_eval
```

Use `--num_point` and `--batch_size` consistently with training. A mismatched checkpoint/model pair usually fails during TensorFlow restore, not during command parsing.

## One-hot category-conditioned training

The one-hot variant changes both the trainer and the model:

- trainer: `part_seg/train_one_hot.py`;
- model: `models/pointnet2_part_seg_msg_one_hot.py`;
- placeholders: `pointclouds_pl`, `labels_pl`, and `cls_labels_pl`;
- model call: `get_model(pointclouds, cls_labels, is_training, bn_decay=...)`;
- category count: `NUM_CATEGORIES = 16`.

The source `part_seg/command_one_hot.sh` ran:

```bash
cd part_seg
python train_one_hot.py --batch_size 8 --model pointnet2_part_seg_msg_one_hot --log_dir log_msg_one_hot --gpu 0 --max_epoch 201 > log_msg_one_hot.txt 2>&1 &
```

Generate that workflow with:

```bash
python scripts/build_part_seg_command.py train-one-hot --gpu 0 --log_dir log_msg_one_hot
```

One-hot training requires the normal all-category layout and `PartNormalDataset(..., return_cls_label=True)`. The class label is derived by the loader from `synsetoffset2category.txt` and its internal category dictionary. Do not create a custom category-id mapping unless every checkpoint, trainer, and inference path uses the same mapping.

Important guard: the repository does **not** provide a standalone one-hot evaluator equivalent to `evaluate.py`. The plain evaluator unpacks only two placeholders and calls `get_model(pointclouds, is_training)`, so it is incompatible with `pointnet2_part_seg_msg_one_hot.py` unless patched to feed `cls_labels_pl` and call the one-hot signature.

## Single-category test-time visualization

`part_seg/test.py` is best treated as a design note for point-level inference plus `show3d_balls` visualization, not as a verified command. It exposes:

- `--category`, default `Airplane`;
- `--num_point`, default 2048;
- `--model`, default `pointnet2_part_seg`;
- `--model_path`, default `log/model.ckpt`.

The intent is:

1. load a category-filtered `PartDataset(..., class_choice=<category>, split='test')`;
2. restore a checkpoint;
3. run logits over a `1 x N x 3` or compatible point cloud batch;
4. color ground truth and prediction labels using `show3d_balls.showpoints`.

Before using it, patch the known issues described in [troubleshooting.md](troubleshooting.md#root_dir-and-stale-testpy-visualization-path). In particular, define `ROOT_DIR`, fix `sys.path` to point at repository-level `models/` and `utils/`, align the dataset layout with the actual ShapeNetPart download, and use the model's 50-channel output plus the selected category's valid part-label range instead of assuming four output classes.

The command builder can still emit the source-style command as a reminder:

```bash
python scripts/build_part_seg_command.py test --category Airplane --model_path log/model.ckpt
```

When the user asks for a robust inference script, implement a patched wrapper rather than reusing the raw `test.py` unchanged.

## Model and tensor shape anchors

`pointnet2_part_seg.py`:

- input placeholder: `(batch_size, num_point, 6)`;
- label placeholder: `(batch_size, num_point)`;
- model output: `(batch_size, num_point, 50)` logits;
- architecture: SSG set abstraction at 512 and 128 points, global abstraction, feature propagation back to all points, `conv1d(128)`, dropout, `conv1d(50)`.

`pointnet2_part_seg_msg_one_hot.py`:

- input placeholder: `(batch_size, num_point, 6)`;
- label placeholder: `(batch_size, num_point)`;
- class label placeholder: `(batch_size,)`;
- one-hot category tensor: depth 16, tiled to `(batch_size, num_point, 16)` and concatenated with XYZ/normals before the final feature propagation layer;
- model output: `(batch_size, num_point, 50)` logits;
- architecture: MSG set abstraction at the first two levels, global abstraction, feature propagation, one-hot-conditioned final propagation, `conv1d(128)`, dropout, `conv1d(50)`.

Both models depend on PointNet++ custom TensorFlow ops through the shared pointnet utility modules. If the user only needs command or dataset checks, use the bundled scripts without importing TensorFlow.

## Operational cautions

- Run the original training/evaluation commands from `part_seg/`; the scripts copy `train.py` into the log directory using a relative shell command.
- The dataset path is hard-coded in the source scripts as `data/shapenetcore_partanno_segmentation_benchmark_v0_normal` relative to the repository root. A different location requires a source patch, symlink, or wrapper.
- Training and evaluation are checkpoint-heavy and expected to run under a legacy TensorFlow 1.x environment; PointNet++ model execution additionally needs compiled sampling/grouping/interpolation custom ops.
- Use [data-formats.md](data-formats.md) and [scripts/validate_shapenetpart_layout.py](../scripts/validate_shapenetpart_layout.py) before diagnosing model failures; many errors come from mismatched split JSON tokens or wrong dataset layout.
