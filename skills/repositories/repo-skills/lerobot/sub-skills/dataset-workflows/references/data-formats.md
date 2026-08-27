# LeRobot Dataset v3 data formats

## Root and required metadata

A v3 dataset root is a self-contained directory with this shape:

```text
<root>/
  meta/
    info.json
    stats.json                 # optional for storage, usually required for normalization
    tasks.parquet              # present when tasks are registered
    episodes/chunk-000/file-000.parquet
  data/chunk-000/file-000.parquet
  videos/<feature-key>/chunk-000/file-000.mp4  # only for dtype=video
```

The exact file templates come from `meta/info.json`, normally `data_path` and
`video_path`; do not reconstruct paths from filenames or assume one episode per
file. v3 is file-based: a Parquet/MP4 shard can contain many episodes. Episode
metadata is the relational index that maps each episode to its data/video shard and
its frame/time range.

`info.json` is the canonical schema and contains at least a v3 codebase version,
`fps`, `features`, `total_episodes`, `total_frames`, `total_tasks`, `splits`,
`data_path`, and (when videos are enabled) `video_path`. It also stores chunk/file
size settings, optional robot type, and per-video information. `stats.json` maps
feature keys to `min`, `max`, `mean`, `std`, and `count`; values are loaded as
NumPy arrays and are commonly shaped `(D,)` for vectors or `(C, 1, 1)` for images.
Stats may be absent in an empty or intentionally unnormalized fixture.

`tasks.parquet` has a task string index and `task_index` values. `episodes` Parquet
contains at least `episode_index`, `tasks`, `length`, `dataset_from_index`,
`dataset_to_index`, data chunk/file references, and video chunk/file and timestamp
references for each video key. Per-episode statistics are stored as flattened
columns such as `stats/action/mean`; the public `meta.episodes` view excludes those
stats columns for faster selection.

## Features and values

User-defined feature declarations are dictionaries with `dtype`, `shape`, and
usually `names`. Common dtypes are NumPy-compatible numeric types (`float32`,
`float64`, `int64`, `bool`), `string`, `image`, and `video`. `LeRobotDatasetMetadata.create`
automatically adds these frame bookkeeping features, so a writer caller should not
supply them in each frame:

- `timestamp`: float seconds, shape `(1,)`;
- `frame_index`: integer offset within an episode;
- `episode_index`: integer episode id;
- `index`: integer global frame index;
- `task_index`: integer row into `tasks.parquet`.

A writer frame must include all user features and a `task` string. Numeric arrays
must be the declared NumPy dtype and exact shape. Image/video frame validation
accepts a NumPy array in either channel-first `(C,H,W)` or channel-last `(H,W,C)`
form, or a PIL image. Image pixels are checked by the image writer: RGB uint8 is
normally `[0,255]`, floating RGB is normally `[0,1]`. The public read transform
converts RGB PIL/image values to channel-first float tensors; `return_uint8=True`
keeps decoded RGB video frames as uint8 tensors. Video/image metadata examples
commonly declare `(H,W,C)`, but consumers should use the actual `shape` from
`info.json` and verify one sample.

For `dtype=video`, the Parquet row carries synchronization and non-visual fields;
frames are decoded from the feature's MP4 path. For `dtype=image`, image payloads
are embedded in Parquet and are decoded without an MP4 dependency. Depth features
are identified by `features[key].info.is_depth_map` (legacy markers are
canonicalized). Raw float depth is interpreted as metres; integer depth as
millimetres. Depth video is quantized at write time and dequantized at read time.

Language columns are special: stored language columns must be declared in
`info.features`. If Parquet contains a supported language column that metadata
does not declare, the reader raises a `ValueError` naming the missing feature.

## Index and episode invariants

For each episode row, `dataset_from_index` is inclusive and `dataset_to_index` is
exclusive. Their difference must equal `length`. The data Parquet rows must carry
matching `episode_index`, contiguous global `index` values, and timestamps spaced
at approximately `1/fps` within the configured tolerance. Video episode metadata
has `from_timestamp` and `to_timestamp`; its duration should agree with
`length/fps`. `meta.get_data_file_path(ep)` and `meta.get_video_file_path(ep,key)`
are the authoritative lookup helpers.

A missing `episode_index` column prevents normal dataset loading because filtering
and episode sufficiency checks use it. A missing `meta/episodes` Parquet or an
out-of-range/non-contiguous episode id is a metadata integrity failure. Do not add
an index by guessing; preserve the source episode map or run a deliberate porting
conversion with a backup and a post-conversion load check.

## Storage choices

Use `use_videos=True` when camera streams should be encoded as MP4. RGB defaults
are selected through `RGBEncoderConfig`; current defaults are software AV1-oriented
with a small GOP and quality setting, but the resolved codec and probed stream
properties are persisted under the feature's `info` block. Encoding is currently
PyAV-backed. `streaming_encoding=True` encodes during capture and uses bounded
per-camera queues; it changes write timing, not the v3 storage contract.

Use `use_videos=False` for image-backed local fixtures or when decoder/FFmpeg
availability is uncertain. `convert_image_to_video_dataset` creates a new dataset
and rejects an input that already has video keys. Depth uses `DepthEncoderConfig`
(`depth_min`, `depth_max`, `shift`, `use_log`) in metres, a 12-bit quantization
range, and a persisted depth marker/parameters. At read time `depth_output_unit`
is independent of record-time encoding and is either `mm` or `m`.

A video key can be present in metadata while its MP4 is absent or corrupt. Treat
that state as incomplete; `download_videos=False` is useful for metadata-only or
non-visual inspection, not as proof that visual samples can be read.
