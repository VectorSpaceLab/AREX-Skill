# Version migration troubleshooting

This reference is a review and recovery guide for the supported LeRobot
version routes. It does not run a converter, download a dataset, invoke
`ffmpeg`, use Git-LFS, contact the Hub, publish a branch/tag, or delete files.
Treat every command below as a preflight or inspection step unless an operator
has separately approved a migration stage.

Use the route and layout contracts in [version-matrix](version-matrix.md),
[workflows](workflows.md), and [metadata-layouts](metadata-layouts.md)
before diagnosing an error. Paths in this document are dataset-relative.

## Triage rules

For every failure, first preserve the source snapshot, manifest/checksums,
environment lock, intended route, resolved source/destination roots, branch/tag,
arguments, first failing stage, and complete stderr. Work on a disposable copy
and a newly named destination. Do not rerun over an unexplained partial tree.

**Stop immediately** when the source version is uncertain, the root overlaps the
destination, a required metadata record is missing, a destructive operation has
already started without a backup, or the failure could have changed a Hub branch.
Classify the case as repair/rollback rather than normal migration until the
source is restored or an operator approves a repair plan.

## Install and import compatibility

**Symptom: `ModuleNotFoundError`, missing constants, or an import from
`lerobot.common.datasets.*` versus `lerobot.datasets.*` fails.**

- **Likely cause:** the converter is coupled to a historical LeRobot checkout;
  a package that merely reports a similar semantic version is not sufficient.
  The v1.6→v2.0 source uses the older `lerobot.common` namespace, v2.x routes
  use `lerobot.datasets.lerobot_dataset` and `lerobot.datasets.utils`, and the
  v3 routes use `lerobot.datasets`, `io_utils`, and `video_utils`.
- **Preflight/recovery:** select the exact route pin and isolated environment;
  install that checkout editable; probe every imported module, constant, and
  callable signature without opening a dataset or writing output. Record Python,
  LeRobot revision, `datasets`, `jsonlines`, `pyarrow`, `safetensors`,
  `huggingface_hub`, and `ffmpeg` versions. Compare the expected environment in
  [version-matrix](version-matrix.md).
- **Stop condition:** do not patch `sys.path`, mix current and historical
  modules, copy individual source modules, or proceed after only one class
  (`LeRobotDataset`) imports. A namespace or signature mismatch is a hard stop.

**Symptom: the class imports, but `revision`, metadata paths, stats methods, or
`push_to_hub` arguments fail later.**

- **Likely cause:** API compatibility is partial: constructor semantics,
  constants, metadata writers, or publication arguments changed.
- **Recovery:** probe the route's constructor and read-only metadata/stat
  interfaces against a tiny synthetic layout. Keep publication disabled while
  checking the target reader. Re-pin the environment if any expected API is
  absent.
- **Stop condition:** a passing import is not conversion compatibility. Do not
  execute a data-writing stage until the target API can open a representative
  target-layout fixture and the required signatures match.

**Symptom: v3.0→v2.1 raises errors involving `List` or `Column`.**

- **Likely cause:** the source README identifies `datasets>=4.0.0` as
  incompatible with this historical route.
- **Recovery:** in the isolated v3 environment, use a tested `datasets<4.0.0`
  version, record the exact version, and rerun only the read-only import/layout
  probes.
- **Stop condition:** never downgrade a shared environment or continue with a
  failed compatibility probe.

## Dependencies: required versus optional

**Symptom: `jsonlines`, `datasets`, `pyarrow`, or `safetensors` is missing.**

- **Likely cause:** the selected historical environment is incomplete. v1.6
  input stats require `safetensors`; v1.6 parquet inspection and conversion
  require `datasets` and `pyarrow`; v2.1↔v3.0 metadata conversion uses
  `jsonlines`, `datasets`, and `pyarrow`. Hub stages also require a compatible
  `huggingface_hub` client and permission to use it.
- **Preflight/recovery:** install the missing package only in the isolated,
  route-pinned environment, then record the version and rerun the import and
  static-layout probes. Verify that `meta_data/stats.safetensors` is readable
  before planning v1.6→v2.0. For a metadata-only review, do not install or
  exercise packages needed only by a later video or publication stage.
- **Stop condition:** a missing package blocks the stage that imports it; do not
  replace it with a newer API or fabricate stats. A missing `safetensors` file
  blocks the v1.6 route, not merely its optional video stage.

**Symptom: video or Hub functionality is unavailable while metadata-only
checks pass.**

- **Likely cause:** video decoding/encoding, Git-LFS, or Hub credentials are
  optional for a local metadata-only plan but required for the corresponding
  migration stage.
- **Recovery:** separate the plan into metadata/data and video/publication
  stages. Record the missing capability and validate the non-video portion only.
  Add the dependency and permissions later in the isolated environment.
