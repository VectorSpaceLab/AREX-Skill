# Workflow Selection and Preflight

## Choose by source and direction

| If the request names... | Route | First question |
|---|---|---|
| `BaseAdapter`, `ConversionTask`, DataTrove, temp aggregation, Ray/local workers | `generic-conversion` | Is the source adapter's task manifest and feature schema known? |
| OpenX/OXE/RLDS/TFDS as input | `openx-conversion` | What exact TFDS builder name/version and OXE config are present? |
| AgiBotWorld, `task_info`, `proprio_stats`, `eef-type` | `agibot-conversion` | Which end-effector family and task IDs are in the raw release? |
| RoboMIND, benchmark release, embodiment, instruction CSV | `robomind-conversion` | Is the full benchmark/embodiment tree and annotation set available? |
| LIBERO `.hdf5`, agentview/eye-in-hand observations | `libero-conversion` | Are images already 256x256x3, or is external regeneration needed? |
| RoboCasa, `env_args`, masks, segmentation/depth/camera matrices | `robocasa-conversion` | Is this conversion-only, subset-first, or simulator rerendering? |
| RLDS/TFDS as output from a LeRobot root | `rlds-export` | Are feature shapes, task text, and episode boundaries complete? |
| LeRobot v1.6/v2.0/v2.1/v3.0, `info.json`, stats/layout changes | `version-migration` | Which exact source/target version and version-matched environment apply? |

If a request spans routes, plan them in order and preserve each handoff. For
example, an HDF5-to-LeRobot conversion may use `generic-conversion` for shared
execution, while a later v2.1→v3.0 rewrite uses `version-migration`. RLDS input
and RLDS output are opposite directions and must never share an assumed schema.

## Required no-write preflight

Before any converter or writer is invoked, record:

- source path, format/version, source ownership, and a read-only layout result;
- target LeRobot version and verified import/signature locations;
- output path, whether it exists, temporary paths, backup/rollback location;
- task/episode count, language/task policy, feature keys, shape/dtype/channel
  order, FPS, robot type, and optional modalities;
- executor (`local` first, Ray only after a resource/shared-path check), CPU and
  memory budget, resume-log identity, and cleanup policy;
- external requirements: TFDS builder, HDF5/Parquet/video tools, ffmpeg,
  Beam/Ray, simulator assets, Hub credentials, or network access;
- validation observations required before publication or downstream training.

Stop when a required row is unknown. A missing optional backend may remain
uninstalled only when its route marks it optional and the limitation is written
in the handoff.

## Route-independent validation

1. Work from a copy or a new output root; never assume a converter is
   idempotent. Check whether its implementation removes the destination.
2. Validate source keys and shape/rank before allocating output. For video,
   verify codec/ffmpeg availability and frame count; for images, verify HWC/CHW,
   channels, dtype, and depth units.
3. Compare source and output episode/task counts. Inspect `meta/info.json`,
   tasks, per-episode records/stats, and representative image/video frames.
4. Keep network, credentials, Hub pushes, Git-LFS, cluster launch, Beam, and
   simulator rerendering as separate approvals. A local pass is not a
   publication pass.

## Output handoff

Return the selected route, exact source/target versions, preflight evidence,
commands or API equivalent, outputs and counts, skipped/failed episodes with
reasons, optional backend gaps, and the next safe action. If the source
checkout is unavailable, this generated skill remains usable because the
workflow and schema details live in its route references.
