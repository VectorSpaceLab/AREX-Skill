# Vision Task Contracts

This file distills the benchmark-specific task dictionaries, losses, metrics,
and head shapes used by the NYUv2 and Cityscapes workflows.

## NYUv2

### Tasks

- `segmentation`
- `depth`
- `normal`

### Task dictionary shape

- segmentation: `metrics=['mIoU', 'pixAcc']`, `SegMetric(num_classes=13)`,
  `SegLoss()`, weight `[1, 1]`
- depth: `metrics=['abs_err', 'rel_err']`, `DepthMetric()`, `DepthLoss()`,
  weight `[0, 0]`
- normal: `metrics=['mean', 'median', '<11.25', '<22.5', '<30']`,
  `NormalMetric()`, `NormalLoss()`, weight `[0, 0, 1, 1, 1]`

### Model wiring

- Encoder: `resnet_dilated('resnet50')`
- Decoder head: `DeepLabHead(2048, num_out_channels[task])`
- Output channels:
  - segmentation: `13`
  - depth: `1`
  - normal: `3`

### Prediction post-processing

The benchmark rescales decoder outputs back to `(288, 384)` before metric
computation.

## Cityscapes

### Tasks

- `segmentation`
- `depth`

### Task dictionary shape

- segmentation: `metrics=['mIoU', 'pixAcc']`, `SegMetric(num_classes=7)`,
  `SegLoss()`, weight `[1, 1]`
- depth: `metrics=['abs_err', 'rel_err']`, `DepthMetric()`, `DepthLoss()`,
  weight `[0, 0]`

### Model wiring

- Encoder: `resnet_dilated('resnet50')`
- Decoder head: `DeepLabHead(2048, num_out_channels[task])`
- Output channels:
  - segmentation: `7`
  - depth: `1`

### Prediction post-processing

The benchmark rescales decoder outputs back to `(128, 256)` before metric
computation.

## Shared notes

- Both benchmarks are single-input tasks, so `multi_input=False`.
- `process_preds(...)` exists to resize the per-task logits back to the target
  spatial size.
- `SegNet_MTAN_encoder` / `SegNet_MTAN_decoder` are the alternative NYUv2
  backbone and head pair.
- The NYUv2 augmentation path is optional and only affects the training data
  loader.
