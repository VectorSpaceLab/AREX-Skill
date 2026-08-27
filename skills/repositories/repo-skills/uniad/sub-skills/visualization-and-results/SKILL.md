---
name: visualization-and-results
description: "Interpret UniAD result artifacts and build
  visualization/log-analysis commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# visualization-and-results

Use this sub-skill when the user already has a UniAD result artifact and needs to inspect it, render it, or build a visualization command.

## Do this first
- Inspect the pickle with `scripts/inspect_results_pickle.py` if the structure is unknown or keys look missing.
- Build the visualization command with `scripts/build_visualization_command.py`.
- Treat `tools/test.py --out` as the normal source of the visualization pickle.
- Treat `--show-dir` as a separate test-time image sink, not the visualizer input.

## Route away when needed
- Generating a fresh result pickle via evaluation -> `training-evaluation`
- Config or model edits, or missing task heads -> `config-and-model-architecture`
- Dataset layout, info PKLs, or motion-anchor problems -> `data-preparation`

## What this sub-skill understands
- `tools/test.py --out` result pickle behavior
- `tools/test.py --show-dir` as a separate review path
- visualization runner args: `predroot`, `out_folder`, `demo_video`, `project_to_cam`
- UniAD forward-test result keys for tracking, motion, map, planning, and occupancy
- log-analysis as a secondary check when the pickle structure is fine but the render looks wrong

## Expected outputs
- per-sample JPG frames in the output folder
- optional combined BEV/camera JPGs
- a final AVI video
- a compact pickle key summary for troubleshooting

## References
- `references/visualization.md`
- `references/results-format.md`
- `references/troubleshooting.md`

## Scripts
- `scripts/build_visualization_command.py`
- `scripts/inspect_results_pickle.py`
