---
name: visualization-and-submission
description: "Guide NAVSIM camera, BEV, and LiDAR visualization plus safe
  two-stage submission pickle preparation and local validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visualization and submission

Use this route for NAVSIM scene plots, sensor overlays, GIFs, or a locally
validated warmup/challenge `submission.pkl`.

## Read this when

- the task mentions `plot_bev_frame`, camera grids, annotations, LiDAR
  overlays, custom plots, or GIF rendering
- a user needs the submission pickle schema or metadata checks
- the workflow is `warmup_two_stage` or the authorized private
  `private_test_hard_two_stage` challenge path

## Start here

1. Read [visualization.md](references/visualization.md) for scene loading,
   plotting entry points, sensor prerequisites, and custom overlays.
2. Read [submission.md](references/submission.md) before creating a pickle;
   it defines the stage containers, required metadata, parity rules, and the
   private-data boundary.
3. Read [troubleshooting.md](references/troubleshooting.md) for dependency,
   path, Hydra, plotting, and submission failures.
4. Run the bundled [submission metadata validator](scripts/validate_submission_metadata.py)
   on a trusted local pickle: `python scripts/validate_submission_metadata.py
   --help`, then `python scripts/validate_submission_metadata.py
   path/to/submission.pkl`.

## Operating rules

- Visualization needs a loaded `Scene`, sensor blobs, calibration, and a map
  API for map layers; API/help checks do not need local data.
- Submission evaluation receives only `AgentInput`. The selected agent must
  have `requires_scene=False`; a privileged agent that needs `Scene` or
  annotations must stop before generation.
- Validate locally, but do not download data, train, run a benchmark, or upload
  a Hugging Face model as part of this route. Stop and ask for explicit
  authorization before any external/private operation.
- Use the same split and metric-cache path for warmup local evaluation and
  compare parity only after the local inputs are present. A valid pickle does
  not prove server acceptance or score parity.

## Ownership boundaries

This route owns plotting and pickle preparation/validation. Route installation,
data layout, sensor contracts, agent implementation, and EPDMS scoring to the
corresponding NAVSIM skills; use the links in the references when composing a
larger workflow.
