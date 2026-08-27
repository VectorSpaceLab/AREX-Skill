# Customization Workflows

This note turns the API contract into change recipes.

## 1) Config-first extension

Use this path when the detector family stays the same and only tuning changes.

1. Start from the closest config in `config/`.
2. Keep the family-specific detector import unchanged.
3. Edit only the knobs that belong to the desired scope:
   - `General`: logging, batch size, FP16, workers
   - `KvstoreParam`: GPU list and communication mode
   - `NormalizeParam`: `fixbn`, `localbn`, `syncbn`, `gn`, or `dummy`
   - `BackboneParam`: depth, branch controls, or family-specific backbone flags
   - `NeckParam`: pyramid channels, stage count, or fusion behavior
   - `RpnParam`: anchor geometry, proposal settings, focal-loss settings, or
     anchor-free thresholds
   - `BboxParam`: class count, class-agnostic regression, stage weights
   - `MaskParam`: mask resolution and channel width
   - `RoiParam` / `MaskRoiParam`: pooling stride and output size
   - `DatasetParam`: roidb split selection
   - `OptimizeParam`: LR schedule, warmup, batch size normalization
   - `TestParam`: NMS, score thresholds, output caps
   - `ModelParam`: pretrain, checkpoint filtering, `process_weight`
4. Re-check the family README for any non-default input or output layout.
5. Run symbolic shape inspection before the first training attempt.

## 2) Add or replace a detector component

Use this path when you need new architecture behavior but want to stay inside
SimpleDet’s component protocol.

### Backbone
- Subclass `Backbone`.
- Populate `self.symbol` or equivalent cached tensors in `__init__`.
- Implement `get_rpn_feature()` and `get_rcnn_feature()`.
- Return tensors with stable names and shapes.

### Neck
- Subclass `Neck`.
- Preserve the two feature hooks.
- Make sure the returned feature collection matches the downstream head’s
  expected dictionary keys or tuple layout.

### RpnHead / anchor-free head
- Subclass `RpnHead` or the family’s anchor-free equivalent.
- Preserve `get_output`, `get_loss`, and proposal helpers when the detector
  expects them.
- If anchors are cached, keep `get_anchor()` and `process_weight()` aligned with
  config-side anchor injection.

### RoI extractor
- Subclass `RoiExtractor`.
- Keep `get_roi_feature()` and `get_roi_feature_test()` synchronized.
- For FPN families, make the ROI assignment strategy explicit.

### Bbox / mask heads
- Subclass the relevant base head.
- Keep `num_class`, `class_agnostic`, and regression target dimensions aligned.
- If you change output heads, update checkpoint compatibility and metrics.

### Detector
- Implement `get_train_symbol()` first.
- Add the matching test symbol path.
- Return outputs in the order expected by the test script.
- Use the smallest possible public API; keep helper methods private unless the
  config calls them directly.

## 3) Class count changes

Changing class count is the most common source of silent shape breakage.

Update together:

- `BboxParam.num_class`
- `RpnParam.bbox_target.num_reg_class` when anchor-based
- mask head output channels when class-specific masks are used
- metrics that read class-dependent outputs
- test post-processing that strips background channels

Rules of thumb:

- `class_agnostic=False` usually means per-class bbox deltas.
- `class_agnostic=True` reduces regression to a foreground/background style
  width, but some families still encode `num_reg_class = 2`.
- Any class-count change should trigger an output-name and shape review.

## 4) Anchor and proposal changes

If you alter anchors, touch both config and graph-side caching.

### Update in config
- `RpnParam.anchor_generate.scale`
- `RpnParam.anchor_generate.ratio`
- `RpnParam.anchor_generate.stride`
- `RpnParam.anchor_generate.max_side`
- `RpnParam.proposal.pre_nms_top_n`
- `RpnParam.proposal.post_nms_top_n`
- `RpnParam.proposal.nms_thr`

### Update in code or graph wiring
- `process_weight()` that injects cached anchors
- `get_anchor()` in the head if the family uses symbolic anchors
- any proposal decode helper that assumes a fixed anchor count

## 5) ROI topology changes

If you alter ROI pooling behavior:

- keep `RoiParam.stride` aligned with the feature pyramid
- keep `roi_canonical_scale` and `roi_canonical_level` consistent with the
  family README or Detectron-style baseline
- update FPN level assignment helpers if the level mapping changes
- re-check any family-specific output order that uses pooled RoI features twice,
  such as mask or TSD branches

## 6) Mask topology changes

Mask families are more sensitive to schema drift than bbox-only detectors.

- Add or preserve `gt_poly` in the training graph.
- Keep the polygon encoder compatible with dataset preprocessing.
- Update `MaskParam.resolution` and `MaskRoiParam.out_size` together.
- Keep mask branch foreground slicing in sync with the sampled proposal count.
- Re-check `mask_test.py` output order and the post-processor.

## 7) Checkpoint compatibility

A checkpoint can usually be reused only when the symbol contract is stable.

### Safe reuse conditions
- same family
- same class count
- same anchor / ROI / mask topology
- same head width and stage count
- same parameter names

### When to reinitialize or filter
- changed head depth or output width
- changed branch count
- changed `class_agnostic` setting
- changed mask resolution or ROI count
- introduced new custom operators or new branch-specific weights

### Tools already used by the repo
- `ModelParam.pretrain.prefix` / `epoch`
- `fixed_param`
- `excluded_param`
- `process_weight(sym, arg, aux)`
- `from_scratch`

Cascade and DoublePred-style families often need extra attention because stage-
specific weights are part of the public contract.

## 8) Safe symbol inspection

Use shape inspection before training or checkpoint loading.

Recommended checks:
- `sym.list_arguments()`
- `sym.list_outputs()`
- `sym.infer_shape(**worker_data_shape)`
- `sym.get_internals().infer_shape(**worker_data_shape)`
- `sym.save(...)` after the graph is built

Good practice:
- derive `worker_data_shape` from loader `provide_data` and `provide_label`
- prefix shapes with the per-GPU `batch_image`
- inspect both intermediate outputs and terminal outputs
- compare shapes before and after memonger or BN fusion

## 9) Decision shortcut

- If the family only needs tuning, edit config only.
- If the family changes topology but not the detector protocol, subclass the
  relevant component.
- If the family changes input labels or output order, update the detector,
  metrics, and test post-processing together.
