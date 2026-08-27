# Data preparation recipes

Use this reference for local, deterministic data-layout work before a training launch. Do not run network downloads, model downloads, cloud operations, or training from this sub-skill unless the user explicitly requests them and the owning sub-skill confirms the runtime route.

## General preparation order

1. Choose the storage backend (`local`, `aws`, `csv`, `huggingface`, `webshart`, or cache-only `memory`).
2. Decide the source dataset type (`image`, `video`, `audio`, or `conditioning`) and cache datasets (`text_embeds`, `image_embeds`, `conditioning_image_embeds`).
3. Choose a caption/metadata strategy that matches the backend.
4. Create separate cache roots for text embeddings, VAE/audio latents, and conditioning image embeddings.
5. Validate the dataloader JSON with the bundled validator.
6. Only then pass the plan to `training-workflows` for launch or performance decisions.

## Image data and captions

For local image datasets, keep media files and captions easy to audit:

```text
datasets/portraits/
  image-0001.png
  image-0001.txt
  image-0002.jpg
  image-0002.txt
```

Caption strategies:

- `textfile`: `.txt` sidecar with the same stem as the image/video/audio file. Newlines become caption variants unless `disable_multiline_split: true`.
- `filename`: derive captions from filenames. Use for quick fixtures or simple demos, not high-quality caption corpora.
- `instanceprompt`: use `instance_prompt` for every sample. Required when intentionally ignoring stored captions.
- `parquet`: use table metadata. Pair `caption_strategy: "parquet"` with `metadata_backend: "parquet"` and a `parquet` block.
- `huggingface`: use Hugging Face columns. Pair with `type: "huggingface"` and `metadata_backend: "huggingface"`.
- `webshart`: use Webshart shard metadata. Pair with `type: "webshart"` and `metadata_backend: "webshart"`.

Caption augmentation/filtering:

- Use `caption_shuffle` on source media datasets when tag order should be randomized during text embed caching.
- Use `caption_filter_list` only on `text_embeds` datasets. It supports literal removals, regex removals, and sed-style replacements.
- Keep destructive cleanup flags (`delete_unwanted_images`, `delete_problematic_images`, `delete_nsfw_images`) disabled unless the user explicitly asks for deletion.

## Parquet and JSONL metadata

Use Parquet/JSONL when captions and dimensions are already tabular or when millions of sidecar files would be costly.

Required/important fields in the `parquet` block:

- `path`: table path visible to the backend.
- `filename_column`: value used to find each media file.
- `caption_column`: caption string or list column.
- `fallback_caption_column`: optional fallback captions.
- `width_column`, `height_column`: strongly recommended so SimpleTuner does not need to open every media file just to discover dimensions.
- `identifier_includes_extension`: true when filenames already include extensions.
- `bbox_column`: optional spatial annotations when grounding uses table metadata.

Use `caption_strategy: "parquet"` only with `metadata_backend: "parquet"`.

## Hugging Face datasets

Hugging Face dataset entries can be used directly when the dataset is not too large to fully inspect for buckets and lengths.

Minimal shape:

```json
{
  "id": "hf-images",
  "type": "huggingface",
  "dataset_type": "image",
  "dataset_name": "owner/dataset",
  "split": "train",
  "caption_strategy": "huggingface",
  "metadata_backend": "huggingface",
  "caption_column": "caption",
  "image_column": "image",
  "cache_dir_vae": "cache/vae/hf-images"
}
```

Important limitations:

- SimpleTuner requires full access to metadata for bucket construction. Treat streaming as unsupported for normal training plans.
- Private datasets require Hugging Face credentials; do not embed tokens in runtime docs or generated configs.
- Use `huggingface.composite_image_config` to split grid/composite samples into independent dataset entries, one entry per selected image.
- Use `huggingface.filter_func` to reduce very large datasets before bucket discovery.

For audio datasets, set `dataset_type: "audio"` and configure caption/lyrics columns under the Hugging Face block or `config` block when the dataset provides prompts and lyrics separately.

## CSV URL manifests

CSV backends are for URL-list media manifests. They are useful when local disk does not hold all images, but startup can be slow and network-dependent.

Minimal fields:

```json
{
  "id": "csv-images",
  "type": "csv",
  "dataset_type": "image",
  "metadata_backend": "csv",
  "caption_strategy": "csv",
  "csv_file": "config/dataset.csv",
  "csv_caption_column": "caption",
  "csv_url_column": "url",
  "csv_cache_dir": "cache/csv/images",
  "cache_dir_vae": "cache/vae/csv-images"
}
```

Validate or clean the URL list before training. SimpleTuner does not automatically repair a manifest full of bad URLs.

## Webshart datasets

Webshart backends load tar-sharded WebDataset-style samples and use Webshart metadata for aspect buckets and captions.

Minimal fields:

```json
{
  "id": "webshart-images",
  "type": "webshart",
  "dataset_type": "image",
  "source": "organization/dataset-shards",
  "metadata": "organization/dataset-metadata",
  "caption_strategy": "webshart",
  "metadata_backend": "webshart",
  "webshart": {
    "cache_dir": "cache/webshart/webshart-images",
    "shard_cache_gb": 25,
    "parallel_downloads": 4
  }
}
```

If captions live in shard sidecars rather than metadata, consider `webshart_optimize_captions: true` or pre-coalescing captions with Webshart tooling outside this skill. Network and Hub publishing actions are not safe default operations.

## Audio datasets and lyrics

