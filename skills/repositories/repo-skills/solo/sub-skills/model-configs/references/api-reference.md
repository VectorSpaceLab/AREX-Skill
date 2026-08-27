# Model/config API reference

## Registries and builders

| Registry | Builder | Representative registered types | Constructor role |
|---|---|---|---|
| `BACKBONES` | `build_backbone` | `ResNet`, `ResNeXt`, `HRNet`, `SSDVGG` | image -> feature-map list |
| `NECKS` | `build_neck` | `FPN`, `BFP`, `HRFPN`, `NASFPN` | feature-map list -> pyramid/list |
| `HEADS` | `build_head` | SOLO, SOLOv2, RPN/Retina/FCOS/Fovea/RepPoints/SSD heads; bbox/mask heads | task-specific prediction/loss |
| `LOSSES` | `build_loss` | `FocalLoss`, `CrossEntropyLoss`, `DiceLoss`, Smooth/IoU/Balanced L1, GHMC/GHMR | differentiable loss module |
| `DETECTORS` | `build_detector` | `SOLO`, `SOLOv2`, `SingleStageDetector`, `TwoStageDetector`, R-CNN families | graph assembly and train/test dispatch |
| `ROI_EXTRACTORS` | `build_roi_extractor` | `SingleRoIExtractor` | ROI feature extraction |
| `SHARED_HEADS` | `build_shared_head` | `ResLayer` | optional shared ROI feature processing |

`build_from_cfg` copies a config, pops `type`, resolves a string through the
registry, merges default args only when a key is absent, and calls the class with
keyword arguments. A missing type, duplicate registration, unknown key, or import
omission has a direct and usually early failure.

## Detector graph contracts

| Base/variant | Built fields | Training/test boundary |
|---|---|---|
| `BaseDetector` | `fp16_enabled` and abstract methods | `forward(return_loss=True)` expects one tensor plus metadata list; inference uses augmentation-nested lists |
| `SingleStageDetector` | backbone, optional neck, bbox head | dense head `loss` and `get_bboxes`; output converted with `bbox2result` |
| `TwoStageDetector` | backbone/neck, optional RPN, ROI extractor(s), bbox/mask heads | proposals -> assign/sample -> ROI losses; inference can return bbox and mask results |
| `SingleStageInsDetector` | backbone, optional neck, bbox head, optional mask feature head | head `loss` receives masks; `simple_test` calls `get_seg`; `aug_test` is not implemented here |
| `SOLO` | `SingleStageInsDetector` with no mask feature head | `SOLOHead` or decoupled head is configured as `bbox_head` despite instance-mask semantics |
| `SOLOv2` | `SingleStageInsDetector` plus `MaskFeatHead` | dynamic kernels from bbox head act on shared mask features |

The `bbox_head` name in `SingleStageInsDetector` is historical. For SOLO it does
not mean a bounding-box regression head. Use the detector's actual class and head
contract, not the field name alone.

## Common configuration keys

| Area | Keys to inspect | Failure if inconsistent |
|---|---|---|
| Backbone | `type`, `depth`, `num_stages`, `out_indices`, `frozen_stages`, `style`, `dcn`, `stage_with_dcn` | wrong feature count/channels or missing DCN extension |
| Neck | `type`, `in_channels`, `out_channels`, `start_level`, `end_level`, `num_outs` | head receives wrong levels or widths |
| SOLO head | `num_classes`, `in_channels`, `seg_feat_channels`, `strides`, `scale_ranges`, `num_grids`, `sigma`, losses | grid/feature resolution mismatch, invalid targets, loss shape errors |
| SOLOv2 head | above plus `ins_out_channels`; optional `use_dcn_in_tower`, `type_dcn` | kernel channel mismatch or missing custom op |
| Mask feature head | `in_channels`, `out_channels`, `start_level`, `end_level`, `num_classes`, `norm_cfg` | dynamic kernel and mask feature dimensions disagree |
| Bbox post-process | `score_thr`, `nms_pre`, NMS IoU/type, `max_per_img` | empty/overfull results or unsupported op |
| SOLO post-process | `mask_thr`, `update_thr`, `kernel`, `sigma`, `max_per_img` | invalid matrix-NMS behavior or mask filtering |
| Runtime | `optimizer`, `optimizer_config`, `lr_config`, `fp16`, `workflow`, `total_epochs` | schedule/precision behavior differs from intended run |

## Loss conventions

- `CrossEntropyLoss` supports standard, sigmoid binary, and mask modes; this
  snapshot asserts that reduction overrides are one of `None`, `none`, `mean`, or
  `sum`.
- `FocalLoss` is sigmoid-only in this implementation, with `gamma`, `alpha`,
  reduction, and `loss_weight`; it calls the compiled sigmoid focal-loss op.
- `IoULoss`, `BoundedIoULoss`, and `GIoULoss` operate on aligned `(N, 4)` boxes
  and use the shared weighted-loss reduction helpers.
- SOLO heads define their local `dice_loss` helper rather than registering a
  general `DiceLoss` in the central `LOSSES` registry in this snapshot. The
  representative configs still use a nested `loss_ins=dict(type='DiceLoss',
  use_sigmoid=True, loss_weight=3.0)`, so treat this as a SOLO-head-specific
  configuration contract and verify the exact head implementation before
  reusing it in another family.
- `loss_weight` scales the returned loss; `avg_factor` changes reduction and must
  be compatible with the number of positive instances/labels.

## Post-processing contracts

`mmdet.core.post_processing.bbox_nms.multiclass_nms` expects `multi_scores` with
column 0 reserved for background. It loops over classes 1..N-1, filters scores,
selects either class-agnostic `(N,4)` boxes or the class slice from `(N,4*C)`,
then calls the configured wrapper. Return values are `(bboxes[N,5], labels[N])`.

`mmdet.ops.nms.nms` accepts a NumPy array or tensor containing `(x1,y1,x2,y2,
score)`. It returns kept detections and indices in the input's type. CPU dispatch
uses `nms_cpu`; CUDA dispatch uses `nms_cuda`. `soft_nms` is CPU-backed and accepts
`linear` or `gaussian`.

`matrix_nms(seg_masks, cate_labels, cate_scores, kernel, sigma)` is pure PyTorch
in this snapshot. It computes pairwise mask IoU only for same-class masks and
returns decayed category scores. `kernel` must be `gaussian` or `linear`; other
values raise `NotImplementedError`. SOLOv2's score path is therefore distinct
from bbox multiclass NMS.

## Inference APIs

- `init_detector(config, checkpoint=None, device='cuda:0')` accepts a filename or
  `mmcv.Config`, forces `config.model.pretrained=None`, builds the detector, and
  optionally loads a checkpoint before moving/evaluating the model.
- `inference_detector(model, img)` expects a path or image array and applies the
  configured test pipeline. It uses the model's saved `cfg` and device.
- A no-checkpoint build is useful for construction/shape checks but does not
  produce meaningful predictions. Do not use random weights to claim recovery.
- `BaseDetector.forward` has different nesting for training and testing. For
  training, pass a tensor and metadata list; for testing, pass list-of-tensors and
  list-of-list-of-metadata, with one batch image per GPU in this snapshot.

## Native evidence map

`tests/test_config.py` builds a curated representative set of detector configs
with pretrained weights removed. `tests/test_heads.py` checks empty/non-empty
anchor and bbox head losses and bbox refinement edge cases. `tests/test_nms.py`
checks CPU NumPy/tensor float32/float64 and conditional GPU float32 NMS. These are
useful candidates only after the target legacy environment is prepared. No native
candidate here authorizes full training.
