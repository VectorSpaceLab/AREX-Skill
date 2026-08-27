# API reference: tf-faster-rcnn architecture internals

This reference records source-level API facts for researchers modifying the model graph. It is based on static source inspection plus the production environment report. It deliberately avoids claims that a full TensorFlow graph executed successfully.

## Verified constructor and architecture signatures

| API | Verified signature | Notes |
| --- | --- | --- |
| `nets.vgg16.vgg16` | `vgg16()` | Constructor body calls `Network.__init__`, sets `_feat_stride = [16]`, `_feat_compress = [1/16]`, `_scope = 'vgg_16'`. |
| `nets.resnet_v1.resnetv1` | `resnetv1(num_layers=50)` | Supports block layouts for 50, 101, and 152 layers; other depths raise `NotImplementedError`. Scope is `resnet_v1_<num_layers>`. |
| `nets.mobilenet_v1.mobilenetv1` | `mobilenetv1()` | Uses `cfg.MOBILENET.DEPTH_MULTIPLIER`; scope is `MobilenetV1`. |
| `nets.network.Network.create_architecture` | `create_architecture(mode, num_classes, tag=None, anchor_scales=(8,16,32), anchor_ratios=(0.5,1,2))` | Creates placeholders, stores mode/classes/anchor values, builds network, returns output/loss/prediction dict. Requires `tag is not None`. |

The raw class method signature in source includes `self`; the user-facing inherited method is shown above without `self`.

## `Network` class contracts

Source: `lib/nets/network.py`.

### Main state dictionaries

- `_predictions`: RPN and RCNN output tensors such as `rpn_cls_score`, `rpn_cls_prob`, `rpn_bbox_pred`, `rois`, `cls_score`, `cls_prob`, `bbox_pred`.
- `_losses`: `cross_entropy`, `loss_box`, `rpn_cross_entropy`, `rpn_loss_box`, `total_loss` in training mode.
- `_anchor_targets`: `rpn_labels`, `rpn_bbox_targets`, `rpn_bbox_inside_weights`, `rpn_bbox_outside_weights`.
- `_proposal_targets`: `rois`, `labels`, `bbox_targets`, `bbox_inside_weights`, `bbox_outside_weights`.
- `_layers['head']`: backbone feature map used by `extract_head`.
- `_variables_to_fix`: variables requiring pretrained-weight reshaping or RGB/BGR conversion.

### Placeholders created by `create_architecture`

- `_image`: `tf.float32`, shape `[1, None, None, 3]`.
- `_im_info`: `tf.float32`, shape `[3]`; convention is `[height, width, scale]`.
- `_gt_boxes`: `tf.float32`, shape `[None, 5]`; `(x1, y1, x2, y2, class)`.

### Build path

`create_architecture` calls `_build_network(training)`, where `training = mode == 'TRAIN'` and `testing = mode == 'TEST'`.

`_build_network` performs:

1. `_image_to_head(is_training)` from the selected backbone.
2. `_anchor_component()` to populate `_anchors` and `_anchor_length`.
3. `_region_proposal(net_conv, is_training, initializer)`.
4. `_crop_pool_layer(net_conv, rois, 'pool5')` when `cfg.POOLING_MODE == 'crop'`; other pooling modes raise `NotImplementedError` in this path.
5. `_head_to_tail(pool5, is_training)` from the selected backbone.
6. `_region_classification(fc7, is_training, initializer, initializer_bbox)`.
7. `_add_losses()` only outside testing mode.

### Runtime helper methods

- `extract_head(sess, image)`: feeds only `_image`, returns `_layers['head']`.
- `test_image(sess, image, im_info)`: returns `cls_score`, `cls_prob`, `bbox_pred`, `rois` from a TensorFlow session.
- `get_summary(sess, blobs)`: expects `blobs['data']`, `blobs['im_info']`, and `blobs['gt_boxes']`.
- `train_step`, `train_step_with_summary`, `train_step_no_return`: all expect the same blobs and an already-created `train_op`.