Audio datasets use `dataset_type: "audio"` plus an `audio` block. Duration-aware buckets prevent long clips from starving ranks.

```json
{
  "id": "songs",
  "type": "local",
  "dataset_type": "audio",
  "instance_data_dir": "datasets/songs",
  "caption_strategy": "textfile",
  "cache_dir_vae": "cache/audio/vae/songs",
  "audio": {
    "bucket_strategy": "duration",
    "duration_interval": 3.0,
    "max_duration_seconds": 90,
    "channels": 2,
    "truncation_mode": "beginning"
  }
}
```

Notes:

- ACE-Step and MiniMaxMusic-style datasets may use lyrics sidecars such as `.lyrics` files in addition to prompt captions.
- Hugging Face audio datasets can specify prompt/caption fields and a lyrics column.
- `audio.max_duration_seconds` filters long clips as `too_long`.
- `audio.duration_interval` controls bucket rounding/truncation. If buckets are empty or uneven, reduce max duration or adjust the interval.

## S2V audio auto-split from video

For Sound-to-Video training, a video dataset can carry an `audio` block. When the model requires S2V, SimpleTuner defaults `audio.auto_split` to true even if the block is absent. When the model merely supports audio, an explicit `audio` block opts in and defaults `auto_split` to true.

```json
{
  "id": "training-videos",
  "type": "local",
  "dataset_type": "video",
  "instance_data_dir": "datasets/videos",
  "cache_dir_vae": "cache/vae/videos",
  "audio": {
    "auto_split": true,
    "sample_rate": 16000,
    "channels": 1,
    "allow_zero_audio": false,
    "duration_interval": 3.0
  }
}
```

SimpleTuner generates an audio dataset id like `training-videos_audio` and links it with `s2v_datasets`. If `s2v_datasets` is already set, auto-injection is skipped.

## Video preparation

Use a `video` block when default 5-second frame windows are not appropriate:

```json
{
  "id": "clips",
  "type": "local",
  "dataset_type": "video",
  "instance_data_dir": "datasets/clips",
  "cache_dir_vae": "cache/vae/clips",
  "video": {
    "bucket_strategy": "resolution_frames",
    "frame_interval": 25,
    "min_frames": 25,
    "max_frames": 250
  }
}
```

Warnings:

- `num_frames` creates a fixed frame target. With `resolution_frames`, fixed `num_frames` can collapse to one frame bucket and discard shorter videos.
- Some model families adjust frame counts to satisfy model constraints; do not assume arbitrary frame counts survive unchanged.
- I2V flavours may force `video.is_i2v: true` and require reference conditioning.

## ControlNet and conditioning data

Use explicit paired directories when the conditioning images are prepared before training:

```text
datasets/controlnet/images/
  sample-001.png
  sample-002.png
datasets/controlnet/canny/
  sample-001.png
  sample-002.png
```

The paired dataloader shape is shown in [dataloader-schema.md](dataloader-schema.md). File stems must match, and strict conditioning should record `source_dataset_id` on the conditioning dataset.

To generate Canny conditioning directories from images, use the bundled helper instead of the original source script:

```bash
python skills/disco/simple-tuner/sub-skills/data-and-config/scripts/make_controlnet_canny_edges.py \
  --input-dir datasets/source-images \
  --output-original-dir datasets/controlnet/images \
  --output-edges-dir datasets/controlnet/canny \
  --low-threshold 100 \
  --high-threshold 200
```

The helper has no hardcoded paths, supports `--dry-run`, refuses overwrites unless `--overwrite` is set, and sorts inputs for deterministic output.

Inline conditioning generation can avoid manual preprocessing:

```json
{
  "id": "source-images",
  "type": "local",
  "dataset_type": "image",
  "instance_data_dir": "datasets/source-images",
  "conditioning": [
    {"type": "canny", "low_threshold": 50, "high_threshold": 150},
    {"type": "random_masks", "conditioning_type": "mask"}
  ]
}
```

CPU-friendly generators include Canny edges, random masks, JPEG artifacts, and superresolution degradations. Depth/segmentation/optical-flow-style generators are model/GPU dependent; route heavy generation planning to the appropriate workflow.

## Grounding and bbox sidecars

For grounding, use a `grounding` block on the source image/video dataset and provide `.bbox` sidecars or a table/HF bbox column.

Supported `.bbox` sidecar shapes:

```json
[
  {"label": "subject", "bbox": [0.1, 0.2, 0.5, 0.8], "mask": "masks/subject.png"}
]
```

```jsonl
{"label": "subject", "bbox": [0.1, 0.2, 0.5, 0.8]}
```

```text
0 0.3 0.5 0.4 0.6
```

Auto-detection uses model-backed components and requires local datasets. Do not run it as a default data-prep step.

## Source script decisions

- Adapted: `scripts/datasets/controlnet/create_canny_edge.py` became the bundled `scripts/make_controlnet_canny_edges.py` with argparse, no hardcoded paths, dry-run and overwrite controls.
- Reference-only: `scripts/datasets/fetch_lyrics.py`. It reads audio tags and can call Genius/tokenless web scraping, so it requires optional dependencies, credentials/rate limits, and network permission.
- Reference-only: `scripts/datasets/masked_loss/generate_dataset_masks.py` and `generate_dataset_masks_via_huggingface.py`. They use Florence/SAM/Gradio/Hugging Face model dependencies and can download model checkpoints or call hosted services. Summarize prerequisites rather than running them by default.
