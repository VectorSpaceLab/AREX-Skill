# Model configuration

Read this reference when editing an experiment config or diagnosing a shape,
class, memory, or model-import failure. Configuration values are organized in
`DefaultConfigs` and the experiment-specific `configs` subclasses.

## Freeze these values together

1. **Geometry:** `dim`, `patch_size`, `pre_crop_size`, `backbone_strides`,
   `pyramid_levels`, and `operate_stride1`.
2. **Channels/classes:** `channels`, `n_channels`, `head_classes`,
   `num_seg_classes`, `class_specific_seg_flag`, and the loader's label mode.
3. **Anchors/proposals:** `rpn_anchor_scales`, `rpn_anchor_ratios`,
   `rpn_anchor_stride`, `anchor_matching_iou`, `rpn_nms_threshold`,
   `pre_nms_limit`, and post-NMS counts.
4. **ROI/mask:** `pool_size`, `mask_pool_size`, `mask_shape`,
   `roi_positive_ratio`, `train_rois_per_image`, and `frcnn_mode`.
5. **Final filtering:** `model_min_confidence`, `model_max_instances_per_batch_element`,
   `detection_nms_threshold`, and evaluation `min_det_thresh`.

Changing only one value in a group commonly produces mismatched feature-map,
anchor, target, or output shapes. Recompute the expected `backbone_shapes` from
the patch and strides, then validate a tiny source-level construction before any
training.

## Family-specific decisions

- **Detection U-Net:** choose weighted cross-entropy, Dice, or both through
  `seg_loss_mode`; choose connected-component aggregation (`max` or `median`)
  and a bounded candidate count. Ensure `head_classes` agrees with
  `num_seg_classes`.
- **MRCNN/U-FRCNN:** choose whether mask loss is active (`frcnn_mode`), whether
  validation/test masks are returned, and whether proposal counts fit memory.
  U-FRCNN enables a high-resolution segmentation path and class-specific
  segmentation in the supplied defaults.
- **RetinaNet/Retina U-Net:** anchor scales expand to three values per pyramid
  level in the supplied configs, the anchor matching IoU changes, and pre-NMS
  counts can be much larger. Keep batch size and patch size conservative.

## Config lifecycle checks

A valid experiment config exposes `configs(server_env=None)`, sets `model` and
`dim`, calls the base config initializer, and then sets paths, data, schedule,
augmentation, and model values. Confirm `model_path`, `backbone_path`,
`input_df_name`, `fold`/CV settings, and class dictionaries before importing.
Route data shape/label decisions to [data-and-preprocessing](../../data-and-preprocessing/SKILL.md)
and detector import failures to [cuda-extensions](../../cuda-extensions/SKILL.md).
