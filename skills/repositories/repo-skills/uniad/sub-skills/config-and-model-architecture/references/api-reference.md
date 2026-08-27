# UniAD API reference

All signatures below were verified against the public UniAD code in the inspection environment.

## Constructor signatures

| Symbol | Verified signature |
| --- | --- |
| `BEVFormerHead` | `(*args, with_box_refine=False, as_two_stage=False, transformer=None, bbox_coder=None, num_cls_fcs=2, code_weights=None, bev_h=30, bev_w=30, **kwargs)` |
| `UniADTrack` | `(use_grid_mask=False, img_backbone=None, img_neck=None, pts_bbox_head=None, train_cfg=None, test_cfg=None, pretrained=None, video_test_mode=False, loss_cfg=None, qim_args={'qim_type': 'QIMBase', 'merger_dropout': 0, 'update_query_pos': False, 'fp_ratio': 0.3, 'random_drop': 0.1}, mem_args={'memory_bank_type': 'MemoryBank', 'memory_bank_score_thresh': 0.0, 'memory_bank_len': 4}, bbox_coder={'type': 'DETRTrack3DCoder', 'post_center_range': [-61.2, -61.2, -10.0, 61.2, 61.2, 10.0], 'pc_range': [-51.2, -51.2, -5.0, 51.2, 51.2, 3.0], 'max_num': 300, 'num_classes': 10, 'score_threshold': 0.0, 'with_nms': False, 'iou_thres': 0.3}, pc_range=None, embed_dims=256, num_query=900, num_classes=10, vehicle_id_list=None, score_thresh=0.2, filter_score_thresh=0.1, miss_tolerance=5, gt_iou_threshold=0.0, freeze_img_backbone=False, freeze_img_neck=False, freeze_bn=False, freeze_bev_encoder=False, queue_length=3)` |
| `UniAD` | `(seg_head=None, motion_head=None, occ_head=None, planning_head=None, task_loss_weight={'track': 1.0, 'map': 1.0, 'motion': 1.0, 'occ': 1.0, 'planning': 1.0}, **kwargs)` |
| `BEVFormerTrackHead` | `(*args, with_box_refine=False, as_two_stage=False, transformer=None, bbox_coder=None, num_cls_fcs=2, code_weights=None, bev_h=30, bev_w=30, past_steps=4, fut_steps=4, **kwargs)` |
| `PansegformerHead` | `(*args, bev_h, bev_w, canvas_size, pc_range, with_box_refine=False, as_two_stage=False, transformer=None, quality_threshold_things=0.25, quality_threshold_stuff=0.25, overlap_threshold_things=0.4, overlap_threshold_stuff=0.2, thing_transformer_head={'type': 'TransformerHead', 'd_model': 256, 'nhead': 8, 'num_decoder_layers': 6}, stuff_transformer_head={'type': 'TransformerHead', 'd_model': 256, 'nhead': 8, 'num_decoder_layers': 6}, loss_mask={'type': 'DiceLoss', 'weight': 2.0}, train_cfg={'assigner': {'type': 'HungarianAssigner', 'cls_cost': {'type': 'ClassificationCost', 'weight': 1.0}, 'reg_cost': {'type': 'BBoxL1Cost', 'weight': 5.0}, 'iou_cost': {'type': 'IoUCost', 'iou_mode': 'giou', 'weight': 2.0}}, 'sampler': {'type': 'PseudoSampler'}}, **kwargs)` |
| `MotionHead` | `(*args, predict_steps=12, transformerlayers=None, bbox_coder=None, num_cls_fcs=2, bev_h=30, bev_w=30, embed_dims=256, num_anchor=6, det_layer_num=6, group_id_list=[], pc_range=None, use_nonlinear_optimizer=False, anchor_info_path=None, loss_traj={}, num_classes=0, vehicle_id_list=[0, 1, 2, 3, 4, 6, 7], **kwargs)` |
| `OccHead` | `(receptive_field=3, n_future=4, spatial_extent=(50, 50), ignore_index=255, grid_conf=None, bev_size=(200, 200), bev_emb_dim=256, bev_proj_dim=64, bev_proj_nlayers=1, query_dim=256, query_mlp_layers=3, detach_query_pos=True, temporal_mlp_layer=2, transformer_decoder=None, attn_mask_thresh=0.5, sample_ignore_mode='all_valid', aux_loss_weight=1.0, loss_mask=None, loss_dice=None, init_cfg=None, pan_eval=False, test_seg_thresh: float = 0.5, test_with_track_score=False)` |
| `PlanningHeadSingleMode` | `(bev_h=200, bev_w=200, embed_dims=256, planning_steps=6, loss_planning=None, loss_collision=None, planning_eval=False, use_col_optim=False, col_optim_args={'occ_filter_range': 5.0, 'sigma': 1.0, 'alpha_collision': 5.0}, with_adapter=False)` |

