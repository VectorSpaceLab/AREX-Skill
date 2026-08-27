# Model Families

This table is task-oriented: it tells you where to start, what is structurally
special, what often breaks, and how confident the claim is from the inspected
source.

Legend:
- **Backed** = directly supported by the inspected config, README, or builder.
- **Code-evidenced, not fully runtime-verified here** = the implementation is in
  the tree, but the Creator pass did not execute the backend.

| Family | Start from | What is special | Inputs / outputs | Optional deps / custom ops | Likely failure modes | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Faster R-CNN | `config/faster_*.py`, `config/resnet_v1b/faster_*.py`, `symbol/builder.py` | Baseline two-stage detector with anchor RPN, ROI pooling/alignment, bbox head | `gt_bbox`, `im_info`; test emits `rec_id, im_id, im_info, cls_score, bbox_xyxy` | `bbox_target`, `proposal`, `decode_bbox`, FPN ROI assign helpers | class-count mismatch, ROI stride mismatch, stale checkpoints with changed head width | Backed |
| Mask R-CNN | `config/mask_*.py`, `models/maskrcnn/*`, `doc/fully_annotated_config.py` | Faster R-CNN + mask branch, polygon labels, mask post-processing | adds `gt_poly`; test emits mask tensors and post-NMS boxes | `ProposalMaskTarget`, `BboxPostProcessing`, `sigmoid_cross_entropy` | missing `gt_poly`, wrong mask resolution, class-specific mask channel mismatch | Backed |
| Cascade R-CNN | `config/cascade_*.py`, `models/cascade_rcnn/*` | Three RCNN stages with stage-specific regression targets and weights | multiple bbox heads; stage 1/2/3 share proposal flow but not decode targets | stage-specific bbox heads and proposal refinement | forgetting to update `BboxParam2nd/3rd`, class-agnostic decode mismatch, broken stage weights | Backed |
| RetinaNet | `config/retina_*.py`, `models/retinanet/*` | Single-stage anchor detector, focal loss, no ROI stage | output is class scores + decoded boxes directly from feature pyramid | `decode_retina`, focal loss, `bbox_norm` | anchor/top-N mismatch, `min_det_score` too high, background channel handling | Backed |
| FCOS | `config/fcos_*.py`, `models/FCOS/*` | Anchor-free detector; location-based target assignment and proposal fusion | uses `make_fcos_gt`; no RPN sampling | `get_proposal_single_stage`, `get_batch_proposal`, focal/BCE/IoU loss ops | `throwout_param` import order, stride range mismatch, ignore-label bugs | Backed |
| TridentNet | `config/tridentnet_*.py`, `config/resnet_v1b/tridentnet_*.py`, `models/tridentnet/*` | Multi-branch, scale-aware training with branch filtering | branch-aware outputs and branch-specific postprocessing | `process_branch_outputs`, `process_branch_rpn_outputs`, `process_branch_mask_outputs` | wrong `num_branch`, inconsistent `valid_ranges`, batch-size scaling errors | Backed |
| FreeAnchor | `config/FreeAnchor/*.py`, `models/FreeAnchor/*` | RetinaNet variant with positive/negative bag losses | uses anchor bags, not proposal sampling | `mxnext.tvm.decode_bbox`, FreeAnchor ops | missing anchor cache, threshold tuning mistakes, num-class mismatch | Backed; backend helpers not executed here |
| KD / FitNet | `config/kd/*.py`, `models/KD/*` | Adds a teacher feature mimic loss to Faster/Retina families | requires `teacher_label` in training graph | teacher module builder and mimic head | teacher feature stage mismatch, channel mismatch, missing teacher params | Backed |
| DCN | `config/dcn/*.py`, `models/dcn/builder.py` | Swaps in deformable ResNet stages for C4/C5 or FPN backbones | same detector contracts as the base family | `mx.sym.contrib.DeformableConvolution` | backend missing deformable conv op, FP16 instability, incompatible pretrained weights | Backed; runtime backend unverified here |
| NASFPN | `config/NASFPN/*.py`, `models/NASFPN/*` | NAS-FPN / hand-crafted TD-BU necks for RetinaNet | single-stage outputs, larger inputs and BN-heavy necks | `RetinaNetHeadWithBN`, `RetinaNetNeckWithBN`, custom neck search blocks | BN mode mismatch, input size too small for pyramid depth, wrong stage count | Backed |
| FPG / PAFPN | `config/FPG/*.py`, `models/FPG/*` | Multi-stage feature grid or path aggregation necks | usually Faster R-CNN with FPN-like outputs | `syncbn`, stage grid fusion code | stage depth mismatch, channel mismatch, incorrect pyramid naming | Backed |
| RepPoints | `config/RepPoints/*.py`, `models/RepPoints/*` | Anchor-free point-set representation; optional DCN refinement | point targets instead of anchor labels | point ops, focal loss, sometimes DCN | non-square point count, bad kernel size, target encoding mismatch | Backed |
| SEPC | `config/sepc/*.py`, `models/sepc/*` | SEPC refinement stacked on NASFPN-style features | RetinaNet-style outputs on five levels | deformable pconv / lcconv, IBN-like settings | pad sizes not divisible by stride, stride list mismatch, BN mode mismatch | Backed |
| TSD | `config/TSD/*.py`, `models/TSD/*` | Task-aware spatial disentanglement with auxiliary RoI branches | uses extra delta-C / delta-R pools and progressive constraints | `shape_tool`, custom RoI pooling code | missing `shape_tool`, class-agnostic bbox setting, shape inference bugs | Backed; external helper not runtime-verified here |
| CrowdHuman / DoublePred | `config/crowdhuman/*.py`, `models/crowdhuman/*` | Ignore-region aware Faster R-CNN and DoublePred refine variant | uses ignore labels, optional second prediction head, optional refine mode | `bbox_target`, `doublebbox_target`, `softmax_entropy` | wrong ignore label, `xywh` vs corner encoding, refine-mode tensor mismatch | Backed |

## Practical reading order

1. Pick the closest family row.
2. Open the listed config and builder files together.
3. Check whether the family is anchor-based, anchor-free, or multi-stage.
4. Verify whether the family changes the input schema, output layout, or custom
   operators.
5. Only then edit the config or builder.

## Notes on confidence

- The core architecture contracts above are directly evidenced in source.
- Backend-specific success for custom operators is not claimed unless the family
  README and builder both indicate it.
- If a row mentions an unverified backend helper, treat it as a code path to
  inspect, not a proven execution guarantee.