These helpers require a built TensorFlow graph and working runtime; this sub-skill only documents their source contract.

## Backbone-specific contracts

### VGG16 (`lib/nets/vgg16.py`)

- `_image_to_head` builds `conv1` through `conv5`, with `conv1`/`conv2` frozen (`trainable=False`) and deeper blocks trainable according to `is_training`.
- `_head_to_tail` flattens pool5 then builds `fc6` and `fc7`, using dropout only during training.
- `get_variables_to_restore` skips `vgg_16/fc6/weights:0`, `vgg_16/fc7/weights:0`, and `vgg_16/conv1/conv1_1/weights:0`, storing them in `_variables_to_fix`.
- `fix_variables` restores FC convolutional weights and reverses RGB channels for the first conv layer.

### ResNet V1 (`lib/nets/resnet_v1.py`)

- `resnet_arg_scope(is_training=True, batch_norm_decay=0.997, batch_norm_epsilon=1e-5, batch_norm_scale=True)` freezes batch norm statistics and trainability in `batch_norm_params`.
- `_decide_blocks` supports `num_layers` 50, 101, or 152.
- `_build_base` manually builds `conv1` and `pool1` to avoid inconsistent SAME padding across image sizes.
- `_image_to_head` uses `cfg.RESNET.FIXED_BLOCKS` in `[0,3]` to freeze initial blocks and uses blocks before the final block for the convolutional head.
- `_head_to_tail` runs the final block and uses `tf.reduce_mean(fc7, axis=[1, 2])`.
- `get_variables_to_restore` skips the first conv layer for RGB/BGR conversion; `fix_variables` restores and reverses `conv1/weights`.

### MobileNet V1 (`lib/nets/mobilenet_v1.py`)

- `separable_conv2d_same(inputs, kernel_size, stride, rate=1, scope=None)` implements explicit padding for stride > 1.
- `mobilenet_v1_base(inputs, conv_defs, starting_layer=0, min_depth=8, depth_multiplier=1.0, output_stride=None, reuse=None, scope=None)` builds a sequence from `Conv` and `DepthSepConv` named tuples.
- `mobilenet_v1_arg_scope(is_training=True, stddev=0.09)` sets batch norm parameters, ReLU6 activations, and MobileNet weight regularization.
- `_image_to_head` uses `cfg.MOBILENET.FIXED_LAYERS` in `[0,12]` and layers `_CONV_DEFS[:12]` for the head.
- `_head_to_tail` uses `_CONV_DEFS[12:]` and reduces spatial dimensions by mean.
- `fix_variables` reverses RGB channels and scales the first convolution weights by `(255.0 / 2.0)`.

## RPN and proposal utility APIs

Sources: `lib/layer_utils/*.py` and `lib/nets/network.py`.

| API | Source signature | Contract |
| --- | --- | --- |
| `generate_anchors` | `generate_anchors(base_size=16, ratios=[0.5, 1, 2], scales=2 ** np.arange(3, 6))` | Enumerates reference anchors. Production smoke verified default shape `(9, 4)`. |
| `generate_anchors_pre` | `generate_anchors_pre(height, width, feat_stride, anchor_scales=(8,16,32), anchor_ratios=(0.5,1,2))` | Tiles anchors over the feature map and returns `(anchors, length)`. |
| `generate_anchors_pre_tf` | `generate_anchors_pre_tf(height, width, feat_stride=16, anchor_scales=(8,16,32), anchor_ratios=(0.5,1,2))` | TensorFlow version of anchor tiling. |
| `proposal_layer` | `proposal_layer(rpn_cls_prob, rpn_bbox_pred, im_info, cfg_key, _feat_stride, anchors, num_anchors)` | Applies bbox deltas, clipping, score sort, NMS, and returns ROIs shaped `(N, 5)` with batch index in column 0 plus scores. |
| `proposal_layer_tf` | `proposal_layer_tf(rpn_cls_prob, rpn_bbox_pred, im_info, cfg_key, _feat_stride, anchors, num_anchors)` | TensorFlow NMS variant used when `cfg.USE_E2E_TF` is true. |
| `proposal_top_layer` | `proposal_top_layer(rpn_cls_prob, rpn_bbox_pred, im_info, _feat_stride, anchors, num_anchors)` | TEST-only top proposal selector without NMS. |
| `proposal_top_layer_tf` | `proposal_top_layer_tf(rpn_cls_prob, rpn_bbox_pred, im_info, _feat_stride, anchors, num_anchors)` | TensorFlow top-k version. |
| `anchor_target_layer` | `anchor_target_layer(rpn_cls_score, gt_boxes, im_info, _feat_stride, all_anchors, num_anchors)` | Assigns anchor labels and bbox targets for RPN training. |
| `proposal_target_layer` | `proposal_target_layer(rpn_rois, rpn_scores, gt_boxes, _num_classes)` | Samples foreground/background RoIs and produces RCNN classification/regression targets. |

