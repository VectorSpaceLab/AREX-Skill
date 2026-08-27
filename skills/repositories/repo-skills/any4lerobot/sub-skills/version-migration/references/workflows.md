# Guarded migration workflows

These are review recipes, not copy-paste commands that silently mutate a
repository. Replace placeholders only after the preflight in `SKILL.md` and
record the exact environment and paths. The source converters are not bundled
or wrapped because their side effects are material.

## Common preparation

1. Define immutable `SOURCE_ROOT`, disposable `WORK_ROOT`, and `BACKUP_ROOT`.
   Ensure source and destination are different resolved paths and neither is a
   broad parent such as a home or root directory.
2. Capture a file manifest with sizes and checksums for `meta/`, `data/`,
   `videos/`, and `images/`. Record the source `info.json`, repo revision,
   branch, tag, and dirty state. Preserve the manifest outside the dataset.
3. Copy/snapshot the source before a migration. A filesystem snapshot or
   read-only clone is preferable to a same-volume rename. Existing names such
   as `<root>_old`, `<root>_v30`, and `<root>_v21` are collision hazards.
4. Run a static metadata checker and a target-namespace import probe. A probe
   may import modules and parse arguments, but must not open a Hub session,
   download data, create a branch, spawn workers, call `ffmpeg`, or write a
   dataset.
5. Plan a local output first. Keep Hub credentials available only for a later
   publication step; do not put `--push-to-hub` or deletion flags in the first
   run plan.

## v1.6 → v2.0

The source converter requires `--repo-id` and exactly one mutually exclusive
annotation mode:

```text
--single-task TEXT
--tasks-col COLUMN_NAME
--tasks-path JSON_FILE
```

Optional controls include `--robot`, `--local-dir`, `--license`, and
`--test-branch`. The task path is an episode-index-to-task JSON mapping. The
column mode cleans a known TensorFlow string wrapper, creates task indices, and
removes the task column from data. A single task assigns one task to every
episode. If `language_instruction` exists, the source behavior prefers it over
`--single-task`; make that override explicit in the run record rather than
assuming the requested flag won.

Preflight requirements:

- source episode indices must be `0..N-1`;
- all task mapping keys must be present exactly once and every task value must
  be non-empty text;
- sequence feature lengths must agree with robot motor names;
- `meta_data/info.json` must agree with inferred fps/video state;
- video count must equal episodes × video feature count;
- a robot type must be explicitly known or marked `unknown` for review.

The converter writes one parquet per episode under chunk directories, writes
`meta/info.json`, `meta/tasks.jsonl`, `meta/episodes.jsonl`, and converts
`safetensors` stats to `meta/stats.json`. Video handling is particularly
sensitive: the reference clones a Hub dataset with Git-LFS smudge disabled,
renames files into chunk/camera paths, may repair `.gitattributes` and LFS
tracking, commits, and pushes. This is not a local-only operation. If the
video migration is not separately approved, stop after the metadata/data plan
or use a test branch and an independently backed-up copy.

## v2.0 → v2.1

Inputs are loaded with `LeRobotDataset(repo_id, ..., revision="v2.0")`.
`--root` selects an exact local root; without it, the source implementation
uses its local/cache/Hub resolution and `force_cache_sync=True`. Controls:

```text
--repo-id REPO_ID                 required
--root LOCAL_ROOT                 optional
--num-workers N                   default 4; use 0 for serial debugging
--branch BRANCH                   publication revision
--push-to-hub                     off by default
--delete-old-stats               destructive cleanup; off by default
```

The conversion removes an existing episode-stats file, computes per-episode
stats (video frames are sampled), writes episode stats, aggregates them, and
compares the aggregate with reference stats. It then sets `codebase_version`
to `v2.1`. Use serial workers first for a small fixture and verify that all
episodes were written. Only after validation should a Hub upload of `meta/` and
creation of the `v2.1` tag be considered.

## v2.1 → v2.0

Use the same v2.1-compatible environment and an explicit local root whenever
possible. The route writes aggregate `stats.json`, changes `codebase_version`
to `v2.0`, and may push only metadata. `--delete-old-stats` removes
`episodes_stats.jsonl` locally and, when found, on the Hub. Keep that flag off
until a v2.0 reader has opened the output and the backup is verified. The
source code contains an `is_file` call-site bug on the local cleanup condition;
validate file presence yourself and do not interpret a successful process as
proof that deletion happened as intended.

## v2.1 → v3.0

The reference route's options are:

```text
--repo-id REPO_ID                       required
--root LOCAL_ROOT                       exact v2.1 root; otherwise HF cache root
--branch BRANCH                         publication revision
--data-file-size-in-mb N                default from target LeRobot
--video-file-size-in-mb N               default from target LeRobot
--push-to-hub true|false                source default is true; override false
--force-conversion                      bypass existing v3.0 revision check
```

Set `--push-to-hub=false` for local staging. If `--root` is omitted, the
reference first tries to download an existing v3.0 revision and returns if one
exists unless forced; this implicit network behavior is why explicit roots and
`--force-conversion` review are required. Validate `info.codebase_version ==
"v2.1"` before processing.

The route converts info/tasks/data/videos/episodes metadata into the v3
consolidated layout. It concatenates episode parquet files up to a file-size
threshold and concatenates videos per camera with timestamp metadata. It
creates a temporary `<root>_v30`, then renames the original to `<root>_old`
and swaps the new tree into the original name. Existing `_old` and `_v30`
directories can be removed by the source behavior; never point it at a root
with unreviewed siblings. With Hub publication enabled, the source deletes old
patterns, changes tags, and pushes; perform those actions only as an explicit
second stage.

Before approving the video path, check every camera has the same episode count,
all episode indices align, durations are positive, and concatenated file
metadata can be reopened by the target decoder. A video-free dataset should
skip video conversion and have a null video path.

## v3.0 → v2.1

This route takes `--repo-id` and optional `--root`; it has no push flag. If the
root is absent, the source downloads a v3.0 revision. Use a local copy and
block network access for a dry structural review.

The reverse operation reads consolidated episode parquet metadata and grouped
`data/chunk-*/file-*.parquet` files, slices rows by
`dataset_from_index`/`dataset_to_index`, reconstructs legacy task and episode
JSONL, and copies `images/` when present. For every video feature it groups
records by the v3 file indices and invokes `ffmpeg` with `-ss`, `-t`, stream
copy, and a bounded timeout to create one legacy video per episode. Require:

- a backup of the complete v3 tree and a fresh, empty destination sibling;
- `ffmpeg -version` preflight, decoder support, writable output, and enough
  temporary/storage capacity;
- a synthetic metadata-only check for timestamps and path containment before
  any real ffmpeg invocation;
- post-slice checks for episode count, video existence, playable duration, and
  no unexpected files;
- review of the source's `_v3.0` backup and destination swap before cleanup.

The source deletes existing `_v3.0`/`_v2.1` siblings and then renames roots.
It does not publish to the Hub, but an absent root can trigger a download. A
failed ffmpeg call must leave the source backup untouched and must not be
recovered by deleting it.

## Validation and publication ladder

Use this order:

1. metadata-only static validation;
2. synthetic two-episode fixture for task/index/stats/layout transformations;
3. local migration into a new destination with no Hub writes;
4. target-version reader open and representative row/video checks;
5. test branch upload, if approved;
6. independent consumer read from the test branch;
7. production tag/rename/delete only after an operator confirms the manifest,
   branch, repo id, and rollback plan.

Do not combine rename, conversion, deletion, and publication in one unattended
step. A tag is not a backup, and a Hub revision does not protect local data
from a destructive root swap.
