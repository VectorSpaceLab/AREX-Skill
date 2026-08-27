---
name: visualization-and-analysis
description: "Route Det3D LiDAR, BEV, KITTI, prediction, training-log, FLOPs,
  and headless-visualization analysis tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Visualization and Analysis

Use this route for prediction/result rendering, BEV/LiDAR/KITTI visualization,
training-log summaries, learning curves, and model-complexity interpretation.
Use `scripts/summarize_log.py` for deterministic headless log summaries.

## Workflow

1. Identify artifact type: JSON log, pickle/result objects, KITTI text,
   point-cloud/boxes, image/calibration, or model/config.
2. Validate coordinate frames, box convention, classes, and score threshold
   before rendering.
3. Prefer saved images/text summaries on remote or headless hosts.
4. Read [visualization-workflows.md](references/visualization-workflows.md) for
   optional VTK/Open3D/Matplotlib paths and [log-analysis.md](references/log-analysis.md)
   for scalar aggregation.
5. Follow [troubleshooting.md](references/troubleshooting.md) for display,
   dependency, malformed-log, or empty-result failures.

FLOPs and parameter counts depend on the exact model/config/input shape and may
require the same compiled dependencies as model construction. A plot or summary
does not prove detector correctness; route metric/evaluator concerns to
`training-and-evaluation`.
