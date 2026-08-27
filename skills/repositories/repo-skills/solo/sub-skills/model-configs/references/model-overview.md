# SOLO-era model overview

This reference distills the pinned SOLO repository's model and config families.
Names below are registry `type` strings, not import paths.

## Choose the family

| Goal | Detector type | Typical head graph | Representative config shape | Main output |
|---|---|---|---|---|
| Box-free instance segmentation | `SOLO` | `ResNet/ResNeXt/HRNet -> FPN -> SOLOHead` | `solo/solo_r50_fpn_*` | per-instance masks and categories |
| Decoupled SOLO | `SOLO` | backbone -> FPN -> `DecoupledSOLOHead` | `solo/decoupled_solo_r50_fpn_*` | x/y factorized mask predictions + categories |
| Lightweight decoupled SOLO | `SOLO` | backbone -> FPN -> `DecoupledSOLOLightHead` | `solo/decoupled_solo_light_*` | same contract, fewer channels and optional DCN |
| Dynamic-kernel instance segmentation | `SOLOv2` | backbone -> FPN -> `SOLOv2Head` + `MaskFeatHead` | `solov2/solov2_r50_fpn_*` | category scores + dynamic masks |
| Lightweight SOLOv2 | `SOLOv2` | smaller backbone/head -> `SOLOv2Head` + `MaskFeatHead` | `solov2/solov2_light_*` | same result contract with reduced capacity |
| Anchor/RPN detection | `RPN`, `FasterRCNN`, `MaskRCNN`, `CascadeRCNN`, `HybridTaskCascade` | backbone -> FPN -> RPN/ROI extractors/heads | root configs, `htc/`, `dcn/` | boxes, optionally masks |
| Dense one-stage detection | `RetinaNet`, `FCOS`, `FOVEA`, `ATSS`, `RepPoints`, `SSD` | backbone -> neck -> dense head | `retinanet_*`, `fcos/`, `foveabox/`, `reppoints/` | boxes and labels |

SOLO's README describes SOLO as box-free and grouping-free. This codebase is
based on MMDetection v1.0.0-era APIs; the config strings and constructor
boundaries are not interchangeable with current MMDetection releases.

## SOLO data and tensor contracts

The standard SOLO train pipeline loads annotations with `with_bbox=True` and
`with_mask=True`, then collects `img`, `gt_bboxes`, `gt_labels`, and `gt_masks`.
`SingleStageInsDetector.forward_train` extracts features, runs the bbox head,
optionally runs `MaskFeatHead`, and calls the head's `loss` with ground-truth
boxes, labels, masks, image metadata, and `train_cfg`.

A standard SOLO config has:

- `model.type='SOLO'`;
- a backbone such as `ResNet` with `out_indices=(0, 1, 2, 3)`;
- `FPN` with matching `in_channels` and `num_outs=5`;
- a head with `num_grids`, `strides`, `scale_ranges`, and `num_classes`;
- `DiceLoss` for instance masks and sigmoid `FocalLoss` for categories;
- test keys `nms_pre`, `score_thr`, `mask_thr`, `update_thr`, `kernel`, `sigma`,
  and `max_per_img`.

`SOLOHead` predicts per-grid mask logits and category logits. The target builder
assigns instances to feature levels by square-root box area, uses mask centers and
neighboring grid cells, rescales masks to the feature resolution, and computes
Dice and category losses. `DecoupledSOLOHead` instead creates separate x and y
instance branches and combines their sigmoid predictions.

SOLOv2's standard config adds:

- `model.type='SOLOv2'`;
- `bbox_head.type='SOLOv2Head'` (or `SOLOv2LightHead`);
- `mask_feat_head.type='MaskFeatHead'` with compatible `out_channels` and
  `num_classes`/kernel width;
- dynamic mask kernel settings such as `ins_out_channels`.

The SOLOv2 head emits category predictions and kernel predictions. `MaskFeatHead`
produces a shared mask feature map. At inference, selected kernels are applied to
that map, masks are resized/cropped to image metadata, category scores are
filtered, and matrix NMS decays scores. `get_seg` returns the instance-segmentation
result structure expected by `tools/test_ins.py` and inference helpers.

## Backbone, neck, and shape decisions

Available registered backbones include `ResNet`, `ResNeXt`, `HRNet`, and `SSDVGG`.
Available necks include `FPN`, `BFP`, `HRFPN`, and `NASFPN`. `ResNet` channel
widths in representative configs are `[256, 512, 1024, 2048]` for depth 50/101;
light R18 uses `[64, 128, 256, 512]`. A custom backbone must emit the number and
width of feature maps promised by its config. A custom neck must return the
number of levels expected by its head.

A list-valued component config is built as `nn.Sequential`; this only works when
each module's input/output contract composes. Do not put unrelated head configs in
one list merely to avoid editing the detector class.

## Representative variants

- `SOLO_R50_1x`, `SOLO_R50_3x`, and `SOLO_R101_3x` are baseline examples.
- Decoupled SOLO variants use `DecoupledSOLOHead`; light variants lower head
  complexity and may enable DCN.
- SOLOv2 R50/R101 variants use the full head; R18/R34/R50 light variants use
  smaller feature dimensions and often smaller image scales.
- DCN variants set backbone `dcn` and `stage_with_dcn`, or head
  `use_dcn_in_tower` and `type_dcn='DCN'`. They are not CPU-safe fallbacks.
- The model zoo's reported latency/AP is benchmark evidence for its historical
  environment, not a promise for a new PyTorch/CUDA/toolchain combination.
