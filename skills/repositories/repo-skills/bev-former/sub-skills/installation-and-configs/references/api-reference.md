# API reference

Keep these signatures aligned with the config family you are editing.

## Detectors

- `BEVFormer.__init__(use_grid_mask=False, pts_voxel_layer=None, pts_voxel_encoder=None, pts_middle_encoder=None, pts_fusion_layer=None, img_backbone=None, pts_backbone=None, img_neck=None, pts_neck=None, pts_bbox_head=None, img_roi_head=None, img_rpn_head=None, train_cfg=None, test_cfg=None, pretrained=None, video_test_mode=False)`
  - Uses a queued camera tensor during training.
  - `video_test_mode` is the temporal inference switch for the BEVFormer family.

- `BEVFormerV2.__init__(use_grid_mask=False, pts_voxel_layer=None, pts_voxel_encoder=None, pts_middle_encoder=None, pts_fusion_layer=None, img_backbone=None, pts_backbone=None, img_neck=None, pts_neck=None, pts_bbox_head=None, fcos3d_bbox_head=None, img_roi_head=None, img_rpn_head=None, train_cfg=None, test_cfg=None, pretrained=None, video_test_mode=False, num_levels=None, num_mono_levels=None, mono_loss_weight=1.0, frames=(0,))`
  - Uses `frames` for temporal wiring.
  - Adds the optional mono/DD3D branch through `fcos3d_bbox_head`.
  - The current code asserts that `video_test_mode` stays off.

## Heads

- `BEVFormerHead.__init__(*args, with_box_refine=False, as_two_stage=False, transformer=None, bbox_coder=None, num_cls_fcs=2, code_weights=None, bev_h=30, bev_w=30, **kwargs)`
- `BEVFormerHead_GroupDETR.__init__(*args, group_detr=1, **kwargs)`
  - Multiplies `num_query` by the group factor.
  - Trims queries at eval time.
- `BEVFormerHead.forward(mlvl_feats, img_metas, prev_bev=None, only_bev=False)`
  - Builds BEV queries from `bev_h` and `bev_w`.
  - Returns BEV-only features when `only_bev=True`.

## Transformers

- `PerceptionTransformer.__init__(num_feature_levels=4, num_cams=6, two_stage_num_proposals=300, encoder=None, decoder=None, embed_dims=256, rotate_prev_bev=True, use_shift=True, use_can_bus=True, can_bus_norm=True, use_cams_embeds=True, rotate_center=[100, 100], **kwargs)`
- `PerceptionTransformer.get_bev_features(mlvl_feats, bev_queries, bev_h, bev_w, grid_length=[0.512, 0.512], bev_pos=None, prev_bev=None, **kwargs)`
- `PerceptionTransformer.forward(mlvl_feats, bev_queries, object_query_embed, bev_h, bev_w, grid_length=[0.512, 0.512], bev_pos=None, reg_branches=None, cls_branches=None, prev_bev=None, **kwargs)`
- `PerceptionTransformerBEVEncoder.__init__(num_feature_levels=4, num_cams=6, two_stage_num_proposals=300, encoder=None, embed_dims=256, use_cams_embeds=True, rotate_center=[100, 100], **kwargs)`
- `PerceptionTransformerV2.__init__(num_feature_levels=4, num_cams=6, two_stage_num_proposals=300, encoder=None, embed_dims=256, use_cams_embeds=True, rotate_center=[100, 100], frames=(0,), decoder=None, num_fusion=3, inter_channels=None, **kwargs)`
- `PerceptionTransformerV2.get_bev_features(mlvl_feats, bev_queries, bev_h, bev_w, grid_length=[0.512, 0.512], bev_pos=None, prev_bev=None, **kwargs)`
- `PerceptionTransformerV2.forward(mlvl_feats, bev_queries, object_query_embed, bev_h, bev_w, grid_length=[0.512, 0.512], bev_pos=None, reg_branches=None, cls_branches=None, prev_bev=None, **kwargs)`

## Encoder and attention

- `BEVFormerEncoder.__init__(*args, pc_range=None, num_points_in_pillar=4, return_intermediate=False, dataset_type='nuscenes', **kwargs)`
- `BEVFormerEncoder.forward(bev_query, key, value, *args, bev_h=None, bev_w=None, bev_pos=None, spatial_shapes=None, level_start_index=None, valid_ratios=None, prev_bev=None, shift=0.0, **kwargs)`
- `BEVFormerLayer.__init__(attn_cfgs, feedforward_channels, ffn_dropout=0.0, operation_order=None, act_cfg=dict(type='ReLU', inplace=True), norm_cfg=dict(type='LN'), ffn_num_fcs=2, **kwargs)`
- `TemporalSelfAttention.__init__(embed_dims=256, num_heads=8, num_levels=4, num_points=4, num_bev_queue=2, im2col_step=64, dropout=0.1, batch_first=True, norm_cfg=None, init_cfg=None)`
- `SpatialCrossAttention.__init__(embed_dims=256, num_cams=6, pc_range=None, dropout=0.1, init_cfg=None, batch_first=False, deformable_attention=dict(type='MSDeformableAttention3D', embed_dims=256, num_levels=4), **kwargs)`
- `MSDeformableAttention3D.__init__(embed_dims=256, num_heads=8, num_levels=4, num_points=8, im2col_step=64, dropout=0.1, batch_first=True, norm_cfg=None, init_cfg=None)`

## Dataset and bbox utilities

- `CustomNuScenesDataset.__init__(queue_length=4, bev_size=(200, 200), overlap_test=False, *args, **kwargs)`
- `CustomNuScenesDatasetV2.__init__(frames=(), mono_cfg=None, overlap_test=False, *args, **kwargs)`
- `NMSFreeCoder.__init__(pc_range, voxel_size=None, post_center_range=None, max_num=100, score_threshold=None, num_classes=10)`
- `HungarianAssigner3D.__init__(cls_cost=dict(type='ClassificationCost', weight=1.0), reg_cost=dict(type='BBoxL1Cost', weight=1.0), iou_cost=dict(type='IoUCost', weight=0.0), pc_range=None)`
- `HungarianAssigner3D.assign(bbox_pred, cls_pred, gt_bboxes, gt_labels, gt_bboxes_ignore=None, eps=1e-07)`

## Practical config mapping

- BEVFormer base, tiny, and small use `CustomNuScenesDataset`, `queue_length`, and `video_test_mode=True`.
- BEVFormerV2 uses `CustomNuScenesDatasetV2`, `frames`, `group_detr`, `mono_cfg`, and `video_test_mode=False`.
- Changing `bev_h_` or `bev_w_` means updating the head `bev_h` and `bev_w`, the positional encoding sizes, and the derived `voxel_size`.
- `NMSFreeCoder` expects `pc_range`; `HungarianAssigner3D` expects SciPy-backed Hungarian matching when you actually build or run the model.
