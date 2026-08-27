# Detection model overview

## Choose the family

| Family | Builder | Detector shape | Best fit | Important output/target contract |
|---|---|---|---|---|
| DETR | `DETR.build_detr(config)` | ResNet feature -> projection -> transformer encoder/decoder -> learned object queries | Query-based end-to-end detection and transformer/loss inspection | `pred_logits [B,Q,C+1]`, normalized `pred_boxes [B,Q,4]`; training also exposes auxiliary decoder outputs |
| Swin | `Swin.build_swin_det(config)` | Swin stages -> FPN -> RPN -> RoI head | Mask-RCNN-style COCO detection with shifted-window backbone | Absolute `gt_boxes`, contiguous `gt_classes`, FPN pyramid, post-NMS rows `[label,score,xmin,ymin,xmax,ymax]` |
| PVTv2 | `PVTv2.build_pvtv2_det(config)` | PVTv2 stages -> FPN -> RPN -> RoI head | Pyramid-transformer backbone variants B0-B5 and B2-linear | Same RPN/RoI target and output contract as Swin; backbone channels/depths differ |

The builders live in standalone source roots. Resolve imports from one family at
a time; `config`, `coco`, `box_ops`, `transforms`, and `utils` are repeated
module names. Shared `object_detection/det_heads/` and `det_necks/` are copied
into family trees or imported by their local relative setup. Do not combine
family source roots in one process unless you have inspected `sys.modules` and
explicitly controlled import order.

## DETR path

`build_detr(config)` constructs a backbone with positional encoding, a
transformer, the DETR query/class/box heads, a Hungarian matcher, a
`SetCriterion`, and a bbox postprocessor. The transformer expects a padded
nested tensor with a boolean-like spatial mask. The final decoder output is
projected to `num_classes + 1`, where the final class is the no-object class;
box output is passed through sigmoid and is therefore normalized center-size
coordinates.

Training losses are:

- `loss_ce`: cross entropy with a reduced no-object weight;
- `loss_bbox`: L1 regression over matched queries;
- `loss_giou`: generalized IoU loss after conversion to corner coordinates;
- `cardinality_error`: logging-only count error;
- optional decoder-index suffixes when auxiliary losses are enabled.

The matcher combines class, L1 box, and GIoU costs and uses SciPy's
`linear_sum_assignment`. Empty-target batches are a special edge case; use a
non-empty tiny target for a model smoke and investigate empty-target behavior
before changing matcher code.

The postprocessor takes `target_sizes` in `[height,width]` order and scales
`[x0,y0,x1,y1]` with `[width,height,width,height]`. Preserve this order when
adapting outputs for COCO.

## Swin/PVTv2 path

Both builders chain a hierarchical backbone to an FPN and Mask-RCNN-style
heads. The FPN consumes stage feature maps and creates lateral/top-down maps;
`LastLevelMaxPool` adds a coarser feature. The RPN makes anchors and proposals,
then the RoI head classifies/regresses sampled proposals. During training, the
model combines RoI losses with RPN losses. During evaluation, post-processing
clips/decodes boxes and applies score filtering and NMS.

Swin config evidence includes stage depths `[2,2,6,2]` for the shipped tiny
YAML, heads `[3,6,12,24]`, FPN channels `[96,192,384,768]`, and 4-level
strides `[4,8,16,32]`. PVTv2 B0 includes embedding dimensions
`[32,64,160,256]`, stage depths `[2,2,2,2]`, and the matching FPN channels.
These are examples, not universal defaults; use the selected YAML.

The Swin/PVTv2 config field is historically misspelled as `ROI.NUM_ClASSES`
(capital `l` in `ClASSES`) in the local code. Preserve the field spelling when
editing a config. `MODEL.NUM_CLASSES` is not the RoI head's class count in
these builders.

## Evidence limits

Repository READMEs report COCO mAP for named checkpoints, but no checkpoint or
COCO data is bundled. Do not reproduce or quote those numbers as a local
verification result. The native DETR tests include useful box conversion and
shape expectations, but several tests are skipped and `test_detr.py` expects a
local `t.npy`; use them as evidence candidates only.
