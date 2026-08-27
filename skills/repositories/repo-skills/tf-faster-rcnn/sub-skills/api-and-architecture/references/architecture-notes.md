# Architecture notes and extension points

These notes explain how source modules connect. They are intended for source modification and review, not for proving runtime execution.

## High-level graph construction

```text
backbone instance
  └─ create_architecture(mode, num_classes, tag, anchor_scales, anchor_ratios)
       ├─ placeholders: image, im_info, gt_boxes
       ├─ _build_network(training)
       │    ├─ _image_to_head(is_training)          # backbone conv feature map
       │    ├─ _anchor_component()                  # tiled anchors from scales/ratios
       │    ├─ _region_proposal(net_conv, ...)      # RPN scores, bbox deltas, rois
       │    ├─ _crop_pool_layer(net_conv, rois)     # crop_and_resize + max pool
       │    ├─ _head_to_tail(pool5, is_training)    # backbone tail / fc7 feature
       │    └─ _region_classification(fc7, ...)     # cls_prob and bbox_pred
       ├─ TEST: unnormalizes bbox_pred with TRAIN bbox means/stds
       └─ TRAIN: adds RPN/RCNN losses and summaries
```

`mode == 'TRAIN'` controls training behavior. `mode == 'TEST'` controls bbox-prediction unnormalization. The source does not validate arbitrary modes beyond these booleans, so callers should use the repo's conventional uppercase strings.

## Anchor flow

1. `create_architecture` stores `self._anchor_scales`, `self._anchor_ratios`, and computes `self._num_anchors = len(scales) * len(ratios)`.
2. `_anchor_component` computes feature-map height/width from `im_info` and `self._feat_stride[0]`.
3. `_anchor_component` calls either:
   - `generate_anchors_pre(...)` through `tf.py_func`, or
   - `generate_anchors_pre_tf(...)` when `cfg.USE_E2E_TF` is true.
4. Tiled anchors are stored as `self._anchors`; the total length is stored as `self._anchor_length`.
5. `_region_proposal` uses `self._num_anchors` for RPN channel counts and proposal slicing.

Default anchor scales/ratios produce 9 anchors per feature-map location. If you change anchors, inspect all `A * 2` and `A * 4` uses: RPN class logits, bbox deltas, anchor labels, bbox target tensors, proposal layers, and any checkpoint variable shapes.

## RPN and proposal flow

### Training path

```text
net_conv
  └─ rpn_conv/3x3
       ├─ rpn_cls_score                # A * 2 channels
       ├─ rpn_cls_score_reshape
       ├─ rpn_cls_prob_reshape
       ├─ rpn_cls_prob                 # A * 2 channels
       └─ rpn_bbox_pred                # A * 4 channels
            ├─ _proposal_layer(..., mode='TRAIN')
            ├─ _anchor_target_layer(...)
            └─ _proposal_target_layer(...)
```

`_anchor_target_layer` uses GT boxes and all anchors to create RPN labels and bbox weights. `_proposal_target_layer` samples RoIs for RCNN classification/regression and appends GT boxes when `cfg.TRAIN.USE_GT` is true.

### Test path

```text
if cfg.TEST.MODE == 'nms':
    _proposal_layer(..., mode='TEST')
elif cfg.TEST.MODE == 'top':
    _proposal_top_layer(...)
else:
    NotImplementedError
```

`proposal_layer` applies bbox deltas, clips proposals, sorts scores, and runs NMS. `proposal_top_layer` selects top proposals without NMS. The default config uses NMS.

## Bbox transform conventions

- Boxes use inclusive pixel coordinates: widths and heights are computed as `x2 - x1 + 1` and `y2 - y1 + 1`.
- Deltas are ordered `(dx, dy, dw, dh)`.
- Multi-class bbox predictions are interleaved by class: class `j` occupies columns `j*4:(j+1)*4`.
- Clip functions use image shape/info as `[height, width]` order for bounds.

## Image blob preprocessing

Training and testing both use NHWC float32 blobs with OpenCV-style BGR input.

- Training path: `roi_data_layer.minibatch._get_image_blob` reads `roidb[i]['image']`, flips if `roidb[i]['flipped']`, and calls `prep_im_for_blob` with `cfg.TRAIN.SCALES` and `cfg.TRAIN.MAX_SIZE`.
- Test path: `model.test._get_image_blob` accepts an in-memory BGR image, subtracts `cfg.PIXEL_MEANS`, and uses `cfg.TEST.SCALES` and `cfg.TEST.MAX_SIZE`.
- `im_info` must be `[blob_height, blob_width, scale]`.

The repo assumes a single image in core train/test network paths: minibatch code asserts `len(im_scales) == 1` and `len(roidb) == 1`, while `Network._image` is shaped `[1, None, None, 3]`.

## Roidb structure

A prepared roidb entry should contain at least:

| Field | Purpose |
| --- | --- |
| `image` | Absolute or checkout-relative image file path used by OpenCV. |
| `width`, `height` | Used for aspect grouping in `RoIDataLayer`. |
| `flipped` | Whether minibatch construction mirrors the image horizontally. |
| `boxes` | Array of `(x1, y1, x2, y2)` boxes. |
| `gt_classes` | Per-box class ids; zero means background. |
| `gt_overlaps` | Sparse overlap matrix; code calls `.toarray()`. |
| `max_classes`, `max_overlaps` | Added by `prepare_roidb`; useful for sampling sanity checks. |

`get_minibatch` converts this into `data`, `gt_boxes`, and `im_info` blobs.

## Backbone extension checklist

When adding a new backbone class:

1. Subclass `Network`; call `Network.__init__(self)`.
2. Set `_feat_stride` to match the spatial downsampling of the feature map consumed by RPN. Existing backbones use `[16]`.
3. Set `_feat_compress` consistently with `_feat_stride`.
4. Set `_scope` to match pretrained checkpoint variable names.
5. Implement `_image_to_head` and put the final convolutional feature map in `self._layers['head']`.
6. Implement `_head_to_tail` and return the feature vector/tensor consumed by `_region_classification`.
7. Decide how early layers are frozen; mirror `cfg.RESNET.FIXED_BLOCKS` or `cfg.MOBILENET.FIXED_LAYERS` patterns only if they fit the new backbone.
8. Implement `get_variables_to_restore` and `fix_variables` for any first-layer RGB/BGR conversion, pretrained FC-to-conv reshape, or scale conversion.
9. Update user-facing CLI net selectors and checkpoint naming only after source-level API inspection. Route command details to sibling CLI sub-skills.

## Anchor/proposal extension checklist

When changing anchors, proposal selection, or NMS:

1. Keep `self._num_anchors = len(anchor_scales) * len(anchor_ratios)` synchronized with generated anchors.
2. Check RPN classification and bbox output channels.
3. Check `anchor_target_layer` output shapes:
   - labels: `[1, 1, A * height, width]`
   - bbox targets/weights: `[1, height, width, A * 4]`
4. Check proposal layer score slicing: foreground scores are `rpn_cls_prob[:, :, :, num_anchors:]`.
5. Check config keys for `TRAIN` and `TEST`: `RPN_PRE_NMS_TOP_N`, `RPN_POST_NMS_TOP_N`, and `RPN_NMS_THRESH`.
6. If relying on `model.nms_wrapper.nms`, confirm CPU/GPU NMS backend setup in `installation-and-configuration`.

## Verification boundary

The bundled inspector validates source presence and signatures with AST parsing. It does not import repo modules, instantiate TensorFlow objects, run `tf.py_func`, compile Cython extensions, or validate checkpoint compatibility.
