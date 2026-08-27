# Troubleshooting

Provenance: distilled from the UniAD visualizer, the E2E forward-test outputs, and the test-time result collector.

## Missing or invalid `results.pkl`
Symptoms:
- file not found
- pickle load failure
- top-level object has no `bbox_results`

Likely cause:
- the path points to a checkpoint, log, or unrelated pickle instead of a UniAD test result artifact

What to do:
- inspect the artifact with `scripts/inspect_results_pickle.py`
- confirm the top-level object is a dictionary with `bbox_results`
- if the pickle was never produced, route back to training/evaluation

## Missing task keys
Symptoms:
- `KeyError` for `traj`, `traj_scores`, `planning_traj`, `command`, `pts_bbox`, `lane_score`, or `occ`

Likely cause:
- the model config does not enable that head
- the result came from an earlier stage that does not produce that task
- the collector stripped heavy plot-only data before dump because `ENABLE_PLOT_MODE` was not set

What to do:
- compare the keys against the expected stage
- do not treat missing planning or occupancy fields as an error for a stage-1 artifact
- if you need those fields for plotting, make sure the upstream run preserved the plot tensors

## `project_to_cam` confusion
The stock runner treats `--project_to_cam` as a raw argparse value and then checks it in a truthy `if` statement.

That means any non-empty string is effectively true.

What to do:
- assume camera projection is on unless the runner has been patched or wrapped
- do not rely on `False` as a guaranteed disable in the stock script
- if BEV-only output is required, use a wrapper that sets the flag inside Python or edit the launcher

## Output folder or video problems
Symptoms:
- no JPG frames
- empty AVI
- `cv2.VideoWriter` fails
- files are written but the video is unreadable

Likely cause:
- output directory permissions
- stale JPGs in the folder
- a missing codec for the `DIVX` writer
- headless OpenCV or an incomplete multimedia stack

What to do:
- start from an empty writable output directory
- use a codec-capable OpenCV build
- if running headless, set `MPLBACKEND=Agg` when the environment needs it
- if AVI creation still fails, use a local wrapper with a different fourcc

## Camera projection dependencies
Symptoms:
- BEV renders but camera panels fail
- image loading or projection errors
- missing calibration data

Likely cause:
- the nuScenes image data, camera intrinsics, or ego pose metadata are unavailable

What to do:
- confirm the dataset root contains the camera images and sensor metadata used by the renderer
- keep in mind that camera projection depends on dataset assets, not just the pickle

## Large pickle memory use
Symptoms:
- slow load
- memory pressure
- process killed during inspection

Likely cause:
- the pickle contains many tensors and per-sample prediction dictionaries

What to do:
- inspect the file with `scripts/inspect_results_pickle.py` first
- summarize only a few samples at a time
- prefer a plot-stripped artifact when you only need a quick visual pass

## Log analysis as a secondary check
If the result pickle is structurally valid but the rendered output still looks wrong, use the run logs, metrics, and the bundled JSON log analyzer to confirm the upstream evaluation used the expected heads and plot-retention mode.

Log analysis is secondary to the result-key summary and should not replace it.
