# Result pickle format

Provenance: distilled from `tools/test.py`, the plotting-preserving result collector, and the UniAD E2E forward-test path.

## Top-level shape
A UniAD visualization pickle is normally a dictionary with these top-level keys:

- `bbox_results`: list of per-sample prediction dictionaries
- `occ_results_computed`: optional aggregated occupancy metrics
- `planning_results_computed`: optional aggregated planning metrics
- `mask_results`: optional mask payload

The visualizer only reads `bbox_results`.

## Per-sample dictionary
Each entry in `bbox_results` is typically the merged output for one sample token.

Common keys from the tracking path:
- `token`
- `boxes_3d`
- `scores_3d`
- `labels_3d`
- `track_scores`
- `bbox_index`
- `track_ids`
- `mask`
- `track_bbox_results`

Motion-related keys:
- `traj`
- `traj_scores`
- `traj_0`, `traj_scores_0`, and similar decoder-layer suffixes when present
- `sdc_boxes_3d`
- `sdc_scores_3d`
- `sdc_track_scores`
- `sdc_track_bbox_results`
- `planning_traj`
- `planning_traj_gt`
- `command`

Map / segmentation keys:
- `pts_bbox`

The nested `pts_bbox` dictionary usually contains:
- `bbox`
- `segm`
- `labels`
- `panoptic`
- `drivable`
- `score_list`
- `lane`
- `lane_score`
- `stuff_score_list`

Occupancy-related keys:
- `occ` when the collector retained it
- `seg_gt`, `ins_seg_gt`, `seg_out`, `ins_seg_out` inside the occupancy dict when plot data is preserved

## What the visualizer actively uses
The current renderer primarily consumes:
- `token`
- `boxes_3d`, `scores_3d`, `labels_3d`
- `traj`, `traj_scores`
- `pts_bbox.lane_score`, `pts_bbox.score_list`, `pts_bbox.lane`, `pts_bbox.drivable`
- `planning_traj` and `command` when planning is enabled

## Collector behavior to remember
`tools/test.py` writes the result pickle from the multi-GPU collector.

By default, the collector removes the heavy `occ` and `planning` dictionaries before saving, which keeps the pickle smaller.

If `ENABLE_PLOT_MODE` is set, extra tensors stay in the pickle for richer local inspection, at the cost of a much larger file.

## Practical reading rule
Do not assume every pickle has every task key.
A stage-1 result can be a valid UniAD output even if it has no planning fields, and a plain test-time pickle can be valid even when the heavy occupancy payload is absent.
