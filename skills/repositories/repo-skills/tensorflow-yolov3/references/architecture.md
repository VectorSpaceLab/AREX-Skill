# Architecture and Shared API Notes

## Purpose

Read this for repo-wide model, config, and helper facts that several sub-skills share.

## Source layout

- `core/config.py`: central `cfg` object built from `easydict.EasyDict`.
- `core/common.py`: convolution, residual block, route, and upsample layer helpers.
- `core/backbone.py`: Darknet-53 backbone returning two route tensors plus final features.
- `core/yolov3.py`: `YOLOV3` class, prediction tensor decoding, GIoU/IoU, focal weighting, and loss computation.
- `core/dataset.py`: training/test dataset iterator, augmentation, annotation parsing, and target tensor construction.
- `core/utils.py`: class/anchor reading, image preprocessing, drawing, NMS, box postprocessing, and frozen-graph import.

## Key config defaults

```text
cfg.YOLO.CLASSES          = ./data/classes/coco.names
cfg.YOLO.ANCHORS          = ./data/anchors/basline_anchors.txt
cfg.YOLO.STRIDES          = [8, 16, 32]
cfg.YOLO.ANCHOR_PER_SCALE = 3
cfg.YOLO.IOU_LOSS_THRESH  = 0.5
cfg.YOLO.UPSAMPLE_METHOD  = resize
cfg.YOLO.ORIGINAL_WEIGHT  = ./checkpoint/yolov3_coco.ckpt
cfg.YOLO.DEMO_WEIGHT      = ./checkpoint/yolov3_coco_demo.ckpt
cfg.TRAIN.ANNOT_PATH      = ./data/dataset/voc_train.txt
cfg.TEST.ANNOT_PATH       = ./data/dataset/voc_test.txt
```

The training epoch field is misspelled in source as `cfg.TRAIN.FISRT_STAGE_EPOCHS`.

## Model construction

`YOLOV3(input_data, trainable)` reads class and anchor files during initialization and builds three output heads:

- small-box output: stride 8, grid 52×52 for 416×416 input
- medium-box output: stride 16, grid 26×26 for 416×416 input
- large-box output: stride 32, grid 13×13 for 416×416 input

For the default 80 COCO classes, the decoded prediction shapes verified by graph construction are:

```text
pred_sbbox: [1, 52, 52, 3, 85]
pred_mbbox: [1, 26, 26, 3, 85]
pred_lbbox: [1, 13, 13, 3, 85]
```

The final channel dimension is `5 + num_classes`: center `x,y`, size `w,h`, objectness score, and class probabilities.

## Helper API facts

Signatures verified from the prepared inspection environment:

```python
core.utils.read_class_names(class_file_name)
core.utils.get_anchors(anchors_path)
core.utils.image_preporcess(image, target_size, gt_boxes=None)
core.utils.nms(bboxes, iou_threshold, sigma=0.3, method='nms')
core.utils.postprocess_boxes(pred_bbox, org_img_shape, input_size, score_threshold)
core.dataset.Dataset(dataset_type)
core.yolov3.YOLOV3(input_data, trainable)
```

Important behavior:

- `read_class_names` returns `{integer_id: class_name}` from one class per line.
- `get_anchors` reads the first line of comma-separated floats and reshapes it to `(3, 3, 2)`.
- `image_preporcess` is intentionally misspelled; it converts BGR to RGB, letterboxes to target size, normalizes to `[0,1]`, and optionally updates ground-truth boxes.
- `nms` supports `method='nms'` and `method='soft-nms'`.
- `postprocess_boxes` converts YOLO center/width/height predictions back to original-image corner boxes and returns `[xmin, ymin, xmax, ymax, score, class]` rows.

## Cross-skill dependencies

- Data-preparation owns class/anchor/annotation correctness. Training, inference, conversion, and evaluation should route class/anchor mismatch questions there first.
- Conversion owns creating `yolov3_coco_demo.ckpt` and `yolov3_coco.pb` from checkpoint artifacts.
- Inference owns reading a frozen PB and producing postprocessed detections.
- Training owns checkpoint creation through `train.py`.
- Evaluation owns converting checkpoint predictions to mAP text files and computing AP/mAP.
