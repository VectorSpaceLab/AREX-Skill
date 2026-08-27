# Configuration reference

## `get_config(is_train)` contract

Every launch config in this repository exposes:

```python
def get_config(is_train):
    ...
    return General, KvstoreParam, RpnParam, RoiParam, BboxParam, DatasetParam, \
           ModelParam, OptimizeParam, TestParam, \
           transform, data_name, label_name, metric_list
```

The launchers call it in train or test mode and then patch each namespace with `patch_config_as_nothrow(...)` so missing optional attributes resolve to `None` instead of raising.

### Required namespaces

- `General`
  - Experiment name, logging cadence, per-GPU batch size, FP16 flag, loader workers, profiling toggle.
- `KvstoreParam`
  - `kvstore`, `batch_image`, `gpus`, `fp16`.
- `RpnParam`
  - Shared detector settings for anchors, proposals, and loss geometry.
- `RoiParam`
  - RoI pooling / align geometry for two-stage detectors.
- `BboxParam`
  - Second-stage classifier / regressor shape and target settings.
- `DatasetParam`
  - `image_set`, usually a tuple of roidb split names.
- `ModelParam`
  - `train_symbol`, `test_symbol`, optional `rpn_test_symbol`, pretrain path, memonger, and `process_weight`.
- `OptimizeParam`
  - `optimizer`, `schedule`, and optional `warmup`.
- `TestParam`
  - Checkpoint location, NMS, score cutoff, COCO annotation, and optional `process_roidb` / `process_output` hooks.
- `transform`, `data_name`, `label_name`, `metric_list`
  - Data pipeline, MXNet iterator names, and metric objects returned to the launcher.

### Common optional namespaces

Some configs also define local helper namespaces that are not returned but are consumed when constructing the detector:

- `MaskParam`, `MaskRoiParam` in Mask R-CNN configs.
- `KDParam` and `teacher_param` in KD configs.
- `Trident`, `ScaleRange`, and other branch helpers in TridentNet configs.
- `FCOSParam` and `throwout_param` in FCOS configs.

## Static-shape assumptions

SimpleDet uses symbolic MXNet graphs with fixed shapes. The config must keep the preprocessing and the network shape contract aligned.

Key rules:

- `ResizeParam.short` / `ResizeParam.long` determine the resized image envelope.
- `PadParam.short` / `PadParam.long` determine the padded canvas.
- `PadParam.max_num_gt` must be large enough for the target dataset.
- Mask configs also use `PadParam.max_len_gt_poly` for encoded polygons.
- `RpnParam.anchor_generate.max_side` must cover the maximum resized side used by anchor caching.
- `data_name` / `label_name` must match the `transform` list and the symbol inputs.
- Test-mode inputs always include `im_info`, `im_id`, and `rec_id`.

## Namespace facts to inspect first

When comparing two configs, look at these fields before anything else:

- `General.name`
- `General.batch_image`
- `General.fp16`
- `KvstoreParam.gpus`
- `KvstoreParam.kvstore`
- `DatasetParam.image_set`
- `ModelParam.pretrain.prefix` and `epoch`
- `OptimizeParam.schedule.begin_epoch`, `end_epoch`, and `lr_iter`
- `TestParam.model.prefix` and `epoch`
- `TestParam.nms.type` and `thr`

## Selection matrix for major families

| Family | Example configs | Training / test route | Notes |
|---|---|---|---|
| Faster R-CNN + FPN | `config/faster_r50v1_fpn_1x.py`, `config/resnet_v1b/faster_r50v1b_fpn_1x.py` | `detection_train.py`, `detection_test.py` | Two-stage baseline. Uses RoIAlign and COCO bbox evaluation. |
| Mask R-CNN + FPN | `config/mask_r50v1_fpn_1x.py`, `config/resnet_v1b/mask_r50v1b_fpn_1x.py` | `detection_train.py`, `mask_test.py` | Adds `MaskParam` / `MaskRoiParam`, polygon preprocessing, and segmentation evaluation. |
| RetinaNet | `config/retina_r50v1_fpn_1x.py`, `config/resnet_v1b/retina_r50v1b_fpn_1x.py` | `detection_train.py`, `detection_test.py` | One-stage anchor-based detector with focal loss and class-aware box decoding. |
| FreeAnchor | `config/FreeAnchor/free_anchor_r50v1_fpn_1x.py` | `detection_train.py`, `detection_test.py` | Retina-style backbone with `bbox_thr` matching and score-thresholded proposals. |
| FCOS | `config/fcos_r50v1_fpn_1x.py` | `detection_train.py`, `detection_test.py` | Anchor-free family. Uses its own `FCOSParam`, loss settings, and proposal thresholds. |
| TridentNet | `config/tridentnet_r101v2c4_c5_2x.py` | `detection_train.py`, `detection_test.py` | Multi-branch scale-aware family. Branch-aware post-processing is part of the config. |
| Knowledge distillation | `config/kd/faster_r50v1b_fpn_1x_fitnet_g5.py` | `detection_train.py`, `detection_test.py` | Adds teacher checkpoint settings and KD loss heads. |
| Finetune / VOC | `config/finetune/faster_r50v1_fpn_voc07_1x.py` | `detection_train.py`, `detection_test.py` | Changes dataset splits, class count, and pretrained weights. |

## Practical checks

- If `num_class` changes, verify the bbox head and metric names match the new dataset.
- If the detector is mask-aware, confirm `MaskParam.num_fg_roi` and `MaskRoiParam` still fit the proposal sampling layout.
- If the config is one-stage, expect fewer label tensors and different post-processing behavior.
- If `TestParam.coco.annotation` is `None`, the test script will synthesize a COCO object from the roidb.
