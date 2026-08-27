# Common Utilities

## Purpose

Read this when a task touches `scenic.common_lib` helpers that support multiple workflows: image/video utilities, debugging/profiling, export helpers, and miscellaneous shared functions.

## Utility families

| Area | Typical use | Notes |
|---|---|---|
| `common_utils` | Cross-host/process helpers, tree/array utilities, logging-friendly helpers. | Prefer these helpers over ad hoc logic when working inside Scenic training code. |
| `debug_utils` | Debug/profiling utilities and JAX-related diagnostics. | Some debug paths may depend on JAX experimental modules; treat import errors as version-compatibility signals. |
| `image_utils` | Image resize/crop/interpolation helpers used by data and project code. | Validate shape/channel assumptions with tiny arrays before using in a full pipeline. |
| `video_utils` | Video sampling/shape helpers used by video projects. | Route dataset loading and TFRecord layout issues to `data-pipelines`. |
| `export_utils` | Export/checkpoint-facing utilities. | Route model parameter shape or checkpoint mismatch questions to `modeling-and-layers` and project-specific export questions to `baselines-and-projects`. |

## Safe validation

Use the root `scripts/run_scenic_smoke.py` first for package-level checks. For utility-specific behavior, prefer small synthetic arrays and avoid invoking dataset builders or full project trainers.

## Routing

- Image/video transformations used before model training: start in `data-pipelines`, then use this reference for helper names and shape cautions.
- JAX/Flax model shapes or layer behavior: use `modeling-and-layers`.
- Debugging a train launch or backend issue: use `running-and-training` plus root troubleshooting.