## Core call contracts

| Symbol | Verified call signature | What it means |
| --- | --- | --- |
| `UniAD.forward_train` | `(self, img=None, img_metas=None, gt_bboxes_3d=None, gt_labels_3d=None, gt_inds=None, l2g_t=None, l2g_r_mat=None, timestamp=None, gt_lane_labels=None, gt_lane_bboxes=None, gt_lane_masks=None, gt_fut_traj=None, gt_fut_traj_mask=None, gt_past_traj=None, gt_past_traj_mask=None, gt_sdc_bbox=None, gt_sdc_label=None, gt_sdc_fut_traj=None, gt_sdc_fut_traj_mask=None, gt_segmentation=None, gt_instance=None, gt_occ_img_is_valid=None, sdc_planning=None, sdc_planning_mask=None, command=None, gt_future_boxes=None, **kwargs)` | Full multi-task training entry point. |
| `UniAD.forward_test` | `(self, img=None, img_metas=None, l2g_t=None, l2g_r_mat=None, timestamp=None, gt_lane_labels=None, gt_lane_masks=None, rescale=False, sdc_planning=None, sdc_planning_mask=None, command=None, gt_segmentation=None, gt_instance=None, gt_occ_img_is_valid=None, **kwargs)` | Full multi-task inference entry point. |
| `UniADTrack.get_bevs` | `(self, imgs, img_metas, prev_img=None, prev_img_metas=None, prev_bev=None)` | Safe place to swap the BEV encoder as long as `bev_embed` / `bev_pos` stay compatible. |
| `UniADTrack.simple_test_track` | `(self, img=None, l2g_t=None, l2g_r_mat=None, img_metas=None, timestamp=None)` | Sequential tracking inference. |
| `UniADTrack._forward_single_frame_train` | `(self, img, img_metas, track_instances, prev_img, prev_img_metas, l2g_r1=None, l2g_t1=None, l2g_r2=None, l2g_t2=None, time_delta=None, all_query_embeddings=None, all_matched_indices=None, all_instances_pred_logits=None, all_instances_pred_boxes=None)` | Per-frame tracking training inside the temporal queue. |
| `BEVFormerTrackHead.get_bev_features` | `(self, mlvl_feats, img_metas, prev_bev=None)` | Returns the BEV feature tensor and positional tensor. |
| `BEVFormerTrackHead.get_detections` | `(self, bev_embed, object_query_embeds=None, ref_points=None, img_metas=None)` | Produces tracking outputs from BEV features. |
| `PansegformerHead.forward` | `(self, bev_embed)` | Consumes BEV features and produces map outputs. |
| `MotionHead.forward_train` | `(self, bev_embed, gt_bboxes_3d, gt_labels_3d, gt_fut_traj=None, gt_fut_traj_mask=None, gt_sdc_fut_traj=None, gt_sdc_fut_traj_mask=None, outs_track={}, outs_seg={})` | Motion training uses track and map outputs plus motion anchors. |
| `MotionHead.forward_test` | `(self, bev_embed, outs_track={}, outs_seg={})` | Motion inference uses the same track/map context. |
| `OccHead.forward_train` | `(self, bev_feat, outs_dict, gt_inds_list=None, gt_segmentation=None, gt_instance=None, gt_img_is_valid=None)` | Occupancy training entry point. |
| `OccHead.forward_test` | `(self, bev_feat, outs_dict, no_query=False, gt_segmentation=None, gt_instance=None, gt_img_is_valid=None)` | Occupancy inference entry point. |
| `PlanningHeadSingleMode.forward_train` | `(self, bev_embed, outs_motion={}, sdc_planning=None, sdc_planning_mask=None, command=None, gt_future_boxes=None)` | Planning training entry point. |
| `PlanningHeadSingleMode.forward_test` | `(self, bev_embed, outs_motion={}, outs_occflow={}, command=None)` | Planning inference entry point. |
| `PlanningHeadSingleMode.forward` | `(self, bev_embed, occ_mask, bev_pos, sdc_traj_query, sdc_track_query, command)` | Lowest-level planning computation; this is where the BEV positional contract is enforced. |

## Practical readouts

- `UniADTrack.get_bevs(...)` is the key seam for alternative BEV encoders.
- `BEVFormerTrackHead.get_bev_features(...)` is the canonical source of `bev_embed` and `bev_pos`.
- `MotionHead` is anchor-aware and class-group aware.
- `PlanningHeadSingleMode` is the only public component that directly needs `bev_pos` in addition to `bev_embed`.
- `UniAD` is just the multi-head router and loss-weighting wrapper on top of the task heads.
