# Troubleshooting evaluation and logs

## Install and import

**`ModuleNotFoundError` for `alpasim_grpc`, `alpasim_utils`, or `eval`**

- Activate the environment that contains the AlpaSim packages and generated
  protobufs; verify with a small `python -c` import before running a glob.
- Check that Python is within the package's supported 3.11–3.12 range and that
  dependency installation is consistent. Do not mix a checkout's partial
  `PYTHONPATH` with a different installed package unless comparing versions on
  purpose.
- Verify `utils_rs` separately. Geometry imports can fail even when protobuf
  imports work because geometry is an optional native extra.

**`print-asl` or `asl-to-frames` fails importing `main`**

This is a known packaging mismatch: the console metadata points to a `main`
symbol that the corresponding `__main__` module does not define. Use
`python -m alpasim_utils.print_asl`, `python -m alpasim_utils.asl_to_frames`,
or the bundled scripts. Do not “fix” a run by importing private checkout code.

## Optional dependencies and backends

**MP4 extraction or video rendering fails at import/codec time**

Use `--format frames` first. MP4 requires imageio's ffmpeg support and valid
PNG/JPEG payloads; evaluation videos also use matplotlib/ffmpeg. A frame
extraction success does not prove the evaluation video path works.

**Map/offroad fails while ASL parsing succeeds**

Check USDZ discovery, scene-id uniqueness, map members inside the archive, and
whether the compatible `trajdata` map stack is installed. A missing map can
leave offroad unavailable; aggregation may insert zero and emit a warning.
Do not call that a measured offroad pass.

**Driver/model debug payload causes unsafe parsing**

`parse_unstructured_debug_info` may parse pickle-encoded data from some driver
images. Set it false for untrusted images or containers. Keep model weights,
HF credentials, renderer containers, and large scene caches outside this
skill's scripts.

## Data and configuration

**No ASL files or “only part of files are complete”**

Check the quoted recursive glob and its suffix. Confirm each intended rollout
has `_complete` beside the ASL. An interrupted rollout may have an ASL but no
marker; evaluate it explicitly only with a deliberate fixture/debug path.

**Missing metadata / empty evaluation input**

The accumulator needs `rollout_metadata`, including an EGO AABB, transform, and
recorded ground truth. It also needs actor poses to build trajectories. Driver
responses, camera records, routes, traffic returns, and a map are conditional
on the selected scorers and video layouts. Inspect message types before
changing config.

**Unexpected scene or rollout identifiers**

Evaluation extracts clip and rollout ids from the two parent directories of a
file. Keep the standard `rollouts/<clipgt-id>/<rollout-id>/` structure. A
renamed or shallow fixture can produce `unknown` ids or merge rows incorrectly.

**Scene score fails for missing columns**

Enabled scene scoring requires its score metrics, including ground-truth
travel distance and progress inputs. Either repair upstream ASL/evaluation
inputs or intentionally disable scene scoring and report the result as
unscored; do not fill required columns with guessed values.

## CLI and API misuse

**`--message-types` rejects a value**

Use the protobuf `LogEntry` oneof field name, such as `rollout_metadata`,
`actor_poses`, `driver_return`, or `driver_camera_image`, not a Python class
name. Start with `python -m alpasim_utils.print_asl --help` to see choices.
`--end` is an exclusive message index in the bundled helper.

**Frame extraction reports no usable frames**

The log needs `driver_camera_image` records for ordinary camera streams, or a
paired `video_model_chunk_request` and `video_model_chunk_return` for video
model streams. `RolloutMetadata` and `DriveSessionRequest` are also required by
the source workflow. Check the type listing and the first matching payload.

**Programmatic evaluator raises on configuration or geometry**

Build a complete `EvalConfig` with vehicle, scorer, aggregation, scene-score,
video, process, and vector-map fields. Use the same rig/AABB transform and
valid timestamp arrays in `ScenarioEvalInput`. A `None` map is legal for tests
but not for offroad claims.

## Workflow failures

**Evaluation fails in multiprocessing but a small fixture works**

Run one worker, isolate the failing ASL, and inspect the first traceback. Check
that every ASL matches the same protobuf/package version and that maps can be
opened by worker processes. Reduce the glob before raising `num_processes`.

**Aggregation finds no metrics**

Per-rollout parquet must be under `rollouts/**/metrics.parquet`. Re-run
post-evaluation, check write permissions and parquet dependencies, and inspect
whether an earlier rollout was filtered by `_complete`. Do not aggregate a
stale `eval/metrics_unprocessed.parquet` as if it were the current unified
layout without checking its schema.

**Aggregation changes pass/fail unexpectedly**

Inspect `metrics_results.txt` modifiers, retained timestamps, and
`results-summary.json`. Pre-engagement removal, black-image trajectory removal,
post-event truncation, and the ground-truth-distance cutoff intentionally
change the rows that reach scene scoring. Compare raw per-rollout metrics
before comparing run-level means.

**Re-evaluation detects an array job but the child jobs disagree**

Check that each child has compatible evaluation and wizard configs, unique clip
ids when combining runs, and a complete scene cache. Evaluate one child locally
first; then aggregate only the successful children. Scheduler mode creates and
submits external jobs and is not a substitute for this diagnosis.

**Video links are broken**

Aggregation uses relative symlinks to videos in rollout directories. Verify
that the original rollout directories remain mounted and that the video filename
contains the expected clip, rollout, camera, and layout ids. Regenerate links
only after verifying metrics; do not copy large video trees into the skill.

## What to report

Record the exact run root, glob, config revision, package/backend versions,
first failing message or file, marker status, map/codec availability, and
whether the failure is syntax, missing data, optional dependency, or required
workflow failure. State what was not tested: GPU/container/model/HF/Slurm
paths, large assets, and credentialed downloads are separate capabilities.
