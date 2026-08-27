# InternImage Detection Config Catalog

This catalog distills public InternImage detection config evidence from source labels under `detection/configs/**` and the detection config README files. Use these names as command arguments; do not reopen original config files for operating instructions.

## Quick selection rules

- For a small wiring check, prefer COCO `coco/mask_rcnn_internimage_t_fpn_1x_coco` with `--eval bbox segm` or a single-image demo. It is still a real model run and needs MMDetection, checkpoint, data or image, and DCNv3 readiness.
- Use COCO Mask R-CNN T/S/B configs for standard instance segmentation with FPN and 1x/3x schedules.
- Use COCO Cascade Mask R-CNN L/XL configs for larger instance segmentation models; memory and checkpoint size are substantially higher.
- Use DINO/CB-DINO configs for detection-only box metrics. They usually evaluate with `bbox`; they are not the right first choice for SAM prompting because the inspected SAM source expects a mask-capable detector object.
- LVIS, OpenImages, and VOC released configs are CB-InternImage-H DINO families initialized from Objects365-style detection checkpoints. They are large and dataset-specific.
- CrowdHuman uses a custom `CrowdHumanDataset` registration and converted JSON annotations. Its inspected config is bbox-focused even though the base file name includes cascade-mask wording.
- Match checkpoint to config family, dataset, detector head, backbone size, and scale suffix. Do not use a classification checkpoint as the positional checkpoint for `test.py`.

## Config keys accepted by the helper

| Dataset | Config key | Relative config path | Intended metric/action | Notes |
| --- | --- | --- | --- | --- |
| COCO | `coco/mask_rcnn_internimage_t_fpn_1x_coco` | `configs/coco/mask_rcnn_internimage_t_fpn_1x_coco.py` | `bbox segm` | Mask R-CNN, InternImage-T, 1x schedule, reported 47.2 box / 42.5 mask mAP. |
| COCO | `coco/mask_rcnn_internimage_t_fpn_3x_coco` | `configs/coco/mask_rcnn_internimage_t_fpn_3x_coco.py` | `bbox segm` | InternImage-T, 3x, reported 49.1 box / 43.7 mask mAP. |
| COCO | `coco/mask_rcnn_internimage_s_fpn_1x_coco` | `configs/coco/mask_rcnn_internimage_s_fpn_1x_coco.py` | `bbox segm` | InternImage-S, 1x, reported 47.8 box / 43.3 mask mAP. |
| COCO | `coco/mask_rcnn_internimage_s_fpn_3x_coco` | `configs/coco/mask_rcnn_internimage_s_fpn_3x_coco.py` | `bbox segm` | InternImage-S, 3x, reported 49.7 box / 44.5 mask mAP. |
| COCO | `coco/mask_rcnn_internimage_b_fpn_1x_coco` | `configs/coco/mask_rcnn_internimage_b_fpn_1x_coco.py` | `bbox segm` | InternImage-B, 1x, reported 48.8 box / 44.0 mask mAP. |
| COCO | `coco/mask_rcnn_internimage_b_fpn_3x_coco` | `configs/coco/mask_rcnn_internimage_b_fpn_3x_coco.py` | `bbox segm` | InternImage-B, 3x, reported 50.3 box / 44.8 mask mAP. |
| COCO | `coco/mask_rcnn_internimage_t_fpn_1x_coco_with_dcnv4` | `configs/coco/mask_rcnn_internimage_t_fpn_1x_coco_with_dcnv4.py` | `bbox segm` | Variant name indicates DCNv4 operator use; treat operator support as deployment/backend-sensitive. |
| COCO | `coco/cascade_internimage_l_fpn_1x_coco` | `configs/coco/cascade_internimage_l_fpn_1x_coco.py` | `bbox segm` | Cascade Mask R-CNN, InternImage-L, 1x, reported 54.9 box / 47.7 mask mAP. |
| COCO | `coco/cascade_internimage_l_fpn_3x_coco` | `configs/coco/cascade_internimage_l_fpn_3x_coco.py` | `bbox segm` | InternImage-L, 3x, reported 56.1 box / 48.5 mask mAP. |
| COCO | `coco/cascade_internimage_xl_fpn_1x_coco` | `configs/coco/cascade_internimage_xl_fpn_1x_coco.py` | `bbox segm` | InternImage-XL, 1x, reported 55.3 box / 48.1 mask mAP. |
| COCO | `coco/cascade_internimage_xl_fpn_3x_coco` | `configs/coco/cascade_internimage_xl_fpn_3x_coco.py` | `bbox segm` | InternImage-XL, 3x, reported 56.2 box / 48.8 mask mAP. |
| COCO | `coco/dino_4scale_internimage_t_1x_coco_layer_wise_lr` | `configs/coco/dino_4scale_internimage_t_1x_coco_layer_wise_lr.py` | `bbox` | DINO, InternImage-T, layer-wise LR, reported 53.9 box mAP. |
| COCO | `coco/dino_4scale_internimage_l_1x_coco_layer_wise_lr` | `configs/coco/dino_4scale_internimage_l_1x_coco_layer_wise_lr.py` | `bbox` | DINO, InternImage-L, layer-wise LR, reported 57.5 box mAP in config README evidence. |
| COCO | `coco/dino_4scale_internimage_l_1x_coco_0.1x_backbone_lr` | `configs/coco/dino_4scale_internimage_l_1x_coco_0.1x_backbone_lr.py` | `bbox` | DINO, InternImage-L, 0.1x backbone LR, reported 57.6 box mAP. |
| COCO | `coco/dino_4scale_internimage_h_objects365_coco_ss` | `configs/coco/dino_4scale_internimage_h_objects365_coco_ss.py` | `bbox` | DINO, InternImage-H, Objects365 to COCO, reported 63.4 single-scale box mAP. |
| COCO | `coco/dino_4scale_cbinternimage_h_objects365_coco_ss` | `configs/coco/dino_4scale_cbinternimage_h_objects365_coco_ss.py` | `bbox` | CB-DINO, CB-InternImage-H, Objects365 to COCO, reported 64.5 single-scale and 65.0 TTA box mAP. |
| COCO | `coco/dino_4scale_internimage_g_objects365_coco_ss` | `configs/coco/dino_4scale_internimage_g_objects365_coco_ss.py` | `bbox` | DINO, InternImage-G, very large model, reported 64.2 single-scale box mAP. |
| LVIS | `lvis/dino_4scale_cbinternimage_h_objects365_lvis_minival_ss` | `configs/lvis/dino_4scale_cbinternimage_h_objects365_lvis_minival_ss.py` | `bbox` | CB-DINO H; README evidence reports 65.8 minival box AP and 62.3/63.2 val ss/ms. |
| LVIS | `lvis/dino_4scale_cbinternimage_h_objects365_lvis_val_ss` | `configs/lvis/dino_4scale_cbinternimage_h_objects365_lvis_val_ss.py` | `bbox` | Same family, val split variant. |
| OpenImages | `openimages/dino_4scale_cbinternimage_h_objects365_openimages_ss` | `configs/openimages/dino_4scale_cbinternimage_h_objects365_openimages_ss.py` | `mAP` | CB-DINO H; README evidence reports 74.1 mAP single-scale. |
| VOC | `voc/dino_4scale_cbinternimage_h_objects365_voc07` | `configs/voc/dino_4scale_cbinternimage_h_objects365_voc07.py` | `mAP` | CB-DINO H; README evidence reports 94.0 on VOC 2007. |
| VOC | `voc/dino_4scale_cbinternimage_h_objects365_voc12` | `configs/voc/dino_4scale_cbinternimage_h_objects365_voc12.py` | `mAP` | CB-DINO H; README evidence reports 97.2 on VOC 2012. |
| CrowdHuman | `crowd_human/cascade_internimage_xl_fpn_3x_crowd_human` | `configs/crowd_human/cascade_internimage_xl_fpn_3x_crowd_human.py` | `bbox` | Custom one-class CrowdHuman dataset; released table had TBD metrics. |

