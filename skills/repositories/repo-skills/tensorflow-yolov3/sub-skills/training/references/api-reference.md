# Training API and Configuration Reference

This file summarizes the repository contracts that matter when configuring
`train.py`.

## `cfg.YOLO` fields used by training

| Field | Default shape/value | Training meaning |
|---|---:|---|
| `cfg.YOLO.CLASSES` | `./data/classes/coco.names` | Text file with one class name per line. The line count becomes `num_classes`, controls output-head width `3 * (num_classes + 5)`, and bounds valid annotation class ids. |
| `cfg.YOLO.ANCHORS` | `./data/anchors/basline_anchors.txt` | Comma-separated anchors reshaped to `(3, 3, 2)` by `get_anchors`. Used for label assignment and prediction decoding. |
| `cfg.YOLO.MOVING_AVE_DECAY` | `0.9995` | Decay for `tf.train.ExponentialMovingAverage` over trainable variables. |
| `cfg.YOLO.STRIDES` | `[8, 16, 32]` | Detection scales for small/medium/large output grids. Input sizes should be divisible by `32`. |
| `cfg.YOLO.ANCHOR_PER_SCALE` | `3` | Number of anchors per detection scale; label tensors use this dimension. |
| `cfg.YOLO.IOU_LOSS_THRESH` | `0.5` | Background mask threshold inside confidence loss. |
| `cfg.YOLO.UPSAMPLE_METHOD` | `resize` | Upsampling implementation used while building the YOLOv3 graph. |
| `cfg.YOLO.ORIGINAL_WEIGHT` | `./checkpoint/yolov3_coco.ckpt` | Source checkpoint prefix used by conversion, not directly by `train.py`. |
| `cfg.YOLO.DEMO_WEIGHT` | `./checkpoint/yolov3_coco_demo.ckpt` | Converted checkpoint target normally assigned to `cfg.TRAIN.INITIAL_WEIGHT`. |

## `cfg.TRAIN` fields

| Field | Default | Contract |
|---|---:|---|
| `cfg.TRAIN.ANNOT_PATH` | `./data/dataset/voc_train.txt` | Training annotation text file. Each kept row must contain an image path and at least one box token. |
| `cfg.TRAIN.BATCH_SIZE` | `6` | Number of samples per yielded batch. The last partial batch wraps around to earlier samples. |
| `cfg.TRAIN.INPUT_SIZE` | `[320, 352, 384, 416, 448, 480, 512, 544, 576, 608]` | Multi-scale square input sizes. A random value is selected every yielded batch. |
| `cfg.TRAIN.DATA_AUG` | `True` | Enables random horizontal flip, crop, and translation in `Dataset.parse_annotation`. |
| `cfg.TRAIN.LEARN_RATE_INIT` | `1e-4` | Warmup target and cosine-decay starting learning rate. |
| `cfg.TRAIN.LEARN_RATE_END` | `1e-6` | Final cosine-decay learning rate. |
| `cfg.TRAIN.WARMUP_EPOCHS` | `2` | Warmup duration in epochs, multiplied by `steps_per_period`. |
| `cfg.TRAIN.FISRT_STAGE_EPOCHS` | `20` | Misspelled first-stage epoch count. During these epochs only output heads are trainable. |
| `cfg.TRAIN.SECOND_STAGE_EPOCHS` | `30` | Epoch count for all-variable training. |
| `cfg.TRAIN.INITIAL_WEIGHT` | `./checkpoint/yolov3_coco_demo.ckpt` | TensorFlow checkpoint prefix restored before training. Missing restore falls back to scratch training and disables first stage. |

## `cfg.TEST` fields used during training validation

`YoloTrain` constructs `Dataset('test')` and feeds it through the same loss graph
at the end of every epoch. The validation loader uses `cfg.TEST.ANNOT_PATH`,
`cfg.TEST.BATCH_SIZE`, and `cfg.TEST.DATA_AUG` for path, batch size, and
augmentation mode. However, the dataset iterator chooses its batch input size
from `cfg.TRAIN.INPUT_SIZE` for both train and test loaders, so validation inside
`train.py` is also multi-scale.

