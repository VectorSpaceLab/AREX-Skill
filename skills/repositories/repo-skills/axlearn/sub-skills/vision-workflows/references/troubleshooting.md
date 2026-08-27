# vision-workflows troubleshooting

## Purpose

Read this when an image-classification or vision helper fails to import, resolve fake inputs, or produce the expected trainer config.

## Common failures

### Fake-data smoke check still tries to fetch a dataset

**Likely cause:** `DATA_DIR` was not set to `FAKE`, or the selected config does not use the fake-input branch.

**Recovery:** Set `DATA_DIR=FAKE` and use `ResNet-Test` for the smallest CPU-safe probe.

### `ImageClassificationModel` fails because the backbone or class count is missing

**Likely cause:** The model config requires both `backbone` and `num_classes` before instantiation.

**Recovery:** Use `ResNet.resnet18_config()` or another backbone builder and set `num_classes` explicitly.

### Input-shape mismatch during preprocessing

**Likely cause:** The image size or batch shape does not match the expected ImageNet format.

**Recovery:** Check the `ImagenetInput` defaults and the `input_config()` helper before changing the processor or batcher.

### CLIP helper import or builder lookup issues

**Likely cause:** The task is really about another vision-language helper or the wrong builder name was used.

**Recovery:** Inspect the public builder names in `axlearn.vision.clip` and route back to this sub-skill only if the task is image-centric.

## Recovery order

1. Confirm whether the workflow is fake-data or real TFDS/ImageNet.
2. Confirm the trainer config name.
3. Confirm the backbone and `num_classes` settings.
4. Only then debug preprocessing or augmentations.