- **Stop condition:** do not claim a complete migration when a required video
  or publication gate was skipped. Do not turn optional access into implicit
  network or credential use.

## Version identity and root/layout validation

**Symptom: the source version is `unknown`, disagrees with the requested route,
or a converter reports an unexpected `codebase_version`.**

- **Likely cause:** the wrong metadata root was inspected, the tree is partial,
  or it was already partly migrated. A directory name or Hub tag alone is not
  version evidence.
- **Preflight/recovery:** read and cross-check `meta/info.json` for v2.0/v2.1/v3.0;
  for v1.6 inspect `meta_data/info.json`, `meta_data/stats.safetensors`, data,
  and legacy video names. Compare path signatures and required files in
  [metadata-layouts](metadata-layouts.md). Restore a trusted snapshot
  if metadata and paths disagree.
- **Stop condition:** never use `--force-conversion` to bypass a version check.
  Do not proceed until exactly one source version and one supported direction
  are established. There is no supplied reverse v2.x→v1.x converter and no
  direct v1.6↔v2.1/v3.0 route; use validated intermediate hops.

**Symptom: `FileNotFoundError` for `info.json`, tasks, episodes, stats, parquet,
or video files; or the converter reads an empty dataset.**

- **Likely cause:** `--root` points to a parent/child rather than the exact
  dataset root, or a Hub/cache snapshot is incomplete. v2.x roots contain
  `meta/`, `data/`, and optional `videos/`; v1.6 uses `meta_data/`; v3 uses
  consolidated `meta/tasks.parquet` and `meta/episodes/chunk-*/file-*.parquet`.
- **Preflight/recovery:** resolve the root without following an unreviewed
  symlink; inspect `info.json` and path templates; verify every referenced local
  file exists and that the root is not a broad parent. For v1.6 distinguish
  `--local-dir` staging space from `--root` (the v1.6 source still requires a
  Hub `--repo-id`). For v2.x/v3, prefer an explicit exact local root.
- **Stop condition:** do not pass a local path as `--repo-id`, use a parent that
  happens to contain `meta/`, or continue with an incomplete snapshot.

**Symptom: layout validation passes superficially but episode counts, indices,
lengths, task references, or feature shapes disagree.**

- **Likely cause:** duplicate/non-contiguous episode indices, missing camera
  records, stale `total_*` fields, invalid data slices, or schema drift.
- **Preflight/recovery:** check unique sorted indices and route-required
  contiguity (`0..N-1` for v1.6), positive lengths, `total_episodes` and frame
  counts, task-index resolution, feature dtype/shape, and existence of every
  data/video path. In v3 also check `dataset_from_index < dataset_to_index`,
  `data/*` index columns, and matching episode IDs across cameras.
- **Stop condition:** do not let a converter silently enumerate, remap, or
  discard records. Produce an explicit old-to-new remapping or repair plan and
  obtain approval before any write.

## Task annotation selection and CLI/API misuse

**Symptom: v1.6→v2.0 rejects task arguments, maps null tasks, or produces the
wrong task indices.**

- **Likely cause:** the three modes are mutually exclusive and exactly one is
  required: `--single-task`, `--tasks-col`, or `--tasks-path`. The column flag
  takes a column name, while the path flag takes a JSON file mapping each
  `episode_index` to one non-empty text instruction.
- **Preflight/recovery:** inspect all episode IDs and task values before a run.
  Ensure the JSON covers every episode exactly once and that the selected column
  exists, is textual, and has episode coverage. Note that the source behavior
  cleans the known `tf.Tensor(b'...', shape=(), dtype=string)` wrapper. If
  `language_instruction` exists, it overrides a supplied `--single-task`; record
  that semantic change and get confirmation.
- **Stop condition:** do not pass a JSON path to `--tasks-col`, combine task
  modes, fabricate missing annotations, accept an empty task, or proceed when
  the override changes the intended labeling.

**Symptom: `--root`, `--local-dir`, `--repo-id`, `--branch`, or push flags behave
unexpectedly.**

- **Likely cause:** flags have route-specific meanings. `--repo-id` is a Hub
  identifier; `--root` is an exact local v2.x/v3 dataset root; v1.6
  `--local-dir` is staging/cache space. `--push-to-hub` is a boolean flag on
  v2.x, while v2.1→v3.0 parses an explicit `true`/`false` string and defaults
  to true; v3.0→v2.1 has no push flag.
- **Recovery:** make a no-write argument record with explicit root, repo,
  revision/branch, and publication state. During local staging set publication
  off (`--push-to-hub=false` where that syntax is supported) and avoid omitted
  roots that can trigger cache or Hub resolution.