## Annotation row contract

A row has this whitespace-separated schema:

```text
image_path x_min,y_min,x_max,y_max,class_id x_min,y_min,x_max,y_max,class_id ...
```

Rules to enforce before training:

- `image_path` must exist from the process working directory used for training.
- `class_id` is a zero-based integer index into `cfg.YOLO.CLASSES`.
- Coordinates may be decimal strings, but the loader converts them with
  `int(float(value))`.
- `x_max > x_min` and `y_max > y_min` are required; invalid boxes are dropped
  after preprocessing and can create empty-label samples.
- Keep boxes inside the original image extent when possible; the README warns
  that `x_max < width` and `y_max < height`, and the loader later clips boxes to
  reduce NaN risk.

## `Dataset(dataset_type)` behavior

Construction:

```python
Dataset('train')  # uses cfg.TRAIN.ANNOT_PATH, BATCH_SIZE, INPUT_SIZE, DATA_AUG
Dataset('test')   # uses cfg.TEST.ANNOT_PATH, BATCH_SIZE, DATA_AUG; see input-size caveat above
```

At initialization it reads classes, anchors, strides, and annotations; shuffles
annotation rows; computes `num_batchs = ceil(num_samples / batch_size)`; and sets
`max_bbox_per_scale = 150`.

One yielded batch returns:

| Index | Array | Shape for selected `S`, batch `B`, classes `C` |
|---:|---|---|
| 0 | `batch_image` | `[B, S, S, 3]` |
| 1 | `batch_label_sbbox` | `[B, S/8, S/8, 3, 5 + C]` |
| 2 | `batch_label_mbbox` | `[B, S/16, S/16, 3, 5 + C]` |
| 3 | `batch_label_lbbox` | `[B, S/32, S/32, 3, 5 + C]` |
| 4 | `batch_sbboxes` | `[B, 150, 4]` |
| 5 | `batch_mbboxes` | `[B, 150, 4]` |
| 6 | `batch_lbboxes` | `[B, 150, 4]` |

`parse_annotation` reads each image with OpenCV, optionally applies
augmentation, letterboxes to the selected input size, rescales boxes, drops
zero/negative-area boxes, and clips coordinates.

`preprocess_true_boxes` assigns each box to anchors at strides `8`, `16`, and
`32`. If any anchor at a scale has IoU above `0.3`, that scale's label cell is
filled. Otherwise the single best anchor receives the object. Class labels use
label smoothing with `deta = 0.01`.

## `YOLOV3` graph pieces relevant to training

`YOLOV3(input_data, trainable)` reads classes and anchors at graph construction.
It builds Darknet-53 and three detection heads:

- `conv_sbbox` / `pred_sbbox` for stride `8`;
- `conv_mbbox` / `pred_mbbox` for stride `16`;
- `conv_lbbox` / `pred_lbbox` for stride `32`.

Each `pred_*` tensor has shape:

```text
[batch, output_size, output_size, 3, 5 + num_classes]
```

where the last dimension is `(x, y, w, h, objectness, class probabilities...)`.

`compute_loss` returns three scalar components:

- `giou_loss` from generalized IoU over positive boxes;
- `conf_loss` from focal-weighted objectness/background cross entropy;
- `prob_loss` from class-probability cross entropy on positive boxes.

`train.py` sums them as `loss = giou_loss + conf_loss + prob_loss` and writes all
four scalars plus learning rate to TensorBoard.

## Restore and save semantics

`train.py` creates two savers:

- `loader = tf.train.Saver(self.net_var)` where `self.net_var` is captured after
  the model graph is built. This restores network variables from
  `cfg.TRAIN.INITIAL_WEIGHT` but does not restore the optimizer state.
- `saver = tf.train.Saver(tf.global_variables(), max_to_keep=10)` for epoch-end
  checkpoints.

A checkpoint prefix is usable when TensorFlow can see matching `.index` and
`.data-*` artifacts for that prefix. A `.meta` file is needed by some conversion
scripts but is not normally required by `Saver.restore` in `train.py`.
