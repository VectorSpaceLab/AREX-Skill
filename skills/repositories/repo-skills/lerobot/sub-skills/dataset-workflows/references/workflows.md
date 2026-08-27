# Dataset workflow recipes

## A. Local fixture or local dataset

1. Require an exact `root` and keep network disabled during inspection. Check
   `root/meta/info.json`, at least one `root/data/*/*.parquet`, and episode metadata.
   If `info.features` has video keys, resolve every selected episode's MP4 and check
   the file exists before constructing a full reader.
2. Run `scripts/load_local_dataset.py --root <root> --limit 3 --no-decode-video`
   for metadata/schema/count inspection. Add `--sample` only after the referenced
   visual files and a decoder have been checked. The helper never downloads.
3. For a normal random-access load, use:

   ```python
   from lerobot.datasets import LeRobotDataset
   ds = LeRobotDataset(
       "fixture/or-local-id", root="<root>", episodes=[0],
       download_videos=False, return_uint8=True,
   )
   print(ds.meta.features, ds.meta.episodes[0])
   item = ds[0]
   ```

   `download_videos=False` is a network/download guard, not a video decoder
   fallback. Do not use it with an item read until MP4 presence is established.
4. Confirm `item` keys, tensor shapes, frame/episode/index values, `task`, and
   finite numeric values. For image-backed data, verify the returned camera tensor
   is `(C,H,W)` float32 in the expected range.

## B. Hub random access versus streaming

Use `LeRobotDataset(repo_id, root=optional)` when random indexing, episode filters,
DataLoader workers, or repeated samples matter. A Hub load may download metadata,
data, and video; make revision and credentials explicit. Use
`StreamingLeRobotDataset(repo_id, streaming=True, buffer_size=..., seed=...,
shuffle=...)` when the dataset is too large for a full local copy or the task is
bounded exploration. Streaming uses HF dataset shards and has bounded buffering;
its order is randomized by default and it is not indexable.

For an HF Storage Bucket, pass `repo_type="bucket"` to
`StreamingLeRobotDataset` and use `hf://buckets/` semantics internally. A bucket
is streaming-only in the training factory. A remote stream with camera features
needs the video decoder and credentials/network access at iteration time; metadata
success is not enough. Use `max_num_shards`, a small `buffer_size`, and stop after a
bounded number of items for smoke checks.

## C. Delta windows and transforms

Delta timestamps are seconds relative to the current frame. Each offset must be a
multiple of `1/fps` within `tolerance_s`; otherwise reader initialization raises a
`ValueError`. A random-access reader clamps an offset at the episode boundary and
adds `<key>_is_pad` booleans. The streaming reader uses bounded backtrack/lookahead
and pads when history crosses an episode boundary or exceeds its buffer. Validate
that every key exists in metadata before asking for a window.

Transforms are applied at read/training time after image decoding, not during
recording. Use `ImageTransformsConfig(enable=True, max_num_transforms=...,` 
`random_order=..., tfs=...)` with `ImageTransforms`, or pass a callable torchvision
v2 transform. Do not transform depth through RGB augmentation. Run
`scripts/transform_probe.py` on a synthetic CHW float image first; then run
`lerobot-imgtransform-viz` with a bounded episode and output directory if visual
inspection is wanted. Keep evaluation transforms disabled unless the experiment
explicitly requires identical augmentation.

## D. Create, record handoff, and finalize

The dataset owner supplies `fps` and a complete user feature dictionary. Create a
writer with `LeRobotDataset.create(..., root=<new-empty-root>, use_videos=...)`.
For each frame, supply every declared user key and `task`; do not supply the five
auto-populated bookkeeping keys. Call `save_episode()` only for a nonempty episode.
On normal completion and on any conversion path, call `finalize()` before loading,
statistics validation, or Hub push. If an interrupted writer has pending frames,
choose deliberately between `save_episode()` and `clear_episode_buffer()`; do not
assume a destructor finalized valid footers.

For video capture, first validate the chosen encoder with the package's codec probe.
`streaming_encoding=True` lowers capture-time post-episode latency but introduces
bounded queues and CPU pressure. Keep `encoder_queue_maxsize`, worker counts, and
encoder threads conservative until a short local episode preserves the requested
FPS and decodes successfully. Persisted `info.features[key].info` reflects the
first encoded stream; do not change encoding settings partway through a dataset.

## E. Validate and repair metadata

For malformed metadata, make a copy and inspect `info.json`, episode Parquet
schema, one data schema, tasks, and referenced video files. Verify:

- `codebase_version` is compatible with v3;
- every non-bookkeeping Parquet column is declared in `features` and every declared
  stored feature appears in Parquet (except video, which is decoded separately);
- numeric arrays have the declared dtype/shape and image fields have a usable image
  schema;
- `total_frames` equals the sum of episode lengths and episode ids are valid;
- each episode's data indices and video duration/ranges agree with `length`;
- `task_index` rows resolve through `tasks.parquet`; and
- stats keys are a subset of declared features and stat shapes fit their features.

A missing index cannot be safely repaired by sorting filenames because v3 shards
are shared by episodes. Recover from the source episode map or use a dedicated
port/conversion process, then reload the output in a fresh process.

## F. Edit, aggregate, convert, and stats

Use `lerobot-edit-dataset` only after planning output semantics. Delete episodes and
split outputs reindex retained episodes and may re-encode mixed video shards. Merge
requires compatible feature schemas; stream-derived video codec/pixel-format,
resolution, and FPS must match. `concatenate_videos=false` and
`concatenate_data=false` keep source files separate but do not remove compatibility
requirements.

`remove_feature` cannot remove bookkeeping features. `modify_features` validates
new feature declarations and may need a callable or per-frame array. Image-to-video
conversion accepts image datasets only and supports bounded episode/frame batches;
output should be a new root. Re-encoding accepts RGB/depth encoder settings and
preserves depth quantization parameters. `recompute_stats` defaults to numeric
features and keeps image/video stats; use relative-action mode only when its
chunk size and excluded joints match the policy contract. Inspect stats after every
operation and keep the source untouched by default.

## G. Porting and visualization

For v2.1 to v3.0, first make a backup and test a small subset. The conversion
changes episode-per-file data/video into shared `file-*.parquet`/`file-*.mp4`, moves
episode metadata to chunked Parquet, converts tasks to `tasks.parquet`, and updates
`info.json`/stats. Use `convert_dataset_v21_to_v30` with an explicit local root for
offline conversion; its optional `jsonlines` dependency is part of the dataset
extra. Large third-party ports need source-format readers, storage/CPU planning,
and a bounded shard test before distributed processing.

`lerobot-dataset-viz` needs the `dataset_viz` extra (dataset + Rerun/Foxglove).
Local mode takes a root and episode index; visual output may show normal lossy MP4
artifacts. Rerun local display, save, distant/gRPC, or Foxglove WebSocket modes
have different UI/network side effects; use `--help` and choose explicitly. A
visualizer skip or import failure does not invalidate the underlying dataset.
