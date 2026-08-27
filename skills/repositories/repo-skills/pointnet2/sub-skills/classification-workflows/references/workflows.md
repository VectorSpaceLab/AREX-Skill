# ModelNet40 classification workflows

This reference distills the repository's classification scripts into safe, repeatable operating steps. It covers the CLI surfaces of `train.py`, `train_multi_gpu.py`, and `evaluate.py` without requiring a future agent to reopen those source files.

## Workflow map

| User intent | Use | Primary command script | Key constraints |
|---|---|---|---|
| Train default ModelNet40 classifier | Single-device training | `train.py` | HDF5 data by default, `--num_point <= 2048`, default model `pointnet2_cls_ssg` |
| Train with several GPUs | Multi-GPU synchronous towers | `train_multi_gpu.py` | `--batch_size` must divide evenly by `--num_gpus`; use `CUDA_VISIBLE_DEVICES` |
| Evaluate a checkpoint | Checkpoint restore + optional voting | `evaluate.py` | `--model` must match checkpoint architecture; `--model_path` is a TensorFlow checkpoint prefix |
| CPU baseline or custom-op-free smoke | PointNet v1 classifier | same scripts with `--model pointnet_cls_basic` | No PointNet++ custom operators, but still TensorFlow 1.x code |

Build commands with the bundled helper from the generated skill tree:

```bash
python sub-skills/classification-workflows/scripts/build_classification_command.py --action train --dataset-mode h5 --model pointnet2_cls_ssg --num-point 1024 --log-dir log_cls_ssg
python sub-skills/classification-workflows/scripts/build_classification_command.py --action train-multi-gpu --dataset-mode h5 --model pointnet2_cls_msg --num-gpus 2 --cuda-visible-devices 0,1 --batch-size 32 --log-dir log_cls_msg_2gpu
python sub-skills/classification-workflows/scripts/build_classification_command.py --action evaluate --dataset-mode h5 --model pointnet2_cls_ssg --model-path log_cls_ssg/model.ckpt --dump-dir dump_cls_ssg --num-votes 12
```

The helper prints the legacy command to run from a compatible PointNet2 checkout and validates high-risk flag combinations before training or evaluation starts.

## Model selection

| Model flag | Evidence-backed behavior | Best fit | Avoid when |
|---|---|---|---|
| `pointnet2_cls_ssg` | PointNet++ single-scale grouping classifier; `placeholder_inputs(batch_size, num_point)` creates `BxNx3` points and `B` labels; output logits are `Bx40`. | Default ModelNet40 PointNet++ classifier. | Shared TensorFlow custom ops are missing or the user asked for CPU-only baseline work. |
| `pointnet2_cls_msg` | PointNet++ multi-scale grouping classifier; uses multi-scale set abstraction in the first two layers; output logits are `Bx40`. | Comparing MSG against the default SSG architecture. | Same custom-op/backend limitations as SSG. |
| `pointnet_cls_basic` | PointNet v1 baseline; builds `BxNx3 -> Bx40` with shared MLP + max pooling and no PointNet++ set-abstraction custom ops. A tiny CPU graph smoke was verified with output shape `[2, 40]`. | CPU baseline, smoke tests, or fallback when PointNet++ custom ops cannot load. | User specifically needs PointNet++ hierarchical set abstraction or paper-equivalent PointNet++ results. |

PointNet++ classification models depend on the shared custom-op backend used by PointNet++ set abstraction. If a user only needs a command template or CPU data validation, stay in this sub-skill. If they need to compile or diagnose custom ops, route to `model-apis-and-custom-ops`.

## Dataset mode selection

| Dataset mode | Flag pattern | Loader behavior | Point limit | Notes |
|---|---|---|---|---|
| HDF5 ModelNet40 | omit `--normal` | `ModelNetH5Dataset(data/modelnet40_ply_hdf5_2048/{train,test}_files.txt, ...)`; HDF5 `data` arrays are sliced to the first `--num_point` XYZ points. | `--num_point <= 2048` | Default and safest path for stock models. |
| Normal-resampled ModelNet40 | add `--normal` | `ModelNetDataset(root=data/modelnet40_normal_resampled, normal_channel=True, ...)`; text files contain XYZ+normal and the loader returns 6 channels. | `--num_point <= 10000` | The README describes XYZ+normal experiments at 5000 points, but the stock classification model files observed here declare `BxNx3` placeholders; use only with a model adapted for six channels. |

Always validate layout first:

```bash
python sub-skills/classification-workflows/scripts/validate_modelnet_layout.py --mode h5 --repo-root . --num-point 1024
python sub-skills/classification-workflows/scripts/validate_modelnet_layout.py --mode normal --repo-root . --num-point 5000
```

For a tiny loader-only smoke independent of TensorFlow:

```bash
python sub-skills/classification-workflows/scripts/smoke_modelnet_loader.py --mode h5 --repo-root . --split test --num-point 16 --batch-size 2
python sub-skills/classification-workflows/scripts/smoke_modelnet_loader.py --mode normal --repo-root . --split train --num-point 16 --batch-size 2 --normal-channel
```

## Single-device training

Source defaults from `train.py`:

