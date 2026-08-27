# Data Formats

## Purpose

Read this when you need the exact raw-video metadata and processed latent schema that the extraction and training flows expect.

## 1) Raw metadata input

The extractor reads a `meta_file.list` file whose lines each point to a JSON file.

Example:

```text
/path/to/0.json
/path/to/1.json
/path/to/2.json
```

Each JSON file must contain at least:

```json
{
  "video_path": "/path/to/video.mp4",
  "raw_caption": {
    "long caption": "Detailed description text of the video"
  }
}
```

Notes:

- `video_path` is the path passed to `decord.VideoReader`.
- The caption text is read from `raw_caption["long caption"]`.
- The extractor derives `video_id` from the basename of `video_path`.

## 2) Processed latent output

For each processed item, the extractor writes:

- `{output_base_dir}/{video_id}.npy`
- `{output_base_dir}/json_path/{video_id}.json`

The processed JSON contains:

```json
{
  "video_id": "example_id",
  "latent_shape": [1, 4, 33, 60, 60],
  "video_path": "/path/to/video.mp4",
  "prompt": "...",
  "npy_save_path": "/path/to/output_base_dir/example_id.npy"
}
```

The shape values come from the latent tensor and are later consumed by the training dataset loader.

## 3) Training dataset expectation

`hyvideo.dataset.video_loader.VideoDataset` reads the processed JSON directory, not the raw video files. It expects every JSON to include:

- `video_id`
- `latent_shape`
- `prompt`
- `npy_save_path`

The training loader derives `height` and `width` from `latent_shape[3]` and `latent_shape[4]`, then uses `npy_save_path` to locate the latent cache.

## 4) Bucket and stride rules

- `sample_n_frames` must respect the VAE temporal compression ratio.
- `use_stride` selects stride 2 for videos with fps >= 50, otherwise stride 1.
- `enable_multi_aspect_ratio=True` assumes the base `sample_size` is square and generates a bucket list from that seed.

## Related Files

- [`workflows.md`](workflows.md)
- [`../../../references/checkpoints.md`](../../../references/checkpoints.md)
- [`../../../references/model-overview.md`](../../../references/model-overview.md)
