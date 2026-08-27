# Model utilities

Use these source-backed helper contracts to validate inputs before changing a
network. They are useful for small CPU assertions but do not replace a model
forward or custom CUDA test.

## Geometry and anchors

- `compute_iou_2D` and `compute_iou_3D` compare one box against arrays of boxes;
  coordinate ordering must match the repository's inclusive extent convention.
- `generate_anchors` and `generate_anchors_3D` expand scales/ratios over feature
  maps. In 3D, XY scales and z scales are separate arguments.
- `apply_box_deltas_*`, `clip_boxes_*`, `bbox_overlaps_*`, and
  `box_refinement` assume the same coordinate ordering as the target builder.
  Validate one known box before processing a batch.
- `gt_anchor_matching` assigns positive/negative/neutral anchors from IoU and
  config thresholds; inspect counts when a batch has no positives.

## Segmentation and tensors

- `get_one_hot_encoding(y, n_classes)` converts class labels into a one-hot
  representation used by segmentation metrics.
- `batch_dice` and `batch_dice_mask` compare batch predictions and targets;
  `false_positive_weight` and `smooth` change the metric/loss behavior.
- `NDConvGenerator` selects 2D or 3D convolution/normalization behavior from
  config. Its dimensionality must agree with `cf.dim` and input tensor rank.
- `pad_nd_image` and `get_patch_crop_coords` are data-owned helpers; use the
  data route when a geometry issue originates before the model.

## Assertion strategy

Use tiny integer boxes and small arrays to assert shape, coordinate, and class
assumptions. Test a no-positive case explicitly because hard-example sampling
and loss code may have special handling. Keep raw arrays unchanged, record the
expected coordinate convention, and stop on a mismatch instead of compensating
with an unexplained transpose or offset.

For exact function signatures and revision-specific behavior, inspect the
installed source version selected for the checkout. Do not copy the source
module into a new skill or claim that a utility's modern dependency behavior
matches the historical pin.
