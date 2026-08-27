# Troubleshooting API and architecture changes

Use this guide when source inspection succeeds but a model/backbone/RPN change is confusing. Installation, TensorFlow, CUDA, checkpoint, and CLI execution failures should be routed to the appropriate sibling sub-skill.

## `create_architecture` fails immediately

Check these source-level requirements first:

- `tag` must be non-`None`; the method asserts this before graph construction proceeds.
- `mode` should be the repo convention `'TRAIN'` or `'TEST'`.
- `num_classes` must match the dataset/checkpoint class count because RCNN classification has `num_classes` outputs and bbox regression has `num_classes * 4` outputs.
- `cfg.POOLING_MODE` must be `'crop'` for the implemented path in `_build_network`; other values hit `NotImplementedError`.

## Anchor changes cause shape mismatches

Likely cause: anchor scales/ratios changed in one place but `A = len(scales) * len(ratios)`-dependent tensors were not considered.

Inspect:

- `create_architecture(..., anchor_scales=..., anchor_ratios=...)`.
- `_anchor_component` and `generate_anchors_pre` defaults.
- RPN class logits: `self._num_anchors * 2` channels.
- RPN bbox deltas: `self._num_anchors * 4` channels.
- `anchor_target_layer` reshapes for labels and bbox weights.
- `proposal_layer` score slicing at `num_anchors:`.

Run the bundled inspector and compare its reported `create_architecture` defaults and layer utility signatures.

## New backbone does not restore variables

Backbone restore logic is source-specific:

- VGG16 skips `fc6`, `fc7`, and first conv weights, then reshapes FC conv weights and reverses RGB/BGR.
- ResNet skips first conv weights and reverses RGB/BGR.
- MobileNet skips first conv weights, reverses RGB/BGR, and scales by `(255.0 / 2.0)`.

For a new backbone, do not assume a checkpoint will restore just because scopes look similar. Implement `get_variables_to_restore` and `fix_variables` around exact variable names, shapes, and preprocessing conventions.

## `gpu_nms` or compiled NMS import fails

The repo defaults to `cfg.USE_GPU_NMS = True`, and full native extension setup was not verified in production. This is not an architecture bug by itself.

- For build/setup diagnosis, route to `installation-and-configuration`.
- For source-level proposal reasoning, inspect `proposal_layer` and `model.nms_wrapper.nms` without claiming full runtime execution.
- For CPU-only debugging, ensure future runtime config intentionally disables GPU NMS before running graph/session code.

## Roidb/minibatch code errors on missing keys

`get_minibatch` and `RoIDataLayer` expect dataset loader output to be enriched by `prepare_roidb` and compatible with single-image training.

Check each roidb entry for:

- `image`, `flipped`, `boxes`, `gt_classes`, and sparse `gt_overlaps` with `.toarray()`.
- `width` and `height` when `cfg.TRAIN.ASPECT_GROUPING` is enabled.
- non-empty foreground/background candidates for `proposal_target_layer`; otherwise source can fall into `pdb.set_trace()`.

Dataset path/layout troubleshooting belongs to `dataset-and-assets`.

## Bbox outputs look transposed or clipped incorrectly

Review coordinate conventions:

- Boxes are `(x1, y1, x2, y2)` with inclusive width/height calculations.
- `im_shape` and `im_info` use `[height, width]` ordering for clipping bounds.
- Multi-class bbox deltas are interleaved by class: `0::4`, `1::4`, `2::4`, `3::4`.
- `im_detect` divides ROIs by the single image scale before bbox regression.

## Image colors or summaries look wrong

The repo's OpenCV image path assumes BGR input. Summary visualization reverses/rescales for display, while pretrained variable fixes often reverse first-layer RGB/BGR channels.

If adapting a backbone or preprocessing pipeline, keep image color order, pixel means, and first-layer checkpoint conversion in sync.

## TensorFlow/contrib/slim errors

The source depends on TensorFlow 1.x APIs such as `tensorflow.contrib.slim`, `tf.py_func`, and legacy graph/session patterns. The production inspection used TensorFlow 1.15 CPU only for limited source/import checks and did not prove full graph execution.

Route environment construction and compatibility diagnosis to `installation-and-configuration` before attempting demo, train, or test runs.

## Inspector reports signature drift

If `scripts/inspect_source_api.py --strict` reports drift:

1. Read the reported file and compare against [API reference](api-reference.md).
2. Update architecture guidance only if the source change is intentional and verified.
3. Treat changed constructor or `create_architecture` signatures as high-impact because CLI selectors, checkpoint restore, and downstream sub-skills may depend on them.
