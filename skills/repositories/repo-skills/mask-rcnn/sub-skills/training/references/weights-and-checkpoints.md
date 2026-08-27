# Weights and Checkpoints

## Weight sources

Mask_RCNN workflows commonly start from one of three sources:

- `coco`: pretrained COCO weights from the package's release artifact.
- `imagenet`: `MaskRCNN.get_imagenet_weights()` downloads a ResNet50 backbone weight file through Keras helpers.
- `last`: `MaskRCNN.find_last()` locates the latest checkpoint in `model_dir`.
- Path to a `.h5` file: load by name or fully, depending on whether classes match.

## Loading rules

`load_weights(filepath, by_name=False, exclude=None)` is the central method.

- `by_name=True` is safest for transfer learning.
- If `exclude` is given, the implementation switches to by-name loading automatically.
- For COCO-to-custom transfer with a different class count, exclude final class and mask heads:

```python
exclude = [
    "mrcnn_class_logits",
    "mrcnn_bbox_fc",
    "mrcnn_bbox",
    "mrcnn_mask",
]
model.load_weights(coco_weights, by_name=True, exclude=exclude)
```

## Checkpoint discovery

`find_last()` scans the experiment directory tree under `model_dir` for directories whose names begin with the config `NAME`, then chooses the latest `mask_rcnn*` checkpoint inside it.

Practical consequences:

- Keep `config.NAME` stable for a given project line if you want resumable checkpoints.
- Do not rename the experiment prefix halfway through and expect `find_last()` to locate old runs.
- Ensure the process has permission to create subdirectories inside `model_dir`.

## Log directory

`set_log_dir(model_path=None)` tracks epoch counters and checkpoint naming. Training scripts normally pass a parent `logs/` directory, not a specific timestamped run directory.

## Common misuse patterns

- Loading COCO heads without excluding incompatible layers when `NUM_CLASSES` changed.
- Calling `get_imagenet_weights()` in an offline or network-restricted environment without a cache policy.
- Resuming from `last` without any checkpoint files present.
- Pointing `model_dir` at a read-only location.

## Validation signals

A sane training setup usually prints:

- `Starting at epoch ...`
- `Checkpoint Path: ...`
- trainable layer names after `set_trainable()`
- TensorBoard/checkpoint callback creation

If any of those are missing, check the training route in `troubleshooting.md`.