- **Stop condition:** cancel if a local run contacts the network unexpectedly,
  if a route receives an unsupported flag, or if a default publication setting
  is still enabled. `--force-conversion`, deletion flags, and worker count do
  not create a backup.

**Symptom: worker/pickling, memory, or video-decoder failures occur only with
parallel stats computation.**

- **Likely cause:** `ProcessPoolExecutor` or video sampling is incompatible
  with the environment or available memory.
- **Recovery:** preserve the output and logs, then plan a small fixture with
  `--num-workers 0` (serial mode) and compare counts/stats. Increase workers
  only after serial behavior is understood.
- **Stop condition:** do not treat a partial `episodes_stats.jsonl` as valid or
  delete the old aggregate stats after a worker failure.

## Stats and schema drift

**Symptom: v2.0→v2.1 aggregate comparison fails, or stats contain NaN/Inf,
wrong dtypes, missing features, or incompatible shapes.**

- **Likely cause:** episode slicing differs from the aggregate source, feature
  schema changed, video stats are sampled, values contain non-finite numbers,
  or the chosen tolerance hides a real mismatch. The reference uses tighter
  tolerances for non-video data and looser tolerances for sampled video.
- **Recovery:** retain both old stats and generated episode stats; compare one
  feature at a time, then check frame counts, dtype/shape, episode boundaries,
  video sampling, and finite numeric values. Recompute in serial mode on a
  small fixture before changing any tolerance. Document any approved tolerance
  change.
- **Stop condition:** an aggregate mismatch is a data-quality stop, not a
  reason to widen tolerances, delete `stats.json`, or publish.

**Symptom: v2.1↔v2.0 cannot read or write the expected stats files, or cleanup
reports success while the old file remains.**

- **Likely cause:** the route expects `stats.json` for v2.0 and
  `episodes_stats.jsonl` for v2.1; the supplied source has an `is_file` call-site
  bug in its local deletion condition.
- **Recovery:** inspect actual file presence before and after every planned
  stage. Write the target stats into a new destination and retain both old
  representations in the backup until a target-version reader passes.
- **Stop condition:** do not infer cleanup from exit status. Keep deletion and
  Hub cleanup as separately approved actions.

**Symptom: v2.1→v3.0 or v3.0→v2.1 loses stats fields, task fields, or metadata
columns.**

- **Likely cause:** v3 flattens episode stats into `stats/<feature>/<field>`
  columns and consolidates task/episode metadata; reverse conversion filters
  back to the legacy `mean`, `std`, `min`, `max`, and `count` fields. Stale
  `info.json` templates or changed feature schemas can also misalign rows.
- **Recovery:** compare source and destination feature names, dtypes, shapes,
  task strings, episode IDs, and flattened stats keys. Check v3 data/video
  index columns and slice bounds before accepting reconstructed files.
- **Stop condition:** never fabricate missing stats or silently present v3-only
  fields as v2.1-compatible. Stop on a missing index column or any count/key
  mismatch.

## Video, metadata, and `ffmpeg` failures

**Symptom: v1.6 video count, FPS, pixel format, or decoder checks fail.**

- **Likely cause:** `total_episodes × video feature count` does not match the
  files, `meta_data/info.json` disagrees with the sample video, or a legacy
  camera/episode filename is missing. The v1.6 route checks FPS and, when
  supplied, pixel format.
- **Recovery:** inspect one representative file per camera and episode range;
  compare readable metadata with `fps`, encoding, and feature declarations.
  Validate Git-LFS tracking separately. Use a metadata-only/no-video plan only
  if the operator explicitly accepts the loss or exclusion.
- **Stop condition:** do not move, upload, or rename videos when count, FPS,
  pixel format, or source readability is unresolved.

**Symptom: v2.1→v3.0 reports unequal camera episode counts/order, or v3.0→v2.1
cannot find a source video or a video index column.**

- **Likely cause:** cameras were recorded with different episode sets, records
  were sorted by filename rather than episode identity, or
  `videos/<key>/{chunk_index,file_index}` metadata is stale/missing.
- **Recovery:** compare episode IDs and source paths independently for every
  camera; verify each referenced consolidated video path and the
  `from_timestamp`/`to_timestamp` pair. Correct metadata from a trusted backup,
  not by sorting or padding records.
- **Stop condition:** do not concatenate, split, or accept a video-free result
  while any camera is misaligned. A missing index column or missing source file
  is a hard stop.

**Symptom: `ffmpeg` is missing, times out, returns non-zero, or emits an
unplayable output.**

- **Likely cause:** the binary/codec is absent, source duration is invalid,
  output storage is unavailable, or the segment request is malformed. The
  reverse source uses stream copy and a bounded timeout.
