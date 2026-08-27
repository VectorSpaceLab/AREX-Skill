# UniAD model architecture

This reference describes how the public UniAD model pieces fit together and which component owns each task.

## High-level flow

```text
BEVFormer base
  image batch -> ResNet101 + FPN -> BEVFormerHead -> bev_embed / bev_pos

Stage 1 track + map
  image sequence -> UniADTrack -> BEVFormerTrackHead -> track outputs + bev_embed / bev_pos
                                       └-> PansegformerHead -> map outputs

Stage 2 end-to-end
  stage 1 backbone -> UniAD
    ├-> track path: UniADTrack + BEVFormerTrackHead
    ├-> map path: PansegformerHead
    ├-> motion path: MotionHead
    ├-> occupancy path: OccHead
    └-> planning path: PlanningHeadSingleMode
```

## Responsibility map

| Component | Main job | Consumes | Produces |
| --- | --- | --- | --- |
| `BEVFormerHead` | Base BEV encoder for the encoder-only config | image features | BEV feature tensor and BEV positional tensor |
| `UniADTrack` | Temporal track backbone and state manager | image sequence, metadata, previous BEV state | tracking outputs, `bev_embed`, `bev_pos`, cached temporal state |
| `BEVFormerTrackHead` | Stage 1 / 2 detection-tracking head | `bev_embed`, object queries, reference points | track logits, boxes, trajectory predictions |
| `PansegformerHead` | Map segmentation head | `bev_embed` | lane / map outputs and map losses |
| `MotionHead` | Future motion prediction | `bev_embed`, track outputs, seg outputs, motion anchors | motion trajectories, motion losses, motion query tensors |
| `OccHead` | Occupancy prediction | `bev_embed`, motion outputs | occupancy outputs and occupancy losses |
| `PlanningHeadSingleMode` | Final planning head | `bev_embed`, `bev_pos`, motion outputs, command | planned trajectory and planning losses |

## Stage 1 structure

Stage 1 trains the perception stack.

- `UniADTrack` owns image backbone / neck, temporal queueing, memory bank state, and the track loss.
- `BEVFormerTrackHead` consumes BEV features and returns tracking outputs plus the BEV tensors needed by downstream heads.
- `PansegformerHead` consumes the same BEV stream for map segmentation.
- The stage does not instantiate the motion, occupancy, or planning heads.

### Stage 1 loss ownership

| Task | Owner | Config location | Routed key prefix |
| --- | --- | --- | --- |
| Track | `UniADTrack.criterion` | `loss_cfg` under `model` | `track.*` |
| Map | `PansegformerHead` | `seg_head` | `map.*` |

## Stage 2 structure

Stage 2 wraps the stage 1 path and adds the remaining tasks.

- `UniAD` inherits from `UniADTrack` and adds `seg_head`, `motion_head`, `occ_head`, and `planning_head`.
- `MotionHead` consumes track and map outputs, along with motion anchors and class-grouping metadata.
- `OccHead` consumes BEV features and motion outputs.
- `PlanningHeadSingleMode` consumes BEV features, `bev_pos`, motion outputs, and the command stream.

### Stage 2 loss ownership

| Task | Owner | Important config fields | Routed key prefix |
| --- | --- | --- | --- |
| Track | `UniADTrack.criterion` | `loss_cfg` | `track.*` |
| Map | `PansegformerHead` | `loss_cls`, `loss_bbox`, `loss_iou`, `loss_mask`, assigners | `map.*` |
| Motion | `MotionHead` | `loss_traj`, `anchor_info_path`, `group_id_list`, `vehicle_id_list` | `motion.*` |
| Occupancy | `OccHead` | `loss_mask`, `loss_dice`, `pan_eval`, `grid_conf` | `occ.*` |
| Planning | `PlanningHeadSingleMode` | `loss_planning`, `loss_collision`, `use_col_optim`, `planning_eval` | `planning.*` |

`UniAD` applies `task_loss_weight` to those task groups and asserts that the keys are exactly `track`, `map`, `motion`, `occ`, and `planning`.

## BEV encoder swap contract

The public code explicitly allows replacing BEVFormer with another BEV encoder, but only if the replacement preserves the feature contract.

- Downstream track code expects a BEV feature tensor and a BEV positional tensor.
- `UniADTrack.get_bevs(...)` returns both `bev_embed` and `bev_pos`.
- `PlanningHeadSingleMode.forward(...)` also consumes both tensors and reshapes `bev_pos` internally.
- If the alternative encoder changes the shape or ordering, the downstream heads will fail or silently learn the wrong geometry.

In practice, the safe swap rule is: keep the semantic meaning of `bev_embed` and `bev_pos` unchanged and preserve their spatial shape.

## Temporal queue and memory

`queue_length` controls how many frames the model uses as temporal context.

- Base BEVFormer uses `4`.
- Stage 1 track/map uses `5`.
- Stage 2 end-to-end uses `3`.

A shorter queue saves memory but reduces temporal context. The stage 1 config comment explicitly notes that lowering the queue from `5` to `3` trades performance for lower memory use.

## Planning note

The planning path is not just another regression head.

- `PlanningHeadSingleMode` fuses SDC trajectory query, SDC track query, and navigation command.
- At test time it can optionally apply collision optimization.
- The reported planning metric depends on `planning_evaluation_strategy`, so the strategy choice is part of the architecture story, not just a logging detail.
