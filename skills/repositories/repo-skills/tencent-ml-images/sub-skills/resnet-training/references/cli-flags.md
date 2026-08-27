# CLI Flags

Read this when translating a user request into a Tencent ML-Images command.
Flags are defined through TensorFlow 1.x `tf.app.flags` in the project.

## Cross-cutting flags

| Flag | Typical value | Meaning |
|---|---:|---|
| `--mode` | `train` | train or validation mode |
| `--max_to_keep` | `200` | maximum checkpoints to keep |
| `--visiable_gpu` | `0` | GPU id string used in TensorFlow session config; note the misspelling in the source flag |

## Data flags

| Flag | Typical value | Meaning |
|---|---:|---|
| `--data_dir` | `./data/ml-images` or `./data/imagenet` | Parent containing `train/` and `val/` TFRecord split directories |
| `--batch_size` | `512` pretraining, `64` finetuning per GPU in example | Batch size before multi-GPU multiplication in finetune.py |
| `--num_preprocess_threads` | `4` | Threads per tower; make it a multiple of 4 |
| `--file_shuffle_buffer` | `1500` | Filename shuffle buffer |
| `--shuffle_buffer` | `2048` | Sample shuffle buffer |
| `--with_bbox` | `False` in example | Whether to use bounding boxes in the training set |

## Model flags

| Flag | Typical value | Meaning |
|---|---:|---|
| `--class_num` | `11166` or `1000` | ML-Images classes for pretraining, ImageNet classes for finetuning/inference |
| `--resnet_size` | `101` | Supported: `50`, `101`, `152` |
| `--data_format` | `NCHW` | Explicitly pass `NCHW` for the source examples |
| `--image_size` | `224` | Input crop size |
| `--image_channels` | `3` | RGB image channels |
| `--batch_norm_decay` | `0.997` | Batch-norm momentum/decay |
| `--batch_norm_epsilon` | `1e-5` | Batch-norm epsilon |
| `--mask_thres` | `0.7` | Threshold for positive mask in multi-label loss |
| `--neg_select` | `0.1` or `0.3` | Negative class sampling fraction |

## Training flags

| Flag | Typical value | Meaning |
|---|---:|---|
| `--restore` | `True` or `False` | Restore compatible variables from checkpoint |
| `--num_gpus` | `1` or `4` | Number of GPUs/towers used by `finetune.py`; public `train.py` Estimator config has a separate visible GPU setting |
| `--optimizer` | `mom` | `mom` or `sgd` in finetuning code |
| `--opt_momentum` | `0.9` | Momentum value |
| `--lr` | `0.08` or `0.1` | Initial learning rate |
| `--lr_decay_step` | workflow-specific | Decay boundary scale |
| `--lr_decay_factor` | `0.1` | Decay factor |
| `--weight_decay` | `0.0001` | Weight decay flag defined in source |
| `--warmup` | `35200` | Warmup stop step for pretraining |
| `--lr_warmup` | `0.01` | Warmup initial LR |
| `--max_iter` | workflow-specific | Maximum training steps |
| `--prof_interval` | `100` or `500` | Print timing every N iterations |
| `--log_interval` | `100` or `5000` | Summary/log interval |
| `--snapshot` | `4400` or `5000` | Checkpoint save interval |
| `--epoch_iter` | `0` | Optional epoch iteration count |
| `--pretrain_ckpt` | checkpoint prefix/path | Source flag used for restore |
| `--FixBlock2` | `True`/`False` | Restrict trainable variables to later blocks/global/logits when true |

## Example-script caveats

- The public finetune shell example uses `--weight_decay_rate` and
  `--batch_norm_elipson`, but the source flags are `--weight_decay` and
  `--batch_norm_epsilon`. Prefer the source flag names unless you have verified
  a patched checkout.
- The public pretraining shell example includes `${NODE_NUM}` and `${GPU_NUM}`
  in paths/log names without defining them. Use the bundled command builder to
  make those values explicit.
- The source flag is spelled `visiable_gpu`, not `visible_gpu`.
