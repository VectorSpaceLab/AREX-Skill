---
name: "version-migration"
description: "Plans safe LeRobot v1.6, v2.0, v2.1, and v3.0 dataset migrations
  with version-matched environments, metadata-layout checks, local or Hub
  staging, video handling, and rollback controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LeRobot version migration

Use this route when an existing LeRobot dataset must move between **v1.6 and
v2.0**, **v2.0 and v2.1**, or **v2.1 and v3.0**. It is a planning and
review route, not a runnable converter. The repository converters are
reference-only because they can rewrite local directories, delete metadata,
clone Git-LFS repositories, invoke `ffmpeg`, create tags, upload files, and
push to the Hugging Face Hub.

Do not use this route for converting raw HDF5, RLDS/TFDS, AgiBot, RoboMIND,
LIBERO, or RoboCasa data. Route those requests to the dataset-specific
sub-skill first, then return here only if the resulting LeRobot dataset needs a
version migration.

## Non-negotiable boundary

- Never run a migration against the only copy of a dataset. Use an immutable
  source snapshot and a separate destination or disposable test branch.
- Never infer the source version from a directory name or a tag alone. Read and
  cross-check `meta/info.json` (or the legacy `meta_data/info.json`) and inspect
  representative data, episode, task, stats, and video paths.
- A current LeRobot import is not proof that a historical converter is usable.
  Resolve the version-specific API imports and constants before touching data.
  The source evidence mixes `lerobot.common.datasets.*`,
  `lerobot.datasets.*`, and `lerobot.datasets.io_utils`; current LeRobot
  commonly exposes `LeRobotDataset` and `LeRobotDatasetMetadata` under
  `lerobot.datasets.lerobot_dataset`. Treat namespace mismatch as a stop gate.
- Keep `--push-to-hub`, deletion flags, tag creation, and any Git-LFS operation
  off until local validation passes and the operator explicitly approves
  publication.

## Route checklist

1. Record `source_version`, `target_version`, `repo_id` if any, local root(s),
   desired branch, whether videos exist, and the rollback location. Use the
   exact direction matrix in [version-matrix](references/version-matrix.md).
2. Confirm the source metadata schema and episode/task indices. Run the
   read-only static or synthetic checks in [metadata layouts](references/metadata-layouts.md)
   before installing or invoking a converter.
3. Select a version-pinned environment. Do not mix the current package with
   historical imports. Record Python, LeRobot revision, `datasets`,
   `jsonlines`, `pyarrow`, `safetensors`, and `ffmpeg` versions.
4. Choose one source mode:
   - **Local:** `--root` is an exact dataset root for v2.0/v2.1/v3.0 routes.
     For v1.6→v2.0, `--local-dir` is staging/cache space; the evidence
     converter still identifies the Hub dataset with `--repo-id`.
   - **Hub:** use a pinned revision or tag and download into a new staging
     root. Treat every upload, delete, tag, or branch operation as a separate
     approval step.
5. For v1.6→v2.0 only, choose exactly one task source: `--single-task`,
   `--tasks-col`, or `--tasks-path`. Check episode coverage and task text
   before starting. See [workflows](references/workflows.md).
6. Make a backup, record a manifest and checksums, and create a non-production
   test branch if Hub validation is required. Never let an existing `_old`,
   `_v30`, or destination directory be silently reused.
7. Perform a no-write plan review: expected metadata files, data/video path
   templates, stats representation, episode counts, frame counts, and tag
   changes. Do not use a hidden wrapper; the source converters are not bundled
   in this skill.
8. Execute only after approval in the pinned environment, preferably to a new
   local root. Keep Hub push and cleanup disabled for the first pass.
9. Validate the output as a dataset of the target version, reopen it with the
   target LeRobot API, compare counts/tasks/stats, and inspect video durations
   and timestamps. Then review the rollback copy before any publication.
10. Publish to a test branch first. Only after a consumer successfully reads
    that branch should the operator rename, tag, delete, or replace a
    production revision.

## Direction-specific dispatch

- **v1.6 ↔ v2.0:** this bundle provides v1.6→v2.0 planning only. There is no
  reverse converter in the assigned evidence. Expect task annotation,
  per-episode parquet splitting, stats serialization, and possible Hub/LFS
  video moves.
- **v2.0 ↔ v2.1:** this is primarily a stats and `codebase_version` migration;
  data files remain in the v2 layout. v2.0→v2.1 computes per-episode stats and
  checks their aggregate; v2.1→v2.0 writes aggregate `stats.json`.
- **v2.1 ↔ v3.0:** this is a physical layout migration. v2.1→v3.0
  consolidates parquet/video files and metadata; v3.0→v2.1 splits them back
  into per-episode files and uses `ffmpeg` for video segments.

Read the detailed [workflows](references/workflows.md),
[metadata layouts](references/metadata-layouts.md), and
[troubleshooting](references/troubleshooting.md) before making a run plan.
