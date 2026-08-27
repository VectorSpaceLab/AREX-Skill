# AgiBotWorld workflows

This reference is a self-contained operational summary of the AgiBot route. It
intentionally does not copy the source converter or invoke it. Substitute the
actual installed conversion entrypoint in the command shape below; do not run
it during planning or a structural-only review.

## Inputs and output policy

The input is the root of one AgiBotWorld release. A valid root normally has:

```text
<release>/
  task_info/task_*.json
  observations/<numeric-task-id>/<episode-id>/videos/*.mp4
  observations/<numeric-task-id>/<episode-id>/depth/head_depth*
  observations/<numeric-task-id>/<episode-id>/tactile/*.mp4
  proprio_stats/<numeric-task-id>/<episode-id>/proprio_stats.h5
```

`task_info/task_N.json` is the scheduling authority. Its records are sorted by
`episode_id`; the task instruction is built from the first record's
`task_name` and `init_scene_text`, joined as `task_name | init_scene_text`.
The numeric task directory is derived from the final underscore-separated token
of the JSON filename (`task_327.json` maps to observations/327). Validate this
mapping before scheduling rather than relying on a broad glob.

`--output-path` is the final aggregated LeRobot root. The shared conversion
lifecycle may create a sibling temporary root whose name ends in `_temp`; keep
it on the same filesystem when possible and do not pre-create it with unrelated
contents. A custom dataset creation path removes the task-local root before
replacing its metadata object, so task-local paths must be disposable and must
never point at the raw release or a valuable existing dataset.

## CLI contract

Pass these options to the AgiBot conversion entrypoint:

| Option | Default / choices | Operational meaning |
|---|---|---|
| `--src-path` | required path | AgiBotWorld release root; must contain all three top-level areas |
| `--output-path` | required path | final aggregated LeRobot root |
| `--eef-type` | `gripper` | Selects the feature schema and task family: `gripper`, `dexhand`, or `tactile` |
| `--task-ids` | empty list | One or more task names such as `task_327`; empty means all tasks in the selected family |
| `--executor` | `ray` | `local` avoids a Ray cluster; `ray` uses the shared distributed executor |
| `--cpus-per-task` | `1` | CPU allocation requested per conversion task; plan about 3 for video-heavy work |
| `--tasks-per-job` | `1` | Concurrent tasks inside a Ray job; ignored by the local executor |
| `--episodes-per-task` | `10` | Number of raw episodes grouped in one scheduled task; `1` isolates failures and improves balancing |
| `--workers` | `-1` | Number of concurrent jobs; use an explicit conservative value when memory is bounded |
| `--resume-dir` | unset | Existing shared-pipeline log directory for a deliberate resume; inspect it first |
| `--save-depth` | off | Adds `observation.images.head_depth` and reads depth images; requires a complete aligned depth stream |
| `--debug` | off | Requests the shared pipeline's debug behavior; combine with local execution for a first smoke |
| `--repo-id` | unset | Local repository identifier and, when pushing, Hub destination identifier |
| `--push-to-hub` | off | Uploads the completed result; require explicit approval and a validated repo ID |

A conservative first-run command shape is:

```text
<installed-agibot-entrypoint> \
  --src-path <release-root> \
  --output-path <new-output-root> \
  --eef-type gripper \
  --task-ids task_327 \
  --executor local \
  --cpus-per-task 1 \
  --episodes-per-task 1 \
  --workers 1 \
  --debug
```

The default `ray` executor and `workers=-1` are throughput-oriented defaults,
not evidence that a Ray cluster or unlimited memory is available. `--repo-id`
is documented as required for a Hub push; enforce that requirement during
preflight even if an older parser accepts the flag combination.

## Selection and chunking

The built-in mapping reserves these task IDs for dexhand:
`task_475`, `task_536`, `task_547`, `task_548`, `task_549`, `task_554`,
`task_577`, `task_578`, `task_591`, `task_595`, `task_608`, `task_620`,
`task_622`, `task_660`, `task_679`, `task_705`, `task_710`, `task_727`,
`task_730`, `task_731`, `task_749`, and `task_753`.

The tactile mapping reserves `task_666`, `task_675`, `task_676`, `task_677`,
`task_694`, `task_737`, and `task_774`. The gripper route excludes both
reserved sets and treats the remaining tasks as gripper tasks. An explicit
`--task-ids` list is intersected with the selected family; an ID from another
family produces no task rather than a schema conversion. Keep each family in a
separate output unless an intentional downstream merge has compatible feature
schemas.

Episodes are sorted and grouped in contiguous chunks of
`--episodes-per-task`. A single episode is named with its episode ID; a chunk
name includes a zero-padded chunk index and the first/last episode IDs. These
names are temporary repository IDs, not frame-level task labels. The final
frame task label remains the instruction from task metadata.

## Execution and resource plan

1. Run a read-only preflight for JSON/HDF5 keys, required video existence,
   depth counts, and task-family membership.
2. Convert one or a few episodes locally with `--episodes-per-task 1` and a
   new output root. Do not use Hub publication in this pass.
3. Inspect the generated feature schema and video/depth metadata. Only then
   increase grouping, workers, or executor scope.
4. For Ray, make the release and output paths visible to every worker, install
   the Ray extra, and verify cluster ownership. A manually started cluster may
   be multi-node; never launch or attach to one without an explicit operator
   decision.
5. Keep task groups small enough for memory. Repository guidance estimates
   roughly 20 GiB per task and recommends about 3 CPU cores per task for good
   throughput; video decoding, Parquet writes, and depth arrays can make the
   estimate conservative. Reduce workers or use one episode per task when RAM
   is tight.
6. Use `--resume-dir` only after checking that its logs belong to the same
   source snapshot, flags, and output root. A resume is not a schema migration.
7. Aggregate and clean temporary task outputs through the shared generic route;
   preserve logs and any skipped-episode report before deleting disposable
   temporary data.

## Depth and video workflow

Without `--save-depth`, the head-depth feature is removed from the selected
schema and only configured RGB/tactile videos are required. With
`--save-depth`, the converter loads all files beginning with `head_depth` from
the episode depth directory, converts integer millimetres to float metres, and
requires exactly one depth frame per state frame. Missing or extra depth frames
are a data-integrity error; preflight should exclude or repair that episode
explicitly rather than pad it.

For configured RGB cameras, expected paths use
`observations/<task-id>/<episode>/videos/<camera>_color.mp4`. For tactile
sensor keys, the path is instead
`observations/<task-id>/<episode>/tactile/<sensor-key>.mp4`. Missing files are
rejected before HDF5 loading. A file that exists but cannot be encoded or read
is reported during episode save and that episode is discarded; preserve the
error and verify that no partial episode remains in the task-local dataset.

## Post-run acceptance

Before a Hub push, check that the final metadata reports the intended FPS (30),
robot type (`a2d`), end-effector schema, camera/depth modalities, task labels,
state/action widths, per-episode action configuration, and expected episode
count after skips. Open representative video streams and inspect depth units.
A successful process exit alone is not sufficient when corrupt episodes were
skipped.