## Bounding-box APIs

Source: `lib/model/bbox_transform.py`.

- `bbox_transform(ex_rois, gt_rois)`: returns `(dx, dy, dw, dh)` deltas from example ROIs to GT boxes.
- `bbox_transform_inv(boxes, deltas)`: applies deltas to boxes; supports multi-class deltas via `0::4`, `1::4`, etc.
- `clip_boxes(boxes, im_shape)`: clips `x` coordinates to `[0, width-1]` and `y` coordinates to `[0, height-1]`.
- `bbox_transform_inv_tf(boxes, deltas)` and `clip_boxes_tf(boxes, im_info)`: TensorFlow variants for the E2E TF path.

## Inference/post-processing API hooks

Source: `lib/model/test.py`.

- `_get_image_blob(im)`: expects BGR image input, subtracts `cfg.PIXEL_MEANS`, scales by `cfg.TEST.SCALES` and `cfg.TEST.MAX_SIZE`, and returns `(blob, im_scale_factors)`.
- `_get_blobs(im)`: returns a `blobs` dict with `data` and image scale factors.
- `im_detect(sess, net, im)`: creates `im_info`, calls `net.test_image`, rescales ROIs, applies bbox regression if `cfg.TEST.BBOX_REG`, and returns `(scores, pred_boxes)`.
- `apply_nms(all_boxes, thresh)`: applies configured NMS to per-class/per-image detections.
- `test_net(sess, net, imdb, weights_filename, max_per_image=100, thresh=0.)`: full dataset evaluation loop; route execution to `training-and-evaluation`.

## Roidb and minibatch APIs

Sources: `lib/roi_data_layer/*.py`.

- `RoIDataLayer(roidb, num_classes, random=False)` stores a roidb, class count, and randomization flag, then shuffles indices.
- `RoIDataLayer.forward()` returns minibatch blobs from `get_minibatch`.
- `get_minibatch(roidb, num_classes)` asserts single-image operation, returns:
  - `data`: NHWC float32 blob.
  - `gt_boxes`: `(N, 5)` scaled boxes plus class id.
  - `im_info`: `[blob_height, blob_width, image_scale]`.
- `prepare_roidb(imdb)` enriches `imdb.roidb` entries with `image`, `width`, `height`, `max_classes`, and `max_overlaps`.

Expected roidb entry fields for minibatch flow include `image`, `flipped`, `boxes`, `gt_classes`, `gt_overlaps`, and, when aspect grouping is enabled, `width` and `height`.

## Blob, timer, and visualization utilities

Sources: `lib/utils/blob.py`, `timer.py`, and `visualization.py`.

- `im_list_to_blob(ims)`: pads prepared images into an NHWC float32 blob.
- `prep_im_for_blob(im, pixel_means, target_size, max_size)`: subtracts means and rescales with OpenCV.
- `Timer.tic()` / `Timer.toc(average=True)`: records elapsed and average time.
- `draw_bounding_boxes(image, gt_boxes, im_info)`: draws GT boxes for TensorBoard summaries after undoing image scale.
