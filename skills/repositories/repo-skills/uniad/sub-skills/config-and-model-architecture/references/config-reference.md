# UniAD config reference

This reference summarizes the three public UniAD config families used by the generated skill. It focuses on the config fields that matter for model selection, plugin loading, queue length, checkpoints, and task ownership.

## Common plugin contract

All public UniAD configs rely on the repo-local plugin package.

- `plugin = True`
- `plugin_dir = 'projects/mmdet3d_plugin/'`
- Public import root: `projects.mmdet3d_plugin`

If these fields are missing, the custom detector and head registries will not resolve the UniAD modules.

## Quick matrix

| Config file | Role | `model.type` | Dataset type | `queue_length` | `load_from` | Active heads |
| --- | --- | --- | --- | --- | --- | --- |
| `bevformer/base_bevformer.py` | BEVFormer base encoder | `BEVFormer` | `CustomNuScenesDataset` | `4` | `ckpts/r101_dcn_fcos3d_pretrain.pth` | `BEVFormerHead` |
| `stage1_track_map/base_track_map.py` | Stage 1 perception warm start | `UniAD` | `NuScenesE2EDataset` | `5` | `ckpts/bevformer_r101_dcn_24ep.pth` | `BEVFormerTrackHead`, `PansegformerHead` |
| `stage2_e2e/base_e2e.py` | Stage 2 end-to-end training | `UniAD` | `NuScenesE2EDataset` | `3` | `ckpts/uniad_base_track_map.pth` | `BEVFormerTrackHead`, `PansegformerHead`, `MotionHead`, `OccHead`, `PlanningHeadSingleMode` |

## Base BEVFormer config

Use the BEVFormer base when you want to reason about the BEV encoder before UniAD task heads are added.

- `model.type = 'BEVFormer'`
- `pts_bbox_head.type = 'BEVFormerHead'`
- `queue_length = 4`
- `load_from = 'ckpts/r101_dcn_fcos3d_pretrain.pth'`
- `dataset_type = 'CustomNuScenesDataset'`
- `data_root = 'data/nuscenes/'`
- `info_root = 'data/infos/'`

This config is the cleanest entry point for the encoder-only path.

## Stage 1 track/map config

Use stage 1 when you want the perception stack that initializes stage 2.

- `model.type = 'UniAD'`
- `pts_bbox_head.type = 'BEVFormerTrackHead'`
- `seg_head.type = 'PansegformerHead'`
- `queue_length = 5`
- `load_from = 'ckpts/bevformer_r101_dcn_24ep.pth'`
- `freeze_img_backbone = True`
- `freeze_img_neck = False`
- `freeze_bn = False`
- `planning_evaluation_strategy = 'uniad'`

The config comment notes that `queue_length` can be reduced from `5` to `3` to save memory, with a small performance drop.

## Stage 2 end-to-end config

Use stage 2 when you want the full track + map + motion + occupancy + planning model.

- `model.type = 'UniAD'`
- `pts_bbox_head.type = 'BEVFormerTrackHead'`
- `seg_head.type = 'PansegformerHead'`
- `motion_head.type = 'MotionHead'`
- `occ_head.type = 'OccHead'`
- `planning_head.type = 'PlanningHeadSingleMode'`
- `queue_length = 3`
- `load_from = 'ckpts/uniad_base_track_map.pth'`
- `freeze_img_backbone = True`
- `freeze_img_neck = True`
- `freeze_bn = True`
- `freeze_bev_encoder = True`
- `motion_head.anchor_info_path = 'data/others/motion_anchor_infos_mode6.pkl'`
- `planning_evaluation_strategy = 'uniad'`

Stage 2 is the lightest temporal setting of the three public configs because the BEV encoder is frozen and the queue length is shorter.

## Shared fields worth checking first

- `queue_length` appears in both the model and the dataset config. Keep the values aligned.
- `load_from` points to the stage checkpoint that initializes the next stage.
- `data_root` and `info_root` point to the expected repo-local data layout.
- `planning_evaluation_strategy` must be stated when you report planning numbers.
- `task_loss_weight` is owned by `UniAD`; if the config does not override it, the class default gives each task weight `1.0`.

## Planning metric note

The config comments define two planning interpretations:

- `uniad`: a point-in-time metric at a chosen horizon.
- `stp3`: an average over the trajectory up to that horizon.

Do not compare planning scores across those strategies as if they were identical.

## Practical edit guide

- Reduce `queue_length` only when memory is the real blocker.
- Change `load_from` when moving between stage checkpoints.
- Keep `plugin` settings intact when you rely on repo-local heads or detectors.
- Update `motion_head.anchor_info_path` whenever the motion anchor bundle moves.
- If you replace the BEV encoder, keep the downstream `bev_embed` / `bev_pos` contract intact.

## Safe summary helper

Run `scripts/summarize_uniad_config.py <path-to-config>` to print a safe summary of the key config fields without executing the config file.
