# vision-workflows

## Purpose

Read this when you need to inspect or explain AXLearn's image-classification recipes, ImageNet inputs, or CLIP-style vision helpers.

## Verified API facts

The installed package exposes these important signatures:

- `axlearn.vision.resnet.ResNet.resnet18_config()`
- `axlearn.vision.resnet.ResNet.resnet34_config()`
- `axlearn.vision.resnet.ResNet.resnet50_config()`
- `axlearn.vision.resnet.ResNet.resnet101_config()`
- `axlearn.vision.resnet.ResNet.resnet152_config()`
- `axlearn.vision.image_classification.ImageClassificationModel.default_config()`
- `axlearn.vision.input_image.ImagenetInput.default_config()`
- `axlearn.vision.input_image.fake_image_dataset(is_training, total_num_examples=None, input_key='image')`
- `axlearn.vision.input_image.crop_augment_whiten(image, *, is_training, image_size, eval_resize=None, augment_name=None, randaug_num_layers=2, randaug_magnitude=10, randaug_exclude_ops=None, erasing_probability=None, use_whitening=True)`
- `axlearn.experiments.vision.imagenet.common.input_config(split, global_batch_size, prefetch_buffer_size=None)`
- `axlearn.experiments.vision.resnet.common.model_config()`
- `axlearn.experiments.vision.resnet.common.learner_config(learning_rate, ema_decay=None)`
- `axlearn.experiments.vision.resnet.imagenet_trainer.named_trainer_configs()`

## Workflow patterns

### 1) ImageNet input setup

The ImageNet helper switches between fake and TFDS-backed inputs:

- `DATA_DIR=FAKE` -> synthetic image batches.
- Real `DATA_DIR` -> `tfds_read_config`-backed ImageNet inputs.

`input_config()` sets the processor and batcher defaults used by the ResNet trainer catalog.

### 2) ResNet trainer catalog

`imagenet_trainer.named_trainer_configs()` exports common names such as:

- `ResNet-Test`
- `ResNet-Testb`
- `ResNet-18`
- `ResNet-34`
- `ResNet-50`
- `ResNet-50-ema`
- `ResNet-101`
- `ResNet-152`

The `ResNet-Test` config is the smallest safe probe because it keeps the model tiny and uses fake inputs.

### 3) Image-classification model API

`ImageClassificationModel` wraps:

- A backbone that emits an `embedding` endpoint.
- A dropout layer.
- A classifier head.
- A classification metric.

This is the main reusable abstraction when you are documenting a new vision backbone or tuning the classifier head.

### 4) CLIP-style helpers

The `axlearn.vision.clip` module exposes builder functions for text and image encoders, plus transformer/vision configuration helpers. Use it when the task names CLIP, CoCa, or CyCLIP.

## Typical command patterns

### Fake-data ResNet probe

```bash
DATA_DIR=FAKE python -m axlearn.common.launch_trainer_main \
  --module=axlearn.experiments.vision.resnet.imagenet_trainer \
  --config=ResNet-Test \
  --trainer_dir=/tmp/axlearn-resnet-test \
  --data_dir=FAKE \
  --jax_backend=cpu
```

### Inspect the catalog names

```bash
python scripts/inspect_vision_configs.py --module axlearn.experiments.vision.resnet.imagenet_trainer
```

## When to read more

- For failure modes and dataset issues, see `references/troubleshooting.md`.
- For the shared trainer runtime, use `../training-core/`.
