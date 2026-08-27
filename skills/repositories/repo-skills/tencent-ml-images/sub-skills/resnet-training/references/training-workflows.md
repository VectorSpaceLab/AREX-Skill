# Training Workflows

These workflows are for constructing commands and checking prerequisites. They
do not make full ML-Images pretraining or ImageNet finetuning cheap: those runs
need large datasets, checkpoint storage, and practical GPU resources.

## ML-Images multi-label pretraining

Inputs:

- TFRecords arranged as `<data-root>/train/*.tfrecords` and optionally
  `<data-root>/val/*.tfrecords`.
- Multi-label dense `float32[class_num]` label bytes, usually `class_num=11166`.
- TensorFlow 1.x runtime with `tf.app`, `tf.estimator`, `tf.layers`, and
  `tf.contrib` support.

Use the bundled command builder instead of copying shell variables:

```bash
python scripts/build_train_command.py \
  --python python2.7 \
  --data-dir ./data/ml-images \
  --model-dir ./out/checkpoint/ml-images/resnet_model_1node_1gpu \
  --tmp-model-dir ./out/tmp/ml-images/resnet_model_1node_1gpu \
  --log-dir ./out/log \
  --class-num 11166 \
  --batch-size 1 \
  --max-iter 440000 \
  --data-format NCHW
```

Then inspect the printed command, verify paths, and only run it in a prepared
TensorFlow 1.x checkout after the user accepts the training budget.

Key source settings from the public example:

- ResNet-101 (`--resnet_size 101`)
- image size 224
- `mask_thres=0.7`, `neg_select=0.1`
- `lr=0.08`, decay step `110000`, warmup `35200`
- snapshot interval `4400`
- log interval `100`

## ImageNet finetuning

Inputs:

- ImageNet-style scalar-label TFRecords under `<data-root>/train`.
- `class_num=1000`.
- A compatible ML-Images pretrained checkpoint.
- GPU runtime for practical runs; CPU can only be a structural smoke.

Build a command:

```bash
python scripts/build_finetune_command.py \
  --python python2.7 \
  --data-dir ./data/imagenet \
  --model-dir ./out/checkpoint \
  --log-dir ./out/log \
  --pretrain-ckpt ./out/checkpoint/model.ckpt \
  --num-gpus 4 \
  --batch-size 64 \
  --max-iter 600000
```

The builder emits source flag names and warns about misspellings found in the
public shell example.

## Checkpoint restore behavior

Finetuning restore logic reads a checkpoint and assigns matching variables by
name while skipping keys containing `global_step`, `Momentum`, or `logits`.
This supports restoring a backbone while training a new classification head. If
restore logs show many missing backbone variables, verify that the checkpoint
belongs to the same ResNet depth and TensorFlow variable naming convention.

## Validation before launch

Before running a generated training command:

1. Use the data-preparation sub-skill to validate TFRecord schemas and class
   count.
2. Run `scripts/resnet_graph_smoke.py --repo-root <checkout> --resnet-size 101`
   in the intended TensorFlow 1.x runtime.
3. Confirm `--data_format` is explicit and compatible with CPU/GPU hardware.
4. Confirm log/model/tmp directories are writable and do not overwrite needed
   results.
5. Confirm the training duration, GPU count, dataset size, and checkpoint
   storage budget with the user.

## Distributed training boundary

The public README says the released code is single-node/single-GPU oriented and
that the authors' full ML-Images training used an internal distributed training
framework that was not released. Do not invent distributed-launch instructions
for this repository. If a user asks for distributed training, treat it as an
adaptation task and state which parts are source-backed versus new engineering.
