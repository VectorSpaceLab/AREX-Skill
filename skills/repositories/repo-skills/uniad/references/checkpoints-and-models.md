# UniAD checkpoints, models, and task ownership

## Released model families

UniAD's README describes two main training stages plus the BEVFormer backbone:

| Stage | Config | Checkpoint used/produced | Covered tasks |
|---|---|---|---|
| BEVFormer backbone | `projects/configs/bevformer/base_bevformer.py` | initializes from `ckpts/r101_dcn_fcos3d_pretrain.pth`, produces BEVFormer weights | camera BEV encoder |
| Stage 1 perception | `projects/configs/stage1_track_map/base_track_map.py` | initializes from `ckpts/bevformer_r101_dcn_24ep.pth`, public checkpoint `ckpts/uniad_base_track_map.pth` | tracking + map |
| Stage 2 E2E | `projects/configs/stage2_e2e/base_e2e.py` | initializes from `ckpts/uniad_base_track_map.pth`, public checkpoint `ckpts/uniad_base_e2e.pth` | tracking, map, motion, occupancy, planning |

## Public checkpoint names

- `r101_dcn_fcos3d_pretrain.pth`
- `bevformer_r101_dcn_24ep.pth`
- `uniad_base_track_map.pth`
- `uniad_base_e2e.pth`

The README points to the OpenDriveLab UniAD 2.0 HuggingFace model repository for these files. Do not bundle or copy checkpoints into this skill.

## Which sub-skill owns what

- Use `data-preparation` before any checkpointed run to make sure annotation PKLs and motion anchors are present.
- Use `config-and-model-architecture` to understand model heads, config fields, or task outputs.
- Use `training-evaluation` to build checkpointed train/eval commands.
- Use `visualization-and-results` after evaluation has produced a result pickle.

## Expected stage-1 evaluation signal

For the stage-1 public checkpoint and documented 8-GPU evaluation setup, the README/docs show:

```text
Aggregated results:
AMOTA 0.394
AMOTP 1.316
RECALL 0.484
```

Treat this as a target for matched environments, not a universal assertion for all GPU counts or modified configs.
