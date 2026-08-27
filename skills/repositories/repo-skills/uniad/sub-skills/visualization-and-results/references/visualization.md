# Visualization workflow

Provenance: distilled from the UniAD visualization notes, the test-time collector, the visualization launcher, the render utilities, and the E2E forward-test path.

## What the visualizer consumes
The bundled visualizer reads a UniAD result pickle and loads the `bbox_results` list from the top-level object. Each list item represents one sample.

The default launcher is configured for the nuScenes mini validation split and renders BEV plus camera views from those sample entries.

## Command flow
1. Load the pickle with `mmcv.load(predroot)`.
2. Read `bbox_results`.
3. Iterate validation samples.
4. Save one BEV image per sample.
5. Optionally render camera panels and combine them with the BEV image.
6. Assemble the generated JPG frames into an AVI video.

## Input arguments
- `predroot`: path to a UniAD result pickle.
- `out_folder`: directory for the rendered frames.
- `demo_video`: AVI filename written from the rendered JPG frames.
- `project_to_cam`: request camera projection and combined BEV/camera output.

## Default rendering layers
The stock renderer emphasizes planning and trajectory inspection:
- predicted track boxes
- predicted trajectories
- SDC box and planning trajectory
- command overlay
- legend

The stock launcher does not enable HD map or occupancy overlays by default.

## Output files
For each sample, the renderer writes numbered JPG files in the output folder. When camera projection is active, a temporary camera image is also created and then merged into the final per-sample JPG.

The final AVI is written from all JPGs found in the output folder, in sorted order.

## How `--show-dir` fits in
`tools/test.py` exposes `--show-dir` as a separate test-time output path. That is useful for quick image review, but the visualizer itself still consumes the pickle written by `--out`.

## Stage-aware usage
- Stage 1 track/map outputs may have tracking and map keys but not planning keys.
- Stage 2 E2E outputs should carry planning trajectory data when the planning head is active.
- Occupancy overlays are diagnostic and may be absent from the default dump.

## Secondary reference
If the pickle structure is valid but the rendered content is wrong, compare the run logs and metrics to confirm the upstream evaluation used the expected heads and plot-retention behavior. Log analysis is secondary to result-key inspection.
