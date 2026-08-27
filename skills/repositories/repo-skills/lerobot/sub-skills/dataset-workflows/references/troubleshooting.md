# Dataset troubleshooting and intentional limits

## Metadata, schema, and episode failures

**`FileNotFoundError` for metadata or data.** Confirm the argument is the exact
dataset root, not its parent or a Hub cache directory. Check `meta/info.json`,
`meta/episodes/*/*.parquet`, and `data/*/*.parquet` before constructing
`LeRobotDataset`. If any are absent, stop the local check; otherwise the package
may attempt a Hub download. Use the local loader helper to report the missing path
without network access.

**Missing `episode_index`, invalid episode index, or no episode metadata.** The
reader uses `episode_index` for Parquet predicate filtering and for episode
sufficiency checks; episode metadata supplies frame and video offsets. A missing
column or missing episode map is a hard schema error. Restore the source metadata
or run a deliberate v2.1/third-party port into a new root. Do not fabricate ids by
sorting filenames. Validate a fresh process after repair.

**Feature mismatch or shape error.** Compare `meta.info.features` to one Parquet
schema and a raw row. At write time, `DatasetWriter.add_frame` reaches
`validate_frame` and `validate_feature_dtype_and_shape`, where numeric dtype/shape
is exact and image/video shape accepts HWC or CHW. At read time,
`DatasetReader._load_hf_dataset` builds the Hugging Face schema and
`load_nested_dataset`/Arrow raises if stored columns cannot satisfy it. Public
image tensors are generally CHW. Check whether a declared image shape is
`(H,W,C)` versus `(C,H,W)` and check channel count. The standard bookkeeping
features are writer-generated and should not be included in `add_frame`.

**Language-column error.** If Parquet contains a supported language column not
listed in metadata, `DatasetReader._validate_language_columns_declared` raises a
ValueError naming the missing feature. Synchronize `info.features` with the
annotation output; do not silently drop the stored column.

**Task lookup error.** `task_index` must resolve through `meta/tasks.parquet` and
`task` is added from that mapping at read time. Check duplicate/empty task entries,
indices, and episode `tasks`. `modify_tasks` requires at least one of `new_task`,
`episode_tasks`, or `task_replacements`; replacement keys must already exist and
episode keys must be in range. It rewrites the source in place in the current tool
contract, so make a copy first.

**Stats missing or wrong shape.** A dataset can load without `stats.json`, but a
normalizing policy may not be valid. Stats are per-feature and commonly have
channel/vector shapes; recompute with `recompute_stats` on a distinct output or
with explicit overwrite consent. Relative-action stats must use the same action
chunk and excluded joints as the policy. Never claim normalization readiness from
metadata-only success.

## Video and image failures

**Optional decoder/FFmpeg unavailable.** The dataset extra supplies PyAV and may
supply TorchCodec only on supported platform/Python/Torch wheel combinations. The
random-access reader chooses a safe backend; streaming RGB video uses TorchCodec
when available, while streaming depth uses PyAV. An image-only dataset can be
inspected and loaded on CPU without a video decoder. That is a valid fallback for
image-backed data only and does not prove any MP4 codec works.

**MP4 codec or pixel-format error.** Distinguish (1) missing optional package or
system library, (2) unsupported encoder/decoder in the current build, (3) missing
MP4 path, and (4) corrupt/truncated MP4. Check `meta/info.json` video info, the
referenced path, file size, and a one-frame bounded decode. Do not switch to a
random codec or reinterpret depth as RGB. For a valid source, re-encode to a new
root with a codec available to the current PyAV build; preserve depth parameters.

**Timestamp mismatch.** Reader initialization checks data/video spacing against
`fps` and `tolerance_s`; delta timestamps also must align to the frame grid. Fix
the source timestamps or use a justified tolerance change after measuring drift.
Do not use large tolerance to mask a frame-rate or video offset error.

**Video reads fail only with DataLoader workers.** Video decoder objects must not
be created in the parent and reused by child workers; the reader documents this as
a possible segmentation fault path. First test `num_workers=0`, then use a
worker-safe construction pattern and a bounded sample. Do not run a second
video DataLoader in the main process over a decoder already created there.

## Streaming, Hub, and porting failures

**Streaming returns no frames or repeats unexpectedly.** Verify `streaming=True`,
`buffer_size`, `max_num_shards`, `seed`, `shuffle`, and the source split. Streaming
is an iterable and uses bounded backtrack/lookahead; positive/negative delta
windows crossing an episode are padded. A bucket requires `repo_type="bucket"`
and remote access to both Parquet and MP4.

**Hub credentials/network failure.** Separate local metadata validation from
remote access. Confirm the repo/revision, credential consent, and network before
retrying. Never place tokens in a report. For a private or gated dataset use the
normal Hub login/token mechanism; `token=False` deliberately disables auth and may
produce a permission failure.

**v2.1 conversion fails.** Confirm `info.codebase_version` is exactly the expected
v2.1 input, the legacy `episodes.jsonl`, `episodes_stats.jsonl`, and tasks files
exist, and the `jsonlines` extra is installed. Use a small copied input, keep
`--push-to-hub=false`, and inspect output v3 metadata/data/video before scaling.
Third-party ports are intentionally not generic: the source reader, language/task
mapping, image/depth units, and episode boundaries must be documented.

## Editing and safe planning

**No explicit output or overwrite intent.** Stop and plan. The CLI can infer a
name/location for some operations, but relying on that is unsafe for production.
Use `dataset_operation_plan.py` with source root, operation, and a proposed output;
it refuses missing output for mutating operations and detects an existing output.
For in-place `modify_tasks`, require an explicit backup/copy. For recompute or
re-encode, pass an output root or explicitly approve the operation's overwrite
switch.

**Conversion writes unexpectedly or runs too long.** Stop before retrying; inspect
whether output contains a partial root. Do not reuse partial output without a
freshness check. Bound `episode_indices`, `max_episodes_per_batch`,
`max_frames_per_batch`, workers, and disk usage. Long porting, video conversion,
re-encoding, and Hub upload are not safe smoke tests.

## Intentional omissions and uncertainty

- This sub-skill does not promise a particular GPU encoder, FFmpeg build, TorchCodec
  wheel, hardware acceleration path, or codec availability across platforms. Probe
  the target environment and report the exact backend.
- It does not execute physical recording/replay, train a policy, upload to Hub, or
  run a remote/distributed port. Those require the routed skills and explicit
  consent.
- The bundled helpers intentionally inspect local roots, synthetic transforms, and
  operation plans only. They do not implement a source-format converter, perform
  arbitrary Parquet repair, or mutate a dataset.
- Dataset visualization requires optional Rerun/Foxglove packages and may open a
  UI or network server; a missing viewer is not a data-format verdict.
- No claim is made that all future v3 schema variants, custom language columns,
  third-party dataset readers, or every `convert-dcp` backend are covered. Re-run
  CLI help and inspect the installed package for those extensions.