- **Preflight/recovery:** before any approved video stage, record `ffmpeg`
  version and decoder support; validate writable destination space, source
  existence/regular-file status, allowed video extensions, and a synthetic
  metadata-only timestamp plan. Preserve stderr and the partial destination on
  failure; inspect output duration/playability before considering retry.
- **Stop condition:** reject non-finite, negative, or reversed ranges
  (`start >= end`); for this route require `0 <= start <= 86400`,
  `0 <= end <= 86400`, and a segment duration no greater than 3600 seconds.
  Also reject paths with traversal/control characters, system-directory
  targets, or a retry over a non-disposable partial destination. Do not delete
  the source backup to recover from an `ffmpeg` failure.

## Git-LFS, Hub, branch, and tag failures

**Symptom: Git-LFS clone, `.gitattributes`, rename, commit, or push fails; files
are pointer files or not tracked.**

- **Likely cause:** Git-LFS is unavailable, credentials are insufficient, the
  branch is wrong, the repository has untracked video files, or the v1.6 route
  needs a `.gitattributes` repair. The source may change the working tree and
  push during video relocation.
- **Recovery:** stop and preserve the working directory, `git status`, remote,
  current revision, branch, and manifest. Do not blindly rerun. Compare against
  the immutable snapshot and use a fresh test branch/worktree after credentials,
  LFS tracking, and approval are resolved.
- **Stop condition:** no implicit credentials or push permission may be used.
  If any remote mutation may have occurred, freeze further publication and get
  an owner-approved branch/revision recovery plan.

**Symptom: authentication, DNS, timeout, rate-limit, or offline errors occur;
a local request unexpectedly downloads from the Hub.**

- **Likely cause:** a missing `--root`, omitted v1.6 staging/repo inputs, Hub
  snapshot resolution, or a publication flag caused network access; or the
  token lacks read/write/revision permissions.
- **Recovery:** cancel network activity, record whether any remote mutation
  occurred, and switch to an explicit local immutable snapshot for structural
  checks. Later, test read-only access and write access independently on a
  disposable branch with credentials supplied by the operator.
- **Stop condition:** no download, upload, deletion, or push is a valid
  troubleshooting step here. Do not retry an unknown remote operation against
  a production revision.

**Symptom: branch creation/push targets the wrong revision, or tag creation
fails/already exists.**

- **Likely cause:** `branch=None` resolves to the route's default (often
  `main`), `--test-branch` was omitted, a branch/tag name is invalid or already
  present, or the source's tag is not a backup.
- **Recovery:** inspect branch heads, tag targets, permissions, and the intended
  repo id; compare them with the preflight manifest. Use a new explicitly named
  test branch after approval, and record the exact revision before any retest.
- **Stop condition:** do not force-delete/repoint a tag, overwrite `main`, or
  infer success from a new version tag. A tag and a Hub revision are not a
  substitute for an immutable backup and consumer read.

## Destructive rename/delete and rollback

**Symptom: destination already exists, or siblings such as `_old`, `_v30`,
`_v21`, `_v3.0`, or `_v2.1` are present.**

- **Likely cause:** the reference routes create temporary sibling roots and may
  remove an existing sibling before swapping directories. The v2 stats routes
  also unlink files; Hub routes delete old folders/patterns.
- **Recovery:** stop before cleanup. Resolve all paths, capture manifests and
  checksums, quarantine or remove nothing, and choose a fresh destination outside
  the source parent. Require explicit approval for any rename, replacement, or
  deletion.
- **Stop condition:** never let converter cleanup choose which copy to keep;
  never use a symlink to disguise source/destination overlap; never proceed
  without an immutable rollback copy.

**Symptom: a process was interrupted after a rename, unlink, upload, or partial
write.**

- **Recovery sequence:**
  1. Stop all retries and do not clean the source, backup, or partial output.
  2. Record the first failed stage, stderr, process status, resolved paths,
     local manifests, branch/tag, and whether a Hub mutation is confirmed.
  3. Compare source, backup, and destination checksums. If the source is
     unchanged, quarantine the partial destination and validate the backup.
  4. Restore from the immutable snapshot into a newly named root, or use a
     documented repair plan with old-to-new file mappings. Keep the failed tree
     for review outside the next run.
  5. For a Hub mutation, freeze publication and have the repository owner
     identify the known-good revision/branch before any revert or new test
     branch. Re-read the restored revision as an independent consumer.
- **Stop condition:** if no immutable snapshot, manifest, or known-good Hub
  revision exists, report rollback as unverified and stop. Do not claim recovery
  from a renamed directory, tag, or successful process exit alone.

A recovered migration is acceptable only after the target reader opens the
restored/new tree and counts, tasks, stats, data paths, and (when in scope)
video metadata match the approved plan. Keep the complete recovery record and
unresolved gaps with the review artifacts, not inside the runtime dataset.
