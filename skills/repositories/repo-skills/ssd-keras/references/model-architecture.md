# Model Architecture Reference

This repository revolves around three SSD builders and a small set of custom layers and utility functions that are reused by training, inference, and evaluation.

## Model builders

- `ssd_300(image_size, n_classes, mode='training', ...)`
  - Canonical SSD300 model built on a reduced atrous VGG-16 backbone.
  - Uses 6 predictor layers.
  - Best fit for the Pascal VOC and COCO-style workflows documented in the notebooks.
- `ssd_512(image_size, n_classes, mode='training', ...)`
  - SSD512 variant with the same overall design but a larger input size.
  - Uses 7 predictor layers.
- `build_model(image_size, n_classes, mode='training', ...)`
  - SSD7 template model.
  - Much smaller and faster than the full SSD300 / SSD512 builders.
  - Useful as a smoke path and as a template for alternate base networks.

### Common builder arguments

The builders share the same major configuration family:

- `image_size`: `(height, width, channels)` tuple.
- `n_classes`: number of positive classes, excluding background.
- `mode`: `training`, `inference`, or `inference_fast`.
- `scales`, `min_scale`, `max_scale`: anchor box scale schedule.
- `aspect_ratios_global`, `aspect_ratios_per_layer`: aspect ratio configuration.
- `steps`, `offsets`, `clip_boxes`, `variances`, `coords`, `normalize_coords`.
- `subtract_mean`, `divide_by_stddev`, `swap_channels`.
- `confidence_thresh`, `iou_threshold`, `top_k`, `nms_max_output_size`.
- `return_predictor_sizes`: return predictor map sizes along with the model.

## Modes and outputs

- `training`
  - Returns the raw prediction tensor.
  - Use with `SSDInputEncoder` and `SSDLoss.compute_loss`.
- `inference`
  - Adds the `DecodeDetections` layer.
  - Returns decoded boxes in `[class_id, confidence, xmin, ymin, xmax, ymax]` form.
- `inference_fast`
  - Adds the `DecodeDetectionsFast` layer.
  - Uses a faster, globally suppressed decoding path.

## Custom layers

- `AnchorBoxes(img_height, img_width, this_scale, next_scale, ...)`
  - Generates the anchor box tensor attached to each predictor cell.
  - TensorFlow backend only.
  - Output shape is `(batch, height, width, n_boxes, 8)`.
- `DecodeDetections(confidence_thresh=0.01, iou_threshold=0.45, top_k=200, ...)`
  - Decodes raw SSD output inside the model graph.
  - TensorFlow backend only.
  - Expects centroids coordinates and returns zero-padded top-k detections.
- `DecodeDetectionsFast(...)`
  - Faster inference-time decoder with global NMS.
- `L2Normalization(gamma_init=20)`
  - Used on the `conv4_3` feature map in the SSD300 / SSD512 builders.

## Training and decoding helpers

- `SSDLoss(neg_pos_ratio=3, n_neg_min=0, alpha=1.0)`
  - Implements the SSD classification + localization loss.
  - `compute_loss(y_true, y_pred)` expects the model's raw tensor shape.
- `SSDInputEncoder(img_height, img_width, n_classes, predictor_sizes, ...)`
  - Builds anchor boxes and encodes ground-truth boxes for training.
  - Its scales, aspect ratios, steps, offsets, and coordinate settings must match the model.
- `decode_detections(y_pred, ...)` and `decode_detections_fast(y_pred, ...)`
  - NumPy post-processing helpers used when the model is in training mode or when you want explicit decoding outside the graph.
- `convert_coordinates`, `iou`
  - Shared bounding-box math utilities.
- `match_bipartite_greedy`, `match_multi`
  - Matching helpers used by the encoder.
- `sample_tensors(weights_list, sampling_instructions, ...)`
  - Utility for class-count adaptation when transferring pretrained weights.

## Practical reminder

The three builders are not interchangeable at runtime.

- Training workflows need the raw tensor and the matching encoder.
- Inference and evaluation workflows need either the graph-based decoder or the NumPy decoder helpers.
- Any change to scales, aspect ratios, or coordinate normalization must be mirrored between the builder and the encoder / decoder that consumes its output.
