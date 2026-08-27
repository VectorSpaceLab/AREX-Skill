# Dataset API reference

The public imports below are exported from `lerobot.datasets` in the current
package. Run them in the prepared LeRobot environment; the signatures here are
for planning and the installed package remains authoritative.

## `LeRobotDataset`

```python
LeRobotDataset(
    repo_id: str,
    root: str | Path | None = None,
    episodes: list[int] | None = None,
    episode_filter: Callable[[dict], bool] | None = None,
    image_transforms: Callable | None = None,
    delta_timestamps: dict[str, list[float]] | None = None,
    tolerance_s: float = 1e-4,
    revision: str | None = None,
    force_cache_sync: bool = False,
    download_videos: bool = True,
    video_backend: str | None = None,
    return_uint8: bool = False,
    depth_output_unit: str = "mm",
    batch_encoding_size: int = 1,
    rgb_encoder: RGBEncoderConfig | None = None,
    depth_encoder: DepthEncoderConfig | None = None,
    encoder_threads: int | None = None,
    streaming_encoding: bool = False,
    encoder_queue_maxsize: int = 30,
    *, token: str | bool | None = None,
)
```

Use `root` for an exact local root. Without it, the package checks its managed
cache and may download from the Hub. `episodes` filters to episode indices;
`episode_filter` receives episode metadata rows and intersects with `episodes` if
both are supplied. `download_videos=False` excludes video files from a download;
it does not make video samples decodable. `video_backend` defaults to a safe
platform choice; PyAV is the fallback decoder in supported paths. `return_uint8`
controls RGB video output. `depth_output_unit` controls returned depth values.

Useful properties and methods:

- `len(ds)`, `ds[i]`, `ds[start:stop]`: random-access frames or a bounded list for
  a slice; reads return dictionaries of tensors plus the task string.
- `ds.meta`: `LeRobotDatasetMetadata`; `ds.features`, `ds.fps`, `ds.num_frames`,
  `ds.num_episodes`, `ds.root`, `ds.hf_dataset`, and `ds.absolute_to_relative_idx`.
- `ds.select_columns(names)`: a Hugging Face `datasets.Dataset` view for selected
  raw columns; `ds.get_raw_item(i)` skips video decoding, delta expansion, and
  image transforms.
- `ds.set_image_transforms(callable_or_none)` and
  `ds.clear_image_transforms()` change read-time image augmentation.
- `ds.finalize()`: idempotently flushes/ closes writers; required for write mode.
- `ds.push_to_hub(...)`: creates/uploads a Hub dataset and is always an explicit
  network side effect.

The class is also a writer facade when created with `create()` or `resume()`.
Calling `add_frame`, `save_episode`, or `clear_episode_buffer` on an ordinary
read-only instance raises a writer-mode error. Reading a dataset still in write
mode before `finalize()` raises a read guard error.

## Creation and resume

```python
LeRobotDataset.create(
    repo_id, fps, features, root=None, robot_type=None,
    use_videos=True, tolerance_s=1e-4,
    image_writer_processes=0, image_writer_threads=0,
    video_backend=None, batch_encoding_size=1,
    rgb_encoder=None, depth_encoder=None,
    metadata_buffer_size=10, streaming_encoding=False,
    encoder_queue_maxsize=30, encoder_threads=None,
    video_files_size_in_mb=None, data_files_size_in_mb=None,
)
```

`create()` makes a new root and a writer. Add a complete frame with `task`, call
`save_episode()` for each nonempty episode, then `finalize()`. `resume()` has the
same writer controls but requires an explicit `root`; this avoids corrupting the
revision-safe shared cache. Do not reuse an existing root with `create()`.

## `LeRobotDatasetMetadata`

```python
LeRobotDatasetMetadata(
    repo_id, root=None, revision=None, force_cache_sync=False,
    metadata_buffer_size=10, *, repo_type="dataset", token=None,
)
```

`repo_type="bucket"` is for HF Storage Bucket metadata and is consumed by
streaming workflows. Important properties are `info`, `features`, `stats`,
`tasks`, `episodes`, `fps`, `total_episodes`, `total_frames`, `total_tasks`,
`image_keys`, `video_keys`, `depth_keys`, `camera_keys`, `shapes`, `names`,
`data_path`, `video_path`, and chunk settings. `filter_episodes(predicate,
 candidates=None)` returns sorted episode indices. `get_data_file_path(ep)` and
`get_video_file_path(ep,key)` resolve the authoritative shard. `ensure_readable()`
reloads episode metadata after a write. `get_task_index(text)` and
`save_episode_tasks(tasks)` manage task registration; duplicate task strings in a
new task list are rejected.

## `StreamingLeRobotDataset`

```python
StreamingLeRobotDataset(
    repo_id, root=None, episodes=None, image_transforms=None,
    delta_timestamps=None, tolerance_s=1e-4, revision=None,
    force_cache_sync=False, streaming=True, buffer_size=1000,
    max_num_shards=16, seed=42, rng=None, shuffle=True,
    return_uint8=False, depth_output_unit="mm", *,
    repo_type="dataset", token=None,
)
```

It is an `IterableDataset`; use `for item in ds`, not integer indexing. It reads
Parquet via the Hugging Face datasets streaming interface, maintains bounded
look-back/look-ahead buffers for delta windows, and shuffles with a bounded frame
buffer. `root` means local data for a normal dataset; for a bucket it is a metadata
cache while data/video remain remote. `repo_type="bucket"` requires
`streaming=True`. A stream can still fail on a video decoder when a visual key is
requested; a successful Parquet iteration alone proves only tabular access.

## Factory and tools

`make_dataset(train_cfg)` builds either random-access or streaming data from the
training config, resolving policy delta indices and optional image transforms.
`resolve_delta_timestamps(policy_cfg, meta, rename_map=None)` converts frame
indices to seconds and fails if an explicit image history has no matching image
feature. `make_train_eval_datasets` holds out the last ceiling fraction per task.

Exported operation functions and their core signatures are:

```python
delete_episodes(dataset, episode_indices, output_dir=None, repo_id=None)
split_dataset(dataset, splits, output_dir=None)
merge_datasets(datasets, output_repo_id, output_dir=None,
               concatenate_videos=True, concatenate_data=True)
modify_features(dataset, add_features=None, remove_features=None,
                output_dir=None, repo_id=None)
add_features(dataset, features, output_dir=None, repo_id=None)
remove_feature(dataset, feature_names, output_dir=None, repo_id=None)
modify_tasks(dataset, new_task=None, episode_tasks=None, task_replacements=None)
recompute_stats(dataset, skip_image_video=True, relative_action=False,
                relative_exclude_joints=None, chunk_size=50, num_workers=0)
convert_image_to_video_dataset(dataset, output_dir=None, repo_id=None,
                rgb_encoder=None, depth_encoder=None, episode_indices=None,
                num_workers=4, max_episodes_per_batch=None,
                max_frames_per_batch=None)
reencode_dataset(dataset, output_dir=None, repo_id=None, rgb_encoder=None,
                depth_encoder=None, num_workers=0, encoder_threads=None)
```

These functions generally create output datasets except `modify_tasks`, which
rewrites task-related files in place. Validate compatibility and output paths before
calling any of them.
