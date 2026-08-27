# Architecture API

This note is the source-independent contract summary for SimpleDet detector customization.
It is derived from `doc/FRAMEWOKR_OVERVIEW.md`, `doc/fully_annotated_config.py`,
`symbol/detector.py`, `symbol/component.py`, `core/detection_metric.py`, and the
family builders under `models/`.

## Detector contract

SimpleDet organizes detector graphs around top-level detector singletons.
Each detector is responsible for assembling a symbolic graph from component
objects and returning a terminal `mxnet.Symbol`.

### Core detector entry points

- `get_train_symbol(...)`
  - Builds the training graph.
  - Creates symbolic labels such as `gt_bbox`, `gt_poly`, and `im_info` when needed.
  - Returns a grouped symbol of the losses and any extra training outputs.
- `get_test_symbol(...)`
  - Builds the evaluation graph used by `detection_test.py` or `mask_test.py`.
  - Returns grouped outputs in a layout expected by the family-specific test script.
- `get_rpn_test_symbol(...)`
  - Present on Faster-RCNN-style detectors that support RPN-only evaluation.
- Family-specific test variants may exist, such as `get_mask_test_symbol`-like
  behavior encoded through `MaskFasterRcnn.get_test_symbol(...)`.

### Config ownership

The config owns the detector symbols, not the training script.
Typical config fields are:

- `ModelParam.train_symbol`
- `ModelParam.test_symbol`
- sometimes `ModelParam.rpn_test_symbol`

The training and testing scripts read these fields directly from `get_config()`.

## Component responsibilities

### Backbone

A `Backbone` must provide:

- `get_rpn_feature()`
- `get_rcnn_feature()`

In many families both methods return the same tensor or FPN feature map.
In C4/C5 or multi-branch families, they may return different features.

### Neck

A `Neck` post-processes backbone features and exposes the same two feature hooks:

- `get_rpn_feature(rpn_feat)`
- `get_rcnn_feature(rcnn_feat)`

Common jobs:

- feature pyramid construction
- channel reduction
- top-down fusion
- branch fusion or pyramid refinement

### RpnHead / anchor-free head

A head that plays the proposal role must usually support:

- `get_anchor()` when anchors are cached in the graph
- `get_output(...)` for raw logits / deltas
- `get_loss(...)` for training targets and losses
- `get_all_proposal(...)` for inference proposals
- `get_sampled_proposal(...)` for RCNN training targets

Anchor-free heads such as FCOS keep the same conceptual role but skip anchor
creation and proposal sampling semantics that depend on RPN anchors.

### RoiExtractor

A `RoiExtractor` must support:

- `get_roi_feature(rcnn_feat, proposal)`
- `get_roi_feature_test(rcnn_feat, proposal)`

FPN ROI extractors often assign proposals to levels before pooling.

### BboxHead

A bbox head typically supports:

- `_get_bbox_head_logit(...)` in the concrete subclass
- `get_output(...)`
- `get_prediction(...)`
- `get_loss(...)`

`get_output()` usually returns `(cls_logit, bbox_delta)`.
`get_prediction()` usually returns `(cls_score, bbox_xyxy)`.

### MaskHead

Mask heads are family-specific but generally follow the same pattern:

- `get_output(...)`
- `get_prediction(...)`
- `get_loss(...)`

Mask heads usually consume foreground RoIs only and emit class-specific masks.

### Post-processors and metrics

- Post-processors convert symbol outputs into final detections.
- Metrics read terminal output names and label names, not Python objects.
- If output names change, metric wiring must change too.

## Common symbol inputs

| Name | Meaning | Typical families |
| --- | --- | --- |
| `data` | input image tensor | all |
| `im_info` | padded image size and scale | most detectors |
| `im_id` | image id used in test outputs | most test graphs |
| `rec_id` | record id used by loaders | most test graphs |
| `gt_bbox` | ground-truth boxes, usually padded | Faster, Mask, Cascade, Retina training, FreeAnchor, KD, TSD, CrowdHuman |
| `gt_poly` | encoded instance polygons | Mask and mask variants |
| `rpn_cls_label` | anchor or proposal class labels | Faster/FPN/Mask/Cascade/KD and some variants |
| `rpn_reg_target` | bbox regression target | anchor-based detectors |
| `rpn_reg_weight` | bbox regression weights | anchor-based detectors |
| `teacher_label` | teacher or mimic target | KD |
| family-specific auxiliary labels | centerness, point targets, mask targets, ignore masks | FCOS, RepPoints, CrowdHuman, TSD, mask variants |

## Common output layouts

| Layout | Meaning |
| --- | --- |
| `[rec_id, im_id, im_info, proposal, proposal_score]` | RPN-only test output |
| `[rec_id, im_id, im_info, cls_score, bbox_xyxy]` | standard detection test output |
| `[rec_id, im_id, im_info, post_cls_score, post_bbox_xyxy, post_cls, mask, mask_score]` | Mask-RCNN-style end-to-end mask output |
| family-specific tuple outputs | Trident, CrowdHuman, FCOS, RepPoints, TSD, and others may extend the tuple |

## Static shape constraints

SimpleDet uses MXNet symbolic graphs, so shape contracts matter.

- Data loader outputs are padded to fixed shapes.
- `PadParam.short`, `PadParam.long`, `PadParam.max_num_gt`, and related fields
  bound the static graph.
- Pyramid families rely on fixed stride lists and canonical assignment settings.
- `RpnParam.anchor_generate.max_side` must be large enough for cached anchors.
- `RoiParam.stride`, `roi_canonical_scale`, and `roi_canonical_level` must match
  the feature hierarchy.
- Multi-branch detectors often multiply batch sizes by branch count.
- Mask graphs add fixed polygon and mask-resolution dimensions.

Practical rule: if a config change alters class count, branch count, anchor
layout, ROI grid, or mask size, re-run symbolic shape inspection before trying
checkpoints or metrics.

## Custom metric contract

`core/detection_metric.py` provides metric helpers that expect the module output
layout to match `output_names` and `label_names`.

Common patterns:

- `AccWithIgnore` and `L1` skip labels marked with `ignore_label`.
- `FgAccWithIgnore` and `FgCeWithIgnore` skip background and ignore labels.
- `SigmoidCELossMetric` in Mask R-CNN reads the first output and averages it.
- Metrics do not inspect graph structure; they only see ordered outputs.

When adding a new output tensor, update the metric wiring together with the
symbol.

## Custom operator contract

Many family-specific behaviors are implemented with custom operators.

- Operators are registered with `@mx.operator.register(...)`.
- They are invoked via `mx.sym.Custom(..., op_type='...')`.
- `list_arguments()`, `list_outputs()`, and `infer_shape()` must agree with the
  symbol call site.
- `create_operator()` constructs the runtime op.
- `declare_backward_dependency()` should stay minimal for inference-only ops.

Observed examples include:

- proposal and proposal top-k helpers
- FPN level assignment
- RetinaNet decode helpers
- bbox and double-bbox target operators
- mask post-processing and CrowdHuman entropy helpers
- FCOS proposal helpers and focal/bce losses

Import order matters: the module that defines the operator must be imported
before the symbol is constructed, or registration will be missing.

## Architectural caution flags

- Do not assume every family uses the same labels or output order.
- Do not assume all families use anchors.
- Do not assume `class_agnostic` is safe to flip without revisiting target and
  decode shapes.
- Do not assume a backend can run every custom op just because the code parses.
