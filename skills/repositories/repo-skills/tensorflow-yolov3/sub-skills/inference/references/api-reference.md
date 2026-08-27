# Inference API and data contracts

## Frozen graph tensor contract

The frozen PB is loaded with TensorFlow graph import and the following return elements:

| Role | Tensor name | Use |
|---|---|---|
| Input image batch | `input/input_data:0` | Feed a float image batch, normally shaped `[1, 416, 416, 3]` after letterbox preprocessing. |
| Small-box prediction | `pred_sbbox/concat_2:0` | YOLO prediction tensor for the stride-8 / 52x52 scale when `input_size=416`. |
| Medium-box prediction | `pred_mbbox/concat_2:0` | YOLO prediction tensor for the stride-16 / 26x26 scale when `input_size=416`. |
| Large-box prediction | `pred_lbbox/concat_2:0` | YOLO prediction tensor for the stride-32 / 13x13 scale when `input_size=416`. |

For the default COCO model, each prediction row is reshaped with `5 + num_classes = 85`. A graph-construction smoke for the default 416/80-class setup produced output shapes consistent with:

- `[1, 52, 52, 3, 85]`
- `[1, 26, 26, 3, 85]`
- `[1, 13, 13, 3, 85]`

If the graph was frozen for a custom class count, update `num_classes` and verify that the final dimension is `5 + num_classes`.

## Default config/data paths

| Config or demo value | Default | Notes |
|---|---|---|
| PB file | `./yolov3_coco.pb` | Produced by the graph-freezing workflow, not bundled by default. |
| Image path | `./docs/images/road.jpeg` | Demo image path. Override for user images. |
| Video path | `./docs/images/road.mp4` | Demo video path. Use `0` for default camera. |
| Classes | `./data/classes/coco.names` | Default 80 COCO class names. |
| Anchors | `./data/anchors/basline_anchors.txt` | Default config spelling is `basline_anchors.txt`. The file should contain 18 comma-separated numbers. |
| Input size | `416` | Demo inference size. Training config supports more sizes, but demos use 416. |
| Score threshold | `0.3` | Used by `postprocess_boxes`. |
| IoU threshold | `0.45` | Used by class-wise NMS. |

## Helper function contracts

### `read_class_names(class_file_name)`

Loads a newline-delimited class-name file into `{id: name}`. IDs start at zero and follow file order. Blank or mismatched class files cause class-indexing and empty-detection problems later.

### `get_anchors(anchors_path)`

Reads the first line of a comma-separated anchor file, parses floats, and reshapes them to `(3, 3, 2)`. In the image/video demos, anchors are not read directly after the graph is frozen, but they are part of the model/config contract that produced the graph. Mismatched anchors during training or conversion can produce poor detections even if the PB tensor names are correct.

### `read_pb_return_tensors(graph, pb_file, return_elements)`

Reads a serialized `GraphDef` from `pb_file`, imports it into `graph`, and returns the requested tensors. It does not run inference by itself. If any return element is missing, graph import fails with a return-element error. Use the bundled contract checker to catch this before writing session code.

### `image_preporcess(image, target_size, gt_boxes=None)`

The helper name is misspelled as `image_preporcess` in the original code. It:

1. Converts the input image with `cv2.COLOR_BGR2RGB`.
2. Casts to `float32`.
3. Letterbox-resizes the image to `target_size` while preserving aspect ratio.
4. Fills padding with value `128.0` before normalization.
5. Divides by `255.0`.
6. Returns either the preprocessed image or `(image, adjusted_gt_boxes)`.

Inference normally calls it as:

```python
image_data = utils.image_preporcess(np.copy(original_image), [input_size, input_size])
image_data = image_data[np.newaxis, ...]
```

Caveat: the demo script converts OpenCV BGR to RGB before calling this helper, while the helper also converts BGR to RGB internally. If refactoring, choose one color convention deliberately and test a known image to avoid channel swaps.

### Prediction concatenation

After session execution:

```python
pred_bbox = np.concatenate([
    np.reshape(pred_sbbox, (-1, 5 + num_classes)),
    np.reshape(pred_mbbox, (-1, 5 + num_classes)),
    np.reshape(pred_lbbox, (-1, 5 + num_classes)),
], axis=0)
```

For the 416/80-class default, the concatenated row count is `(52*52*3) + (26*26*3) + (13*13*3) = 10647`, with 85 values per row.

### `postprocess_boxes(pred_bbox, org_img_shape, input_size, score_threshold)`

Inputs:

- `pred_bbox`: rows of `[x_center, y_center, width, height, objectness, class_probabilities...]` after prediction concatenation;
- `org_img_shape`: `(height, width)` from the original image or frame;
- `input_size`: demo default `416`;
- `score_threshold`: demo default `0.3`.

Behavior:

1. Converts center/width/height boxes to `[xmin, ymin, xmax, ymax]`.
2. Reverses letterbox padding/scale into original image coordinates.
3. Clips coordinates to image bounds.
4. Discards invalid boxes and low-confidence boxes.
5. Selects `class = argmax(class_probabilities)` and `score = objectness * selected_class_probability`.

Return format:

```text
[xmin, ymin, xmax, ymax, score, class]
```

The returned `class` value is numeric; cast it to `int` for class-name lookup.

### `nms(bboxes, iou_threshold, sigma=0.3, method='nms')`

Inputs:

- `bboxes`: array with rows `[xmin, ymin, xmax, ymax, score, class]`;
- `iou_threshold`: demo default `0.45`;
- `method`: either `nms` or `soft-nms`.

Behavior:

- Runs class-wise suppression.
- For `nms`, boxes above the IoU threshold with a higher-scored selected box are suppressed.
- For `soft-nms`, overlapping boxes have scores decayed by `exp(-(iou ** 2 / sigma))`.
- Returns a Python list of selected boxes, not necessarily a NumPy array.

### `draw_bbox(image, bboxes, classes, show_label=True)`

Draws `[xmin, ymin, xmax, ymax, score, class]` rows on an image. Pass `classes` explicitly when running outside the default working directory. The function's default argument reads the configured class file at import time, so missing `./data/classes/coco.names` can fail before the function is called.

## Output conventions for downstream tools

Recommended serialized detection fields:

```text
image_id xmin ymin xmax ymax score class_id class_name
```

Where:

- `xmin`, `ymin`, `xmax`, `ymax` are clipped to the original image/frame dimensions;
- `score` is a float after score thresholding and NMS;
- `class_id` is an integer index into the selected class-name file;
- `class_name` is optional but should be filled when class names are available.

## Non-execution validation

Use [the bundled PB contract checker](../scripts/pb_inference_contract.py) for preflight validation. It imports the frozen graph to check tensor names, but it does not create a session or run predictions.