The helper also accepts bare config stems, such as `mask_rcnn_internimage_t_fpn_1x_coco`, when unambiguous.

## Dataset base facts

| Dataset base | Dataset type | Expected data root in config evidence | Annotation/image facts | Default evaluator signal |
| --- | --- | --- | --- | --- |
| COCO instance | `CocoDataset` | `data/coco/` | `annotations/instances_train2017.json`, `annotations/instances_val2017.json`, `train2017/`, `val2017/`, masks loaded | `bbox`, `segm`, classwise |
| COCO detection | `CocoDataset` | `data/coco/` | Same split names as COCO instance, bbox-only annotations in pipeline | `bbox`, classwise |
| LVIS v1 | `LVISV1Dataset` | `data/lvis_v1/` | train uses `lvis_v1_train.json`; val/minival variants use `lvis_v1_val.json` or `lvis_v1_minival.json`; image prefix is the LVIS root | `bbox` |
| OpenImages | `OpenImagesDataset` | `data/OpenImages/` | CSV bbox annotations, class description file, label hierarchy file, validation image metas, and image-level labels | `mAP` |
| VOC 2007/2012 | `VOCDataset` | `data/VOCdevkit/` | train repeats VOC2007+VOC2012 trainval; test uses VOC2007 test | `mAP` |
| CrowdHuman | `CrowdHumanDataset` | `data/CrowdHuman/` | expects converted `annotations/annotation_train.json` and `annotation_val.json` plus `Images/`; class tuple is `person` | `bbox` |

## Architecture and optimizer facts that affect config choice

- InternImage backbones are registered through `mmdet_custom` as `type='InternImage'`; coupled-backbone variants use `type='CBInternImage'`.
- Detection configs set `core_op='DCNv3'`. A config name containing `with_dcnv4` or `use_dcn_v4_op` requires explicit operator/backend verification before runtime claims.
- Mask R-CNN T/S/B COCO configs use FPN and AdamW with `CustomLayerDecayOptimizerConstructor`. The inspected T config sets channels `[64, 128, 256, 512]`, depths `[4, 4, 18, 4]`, and samples per GPU `2`.
- Large H/G DINO configs set InternImage-H/G-specific fields such as `dw_kernel_size=5`, post-norm flags, `center_feature_scale=True`, and `with_cp=True` for memory. They also use gradient clipping and custom DINO heads/transformers.
- CB-DINO configs use the `CBDINO` detector, `CBChannelMapper`, `CBDINOHead`, and custom DINO transformer components; these are not available in plain MMDetection without `mmdet_custom` imports.
- CrowdHuman uses one class and custom annotation conversion. Do not compare its one-class bbox metrics with COCO mask metrics.

## Checkpoint naming and compatibility notes

- The released checkpoint names usually mirror config stems. The command builder intentionally requires explicit `--checkpoint` values for test, demo, and SAM so it does not guess network/cache state.
- Some DINO configs contain `load_from` pointing to Objects365-initialized detector checkpoints. That is training initialization evidence, not permission to assume the checkpoint is already present.
- For evaluation/demo, the positional checkpoint must be a detection checkpoint whose detector head and class count match the config. A classification `.pth` pretraining checkpoint will commonly produce missing or unexpected keys.
- If checkpoint metadata lacks `CLASSES`, the source falls back to dataset classes from the selected config; this can hide mismatches until evaluation or visualization looks wrong.
- Treat reported model-zoo scores as source evidence only. This generated sub-skill did not reproduce those metrics.
