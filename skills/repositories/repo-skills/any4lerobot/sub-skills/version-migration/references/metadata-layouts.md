# Metadata and storage layouts

Use these signatures for read-only preflight and post-conversion validation.
The names below are logical dataset-relative paths; do not assume a particular
cache or checkout location.

## v1.6 legacy signature

Expected legacy markers:

```text
meta_data/info.json
meta_data/stats.safetensors
data/<parquet files>
videos*/<camera>_episode_<episode_index six digits>.mp4   # when video exists
```

The v1.6→v2.0 converter loads parquet with the `datasets` library, requires
contiguous episode indices `0..N-1`, and discovers features from the parquet
schema. It treats scalar values, fixed sequences, images, and `VideoFrame`
columns differently. When sequence feature names are not supplied, it uses
synthetic `motor_0`, `motor_1`, … names; do not accept those names for a known
robot without an explicit review. `robot_config` only supports the source
implementation's `aloha`/`koch` branch unless a direct config is supplied.

## v2.0 and v2.1 legacy layout

The v2 layout uses metadata files and one parquet per episode:

```text
meta/info.json
meta/stats.json                         # v2.0 aggregate stats
meta/episodes_stats.jsonl               # v2.1 per-episode stats
meta/tasks.jsonl
meta/episodes.jsonl
meta/episodes/<optional v3-only no>     # should not be required in v2.x
data/chunk-000/episode_000000.parquet
videos/chunk-000/<camera>/episode_000000.mp4   # if video features exist
```

The exact path templates are carried in `info.json` (`data_path` and
`video_path`). In v2.0→v2.1, data/video files are not the main physical
conversion; per-episode statistics are computed by sampling video frames and
reading each episode's data. Aggregate statistics are compared with tolerances
(approximately `5e-6/6e-5` for non-video and `1e-2/1e-2` for video in the
reference check). A failed check is a data-quality stop, not a reason to delete
old stats.

In v2.1→v2.0, `episodes_stats.jsonl` is replaced by aggregate `stats.json`.
The source implementation deletes the old `stats.json` before writing it and,
if requested, deletes episode stats locally and on the Hub. Keep both files in
a backup until the target reader passes.

## v3.0 consolidated layout

v3.0 consolidates multiple episodes into size-bounded files and stores typed
metadata:

```text
meta/info.json
meta/tasks.parquet
meta/episodes/chunk-000/file-000.parquet
meta/episodes_stats.jsonl                 # intermediate/legacy marker; may be removed by v3 writer
# v3 episode statistics are also represented as flattened columns in meta/episodes files

data/chunk-000/file-000.parquet
videos/<camera>/chunk-000/file-000.mp4
images/                                      # ancillary directory, if present
```

The v2.1→v3.0 reference transforms the following conceptual records:

- `data/chunk-*/episode_*.parquet` → size-bounded `data/chunk-*/file_*.parquet`
- `videos/chunk-*/<camera>/episode_*.mp4` →
  `videos/<camera>/chunk-*/file_*.mp4`
- `episodes.jsonl` → `meta/episodes/chunk-*/file-*.parquet`
- `tasks.jsonl` → `meta/tasks.parquet`
- `episodes_stats.jsonl` → flattened stats columns in episode metadata
- `meta/info.json` is updated to `codebase_version: "v3.0"`, removes
  `total_chunks`/`total_videos`, and adds data/video file-size fields.

The v3 data episode records include `data/chunk_index`, `data/file_index`,
`dataset_from_index`, and `dataset_to_index`. Video episode records include
`videos/<key>/chunk_index`, `file_index`, `from_timestamp`, and
`to_timestamp`. The metadata rows must agree across all cameras and with the
source episode index.

## v3.0 → v2.1 reverse layout

The reverse converter reads `meta/episodes/chunk-*/file-*.parquet`, loads
`meta/tasks.parquet`, and uses the data/video index columns to slice files:

```text
meta/info.json                         # codebase_version v3.0 input
meta/tasks.parquet
meta/episodes/chunk-000/file-000.parquet

data/chunk-000/file-000.parquet
videos/<camera>/chunk-000/file-000.mp4
```

It writes a new v2.1 tree:

```text
meta/info.json                         # codebase_version v2.1
meta/tasks.jsonl
meta/episodes.jsonl
meta/episodes_stats.jsonl
meta/stats.json                         # not normally reconstructed by this route
data/chunk-000/episode_000000.parquet
videos/chunk-000/<camera>/episode_000000.mp4
images/                                  # copied when present
```

The reverse `info.json` restores the legacy path templates, removes v3 sizing
hints, removes per-feature `fps` entries for non-video features, restores
`total_chunks`, and computes `total_videos`. Episode stats are filtered to the
legacy keys `mean`, `std`, `min`, `max`, and `count`; v3-only statistics must
not be silently presented as v2.1-compatible.

## Static and synthetic checks

Before any write, a checker should assert:

- exactly one recognized source version, expected metadata root, and matching
  `codebase_version`;
- `total_episodes` agrees with episode records and data slices;
- episode indices are unique, sorted, and contiguous where the route requires
  contiguity;
- each episode has positive length and valid `dataset_from_index <
  dataset_to_index` in v3;
- each task index resolves to one task string, and every episode task reference
  exists;
- every feature in `info.json` has a dtype and shape; video features have
  usable camera metadata and path entries;
- each v3 camera has the same episode count and matching episode indices;
- every referenced parquet/video path exists in a local test fixture;
- v3→v2.1 video timestamps are finite, satisfy `0 <= start < end`, and point
  to a destination with an allowed video extension;
- stats contain the required fields and numeric arrays have compatible shapes.

A synthetic fixture should contain two episodes, two tasks, one numeric feature,
and optionally one camera with two concatenated video records. It must test
metadata/path/index validation only; do not generate or transcode video in a
routine skill check.