- `--gpu 0`
- `--model pointnet2_cls_ssg`
- `--log_dir log`
- `--num_point 1024`
- `--max_epoch 251`
- `--batch_size 16`
- `--learning_rate 0.001`
- `--momentum 0.9`
- `--optimizer adam` (`adam` or `momentum`)
- `--decay_step 200000`
- `--decay_rate 0.7`
- `--normal` disabled by default

Example generated command for the default HDF5 SSG run:

```bash
python train.py --gpu 0 --model pointnet2_cls_ssg --log_dir log_cls_ssg --num_point 1024 --max_epoch 251 --batch_size 16 --learning_rate 0.001 --momentum 0.9 --optimizer adam --decay_step 200000 --decay_rate 0.7
```

Operational notes:

1. The script imports the selected model module from `models/` by module name, not by filename path.
2. It copies the selected model file and `train.py` into `--log_dir` as run provenance.
3. It writes TensorBoard summaries below `--log_dir/train` and `--log_dir/test`.
4. It saves a checkpoint every 10 epochs as `--log_dir/model.ckpt`.
5. The TensorFlow session sets `allow_soft_placement=True`; for CPU-only smoke work prefer `pointnet_cls_basic`, very small `--num_point`, and tiny fixture data.

## Multi-GPU training

Source defaults from `train_multi_gpu.py` mostly match single-device training, except:

- `--num_gpus 1`
- `--batch_size 32`
- no `--gpu` flag; towers are placed on `/gpu:0`, `/gpu:1`, ... up to `--num_gpus - 1`
- `assert(BATCH_SIZE % NUM_GPUS == 0)` must pass before the graph is built

Example generated command:

```bash
CUDA_VISIBLE_DEVICES=0,1 python train_multi_gpu.py --num_gpus 2 --model pointnet2_cls_msg --log_dir log_cls_msg_2gpu --num_point 1024 --max_epoch 251 --batch_size 32 --learning_rate 0.001 --momentum 0.9 --optimizer adam --decay_step 200000 --decay_rate 0.7
```

Use a global batch size that divides evenly by the requested GPU count. If the user gives physical device ids, place them in `CUDA_VISIBLE_DEVICES`; the script will still refer to visible devices as `/gpu:0`, `/gpu:1`, etc.

## Checkpoint evaluation and voting

Source defaults from `evaluate.py`:

- `--gpu 0`
- `--model pointnet2_cls_ssg`
- `--batch_size 16`
- `--num_point 1024`
- `--model_path log/model.ckpt`
- `--dump_dir dump`
- `--normal` disabled by default
- `--num_votes 1`

Example generated command:

```bash
python evaluate.py --gpu 0 --model pointnet2_cls_ssg --batch_size 16 --num_point 1024 --model_path log_cls_ssg/model.ckpt --dump_dir dump_cls_ssg --num_votes 12
```

Evaluation restores variables with `tf.train.Saver().restore(sess, MODEL_PATH)`, so `--model_path` should be the checkpoint prefix that matches the chosen model architecture. Do not pass only a directory. Do not point a `pointnet2_cls_msg` evaluation command at an SSG checkpoint or a `pointnet_cls_basic` checkpoint.

`--num_votes` controls repeated rotations and point-order shuffles. Higher values can improve robustness but cost roughly linearly because every batch is evaluated once per vote. Use `--num_votes 1` for smoke checks and larger values such as `12` only for a full evaluation.

Evaluation writes `log_evaluate.txt` in `--dump_dir` and prints overall accuracy, average class accuracy, and per-class accuracies based on `data/modelnet40_ply_hdf5_2048/shape_names.txt`.

## Recommended command-building patterns

### Safe HDF5 SSG training

```bash
python sub-skills/classification-workflows/scripts/build_classification_command.py \
  --action train \
  --dataset-mode h5 \
  --model pointnet2_cls_ssg \
  --num-point 1024 \
  --batch-size 16 \
  --log-dir log_cls_ssg
```

### MSG comparison run

```bash
python sub-skills/classification-workflows/scripts/build_classification_command.py \
  --action train \
  --dataset-mode h5 \
  --model pointnet2_cls_msg \
  --num-point 1024 \
  --log-dir log_cls_msg
```

### CPU baseline command surface

```bash
python sub-skills/classification-workflows/scripts/build_classification_command.py \
  --action train \
  --dataset-mode h5 \
  --model pointnet_cls_basic \
  --num-point 16 \
  --batch-size 2 \
  --max-epoch 1 \
  --log-dir log_basic_smoke
```

### Evaluation with one vote for smoke

```bash
python sub-skills/classification-workflows/scripts/build_classification_command.py \
  --action evaluate \
  --dataset-mode h5 \
  --model pointnet_cls_basic \
  --model-path log_basic_smoke/model.ckpt \
  --dump-dir dump_basic_smoke \
  --num-point 16 \
  --batch-size 2 \
  --num-votes 1
```

## When to stop and reroute

- If the failure is a missing `tf_sampling_so.so`, `tf_grouping_so.so`, or interpolation custom op for PointNet++ models, route to `model-apis-and-custom-ops`.
- If the task mentions ShapeNetPart, part labels, category one-hot conditioning, or `part_seg/`, route to `part-segmentation-workflows`.
- If the task mentions ScanNet, semantic scene parsing, scene pickles, virtual scans, or whole-scene evaluation, route to `scannet-semantic-scene-workflows`.
