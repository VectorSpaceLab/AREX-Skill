# UniAD troubleshooting

This page collects the most common config and model-architecture failures for the UniAD sub-skill.

## Fast triage order

1. Check the plugin fields: `plugin = True` and `plugin_dir = 'projects/mmdet3d_plugin/'`.
2. Check the stage checkpoint in `load_from`.
3. Check the temporal setting in `queue_length`.
4. Check the motion anchor path if the motion head is involved.
5. Check the planning strategy if the issue is about planning numbers.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Custom detectors or heads are not found in the registry | The plugin package was not enabled or the repo root was not on the import path | Keep `plugin=True`, keep `plugin_dir='projects/mmdet3d_plugin/'`, and make sure the `projects.mmdet3d_plugin` package is the import root used by the config |
| `ImportError`, `ModuleNotFoundError`, or registry build failures after a package upgrade | The OpenMMLab stack does not match the UniAD-compatible versions | Realign the environment to a compatible `torch` / `mmcv-full` / `mmdet` / `mmsegmentation` / `mmdet3d` set before blaming the model code |
| `FileNotFoundError` or `pickle` errors inside motion prediction | `MotionHead` could not open the anchor bundle | Set `motion_head.anchor_info_path` to a valid anchor file, usually `data/others/motion_anchor_infos_mode6.pkl` |
| Stage 1 runs out of memory or becomes too slow | The temporal queue is too long for the available GPU memory | Lower `queue_length` from `5` to `3` for stage 1; expect a small tracking-performance drop |
| A swapped BEV encoder crashes on missing `bev_embed` or `bev_pos` | The alternative encoder did not preserve UniAD's BEV contract | Return both tensors with the same spatial meaning and shape expected by `UniADTrack` and `PlanningHeadSingleMode` |
| Planning metrics look inconsistent with another paper or another UniAD run | The planning evaluation strategy does not match | Set `planning_evaluation_strategy` explicitly and compare only runs that use the same strategy |

## Notes by failure class

### Plugin / registry problems

The UniAD configs are not plain OpenMMLab configs that work without the plugin package. The custom detectors, heads, losses, and hooks are registered by `projects.mmdet3d_plugin`. If that package is not imported, the registry cannot build `UniAD`, `UniADTrack`, `BEVFormerTrackHead`, `PansegformerHead`, `MotionHead`, `OccHead`, or `PlanningHeadSingleMode`.

### Wrong stack problems

If the environment uses incompatible OpenMMLab wheels, the failure may appear as an import error, a missing CUDA op, or a registry build error. When that happens, treat the package stack as the first suspect, not the config syntax.

### Motion anchor problems

The motion module loads its anchor bundle from `anchor_info_path` during initialization. If the path is missing or points at a wrong file, the failure appears early and clearly. The fix is to provide a valid file path, not to edit the motion head internals.

### Memory tradeoff problems

Stage 1 uses a longer temporal queue than stage 2. That is useful for perception quality, but it costs memory. The config comment explicitly allows reducing the queue length for a cheaper run.

### BEV encoder swap problems

The public code allows swapping the BEV encoder, but only if the replacement preserves the expected BEV feature contract. In practice that means the downstream heads still get a compatible `bev_embed`, and the planning path still receives `bev_pos`.

### Planning metric confusion

The planning metrics are easy to misread because the config comments distinguish two evaluation interpretations:

- `uniad` = point-in-time horizon metric.
- `stp3` = average-up-to-horizon metric.

If you do not state the strategy, the number is ambiguous.

## When to escalate to another sub-skill

- If the question is about training or evaluation commands, route it to `training-evaluation`.
- If the question is about dataset layout or motion-anchor placement, route it to `data-preparation`.
- If the question is about visual outputs, route it to `visualization-and-results`.
