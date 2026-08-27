---
name: live-demo-and-visualization
description: "Run demo_superglue live matching, headless sequence processing,
  keyboard controls, and visualization troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Live Demo and Visualization

Use this sub-skill for `demo_superglue.py`-style live matching when the goal is to watch matches update against an anchor frame, write output images, or run safely on a remote server without a GUI.

## Route elsewhere

- Batch image-pair matching, `.npz` dumps, pose evaluation, or pair-file validation: [`../pair-matching-evaluation/`](../pair-matching-evaluation/)
- Direct Python API work with `models.Matching`, `SuperPoint`, `SuperGlue`, or tensor-level inference: [`../programmatic-api/`](../programmatic-api/)

## Use the bundled references

- [CLI reference](references/cli-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helper

- [`scripts/run_headless_demo_smoke.py`](scripts/run_headless_demo_smoke.py): bounded directory-mode smoke helper that always uses `--no_display` and forces CPU when requested.

## Operating notes

- `demo_superglue.py` uses `VideoStreamer` to normalize webcam, IP/RTSP, video-file, and directory inputs.
- The first frame becomes the initial anchor; press `n` to replace it with the current frame.
- `make_matching_plot_fast` renders confidence-colored lines and optional keypoints; `k` toggles keypoints in the interactive viewer.
- Prefer `--no_display` plus `--output_dir` for remote or headless runs.
- When few or no matches appear, first check resize, model choice, thresholds, and the selected anchor frame.
- Keep this sub-skill focused on visualization and interactive demo flows; do not use it for pair evaluation or Python API guidance.