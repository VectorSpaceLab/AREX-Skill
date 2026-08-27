# SimpleTuner dataloader schema

SimpleTuner's dataloader is selected by the training option `data_backend_config` and is normally a JSON file named like `multidatabackend.json`. The runtime shape is an array of dataset backend objects. Some WebUI/service code may wrap the same array as `{ "datasets": [...] }`; unwrap that before handing the file to training unless that caller explicitly expects the wrapper.

Use the bundled validator for structural mistakes that are expensive to discover during trainer startup:

```bash
python skills/disco/simple-tuner/sub-skills/data-and-config/scripts/validate_dataloader_config.py \
  --input config/multidatabackend.json --expect-training-set
```

## Dataset object essentials

| Field | Meaning | Notes |
|---|---|---|
| `id` | Stable unique dataset id. | Keep it stable across runs because caches and state are keyed by it. Duplicate ids are invalid. |
| `type` | Storage backend type. | Common values: `local`, `aws`, `memory`, `csv`, `huggingface`, `webshart`. Defaults are code-path dependent; set it explicitly. |
| `dataset_type` | What kind of data/cache this object represents. | For omitted values, SimpleTuner treats storage backends such as local/AWS/CSV/HF/Webshart as image-like primary data. Prefer explicit values. |
| `disabled` / `disable` | Skip this dataset. | Both spellings are accepted. Disabled datasets do not satisfy training-set readiness. |
| `train_batch_size` | Per-dataset microbatch override. | Applies only to independently sampled primary datasets (`image`, `video`, `audio`, and source-code caption datasets). It does not create an optimizer-sample count for auxiliary `conditioning`. |
| `probability` | Relative sampling weight. | Usually leave unset unless mixing datasets intentionally. |
| `repeats` | Extra epoch repeats. | SimpleTuner uses `0` for no repeats; this differs from some other LoRA training tools. |
| `start_epoch`, `start_step`, `end_epoch`, `end_step` | Curriculum schedule. | At least one enabled primary dataset must be available at startup (`start_epoch <= 1` and `start_step <= 1`, or omitted). |

## Dataset type values covered here

| `dataset_type` | Role | Typical required data path/cache fields |
|---|---|---|
| `image` | Primary image training samples. | `instance_data_dir` for local data, `cache_dir_vae` for VAE latents, captions/metadata fields. |
| `video` | Primary video training samples. | `instance_data_dir`, `cache_dir_vae`, and a `video` block for frame counts/bucketing when not using defaults. May carry an `audio` block for S2V auto-split. |
| `audio` | Primary audio training samples. | `instance_data_dir`, `cache_dir_vae`, and an `audio` block for duration buckets, channels, lyrics, and truncation. |
| `text_embeds` | Text encoder cache. | `cache_dir`; exactly one enabled text cache should be the default when multiple are present. |
| `image_embeds` | VAE latent cache storage. | Usually linked from a primary dataset with `image_embeds`; local/AWS/memory cache storage only. |
| `conditioning_image_embeds` | Cached conditioning image embeddings such as CLIP vision features. | Link from image/video datasets with `conditioning_image_embeds` or let SimpleTuner choose the default cache location. |
| `conditioning` | Paired conditioning samples for ControlNet, masks, reference images, or generated conditioning data. | `instance_data_dir`, `conditioning_type`, and often `source_dataset_id` for strict alignment. |

Source code also contains maintainer/internal dataset types such as `eval`, `caption`, `grounding`, and `distillation_cache`. Do not invent user guidance for those from this file alone; route code-change or feature-extension tasks to the owner sub-skill for that workflow.

## Backend type values

| `type` | Use for | Key fields and restrictions |
|---|---|---|
| `local` | Filesystem folders or mounted storage. | Primary and conditioning datasets use `instance_data_dir`; text caches use `cache_dir`; VAE caches use `cache_dir_vae` on the source dataset. |
| `aws` | S3-compatible object storage. | Use `aws_bucket_name`, optional `aws_data_prefix`, `aws_region_name`, `aws_endpoint_url`, and credentials. Prefer local caches for expensive encoder outputs when storage listing is slow/costly. |
| `memory` | tmpfs/RAM-disk cache acceleration. | Only valid for `text_embeds` and `image_embeds`. Requires a source `cache_dir`; `memory_filesystem_path` must not overlap that source cache. |
| `csv` | URL-list image/video manifests. | Use `csv_file`, `csv_caption_column`, `csv_url_column`, `csv_cache_dir`, `caption_strategy: "csv"`, and `metadata_backend: "csv"`. Do not use CSV for text/image embed caches. |
| `huggingface` | Hugging Face datasets. | Use `dataset_name`, `split`, `caption_strategy: "huggingface"` or `instanceprompt`, and `metadata_backend: "huggingface"`. Streaming is not compatible with SimpleTuner's full bucket/length discovery needs. |
| `webshart` | WebDataset-style tar shards via Webshart. | Use `source`, optional `metadata`, `caption_strategy: "webshart"` or `instanceprompt`, and `metadata_backend: "webshart"`. Requires a Webshart build with the metadata methods SimpleTuner expects. |

## Primary image/video/audio datasets

Primary datasets are independently sampled by the trainer. They must be enabled and usable at startup unless the task is intentionally validating a staged/curriculum plan.

Common media fields:

- `instance_data_dir`: local folder or source path/prefix for primary files.
- `cache_dir_vae`: VAE/audio latent cache location for primary datasets. Keep this separate per source dataset unless sharing is intentional and proven safe.
- `resolution` + `resolution_type`:
  - `pixel`: `resolution` is the shorter-edge pixel target.
  - `pixel_area`: user-facing square-edge area shorthand; SimpleTuner converts it internally to `area` units.
  - `area`: megapixel-style area target.
- `minimum_image_size`, `maximum_image_size`, `target_downsample_size`: filtering/downsampling controls. If `maximum_image_size` is set, `target_downsample_size` must also be set.
- `minimum_aspect_ratio`, `maximum_aspect_ratio`: aspect filter bounds.
- `crop`, `crop_style`, `crop_aspect`, `crop_aspect_buckets`: crop and bucket selection. `crop_aspect: "random"` or `"closest"` requires a bucket list.
- `vae_cache_ondemand`: encode missing VAE/audio latents during training and write them.
- `vae_cache_disable`: encode missing latents on demand but do not write new cache entries; this implies on-demand mode.

Video fields live under `video`:

- `num_frames`: target frame count.
- `min_frames`: minimum acceptable frame count; must be at least `num_frames`.
- `max_frames`: maximum scan/training frame count.
- `bucket_strategy`: `aspect_ratio` or `resolution_frames`.
- `frame_interval`: frame rounding interval for `resolution_frames` bucketing.
- `is_i2v`: image-to-video mode; some model/flavour combinations force this true.

Audio fields live under `audio`:

- `bucket_strategy`: currently duration-oriented; defaults to `duration`.
- `duration_interval`: duration bucket rounding/truncation interval in seconds; must be positive.
- `max_duration_seconds` and `min_duration_seconds`: skip clips outside duration bounds.
- `truncation_mode`: `beginning`, `end`, or `random`.
- `channels`, `sample_rate`: audio normalization settings.
- `audio_only`: explicit audio-only mode for model families that support it. LTX-2 and MiniMax-H3 can infer audio-only when all enabled media datasets are audio.

## Text embed caches

A `text_embeds` dataset stores text encoder outputs, including validation/null/default prompt embeddings that are not tied to one source image. It is not a training sample dataset.

Key rules:

- Use `cache_dir` for local/memory cache roots; for S3 caches use the AWS fields and prefix.
- If only one enabled text cache exists, SimpleTuner can mark it default internally, but set `default: true` explicitly for clarity.
- If more than one enabled text cache exists, exactly one must have `default: true`.
- `text_embeds` on an `image` or `video` dataset links that source dataset to a non-default text cache by id.
- `text_cache_ondemand: true` skips full precomputation and encodes missing embeddings during training/validation.
- `text_cache_disable: true` reads existing embeddings and encodes missing ones without writing them; it implies `text_cache_ondemand`.
- `caption_filter_list` is valid only on `text_embeds` datasets. It may be a list or a path to a filter list and supports simple removals, regex removals, and sed-style replacements.
- `write_batch_size` controls cache-write batches; `text_encoder_batch_size` controls text encoder forward batches.

## Image and conditioning image caches

- `image_embeds` stores VAE latents separately from the source dataset when the source dataset uses `image_embeds: "cache-id"`.
- `conditioning_image_embeds` stores conditioning image embeddings for models that require them. Image/video datasets may set `conditioning_image_embeds: "cache-id"`.
- `cache_dir_conditioning_image_embeds` overrides the default conditioning-image embed cache destination.
- When `conditioning_image_embeds` is unset and the model requires conditioning image embeds, SimpleTuner defaults to a cache under the run output cache area, separated from the VAE cache.
- Do not reuse `cache_dir_vae`, `cache_dir`, and `cache_dir_conditioning_image_embeds` for different cache roles unless you can explain exactly why it is safe.

## Caption and metadata strategies

| Strategy/backend | Requirements | Failure to watch |
|---|---|---|
| `textfile` | Caption `.txt` files beside media files; newlines become multiple caption variants unless `disable_multiline_split` is true. | Missing sidecars cause empty or fallback captions. |
| `filename` | Caption derived from file stem. | Good for simple demos, weak for complex datasets. |
| `instanceprompt` | `instance_prompt` supplies all captions. | Missing `instance_prompt` makes the dataset effectively uncaptioned. |
| `parquet` | `metadata_backend: "parquet"` and a `parquet` block with `path`, `filename_column`, `caption_column`, `width_column`, and `height_column`. | `caption_strategy: "parquet"` with `metadata_backend: "json"` or `"discovery"` is invalid. |
| `csv` | CSV backend with caption/url/cache columns. | CSV downloads can be slow, network-dependent, and bad URLs persist unless the manifest is cleaned. |
| `huggingface` | HF backend with `metadata_backend: "huggingface"`, `dataset_name`, and caption/image/video/audio column choices. | Streaming is not suitable because SimpleTuner needs full metadata for buckets and lengths. |
| `webshart` | Webshart backend with `metadata_backend: "webshart"`, `source`, optional `metadata`, and Webshart cache settings. | Sidecar captions may need `webshart_optimize_captions` to avoid one range read per sample. |

`caption_shuffle` is a dictionary used during text embed caching. It supports deterministic tag-order variants with `enable`, `count`, `seed`, `split_on` (`comma`, `space`, `period`), `position_start`, and `include_original`.

## Conditioning and ControlNet schema

There are two supported patterns.

### Explicit paired conditioning dataset

```json
[
  {
    "id": "train-images",
    "type": "local",
    "dataset_type": "image",
    "instance_data_dir": "datasets/controlnet/images",
    "conditioning_data": "train-canny",
    "caption_strategy": "textfile",
    "cache_dir_vae": "cache/vae/controlnet/images"
  },
  {
    "id": "train-canny",
    "type": "local",
    "dataset_type": "conditioning",
    "conditioning_type": "controlnet",
    "instance_data_dir": "datasets/controlnet/canny",
    "source_dataset_id": "train-images",
    "caption_strategy": "instanceprompt",
    "instance_prompt": "canny edge map"
  },
  {
    "id": "text-cache",
    "type": "local",
    "dataset_type": "text_embeds",
    "default": true,
    "cache_dir": "cache/text/controlnet"
  }
]
```

`conditioning_data` may be a string or an array of conditioning ids. File stems must align between source and conditioning directories for strict pairings.

### Inline generated conditioning

A source image/video dataset may include a `conditioning` object or array. SimpleTuner generates local `conditioning` datasets and links them back to the source. Common generator values include:

- `superresolution`
- `sdr` / `logc3_sdr`
- `jpeg_artifacts`
- `depth` / `depth_midas`
- `random_masks` / `inpainting`
- `canny` / `edges`
- `i2v_first_frame` for image-to-video first-frame conditioning

`conditioning_type` defaults toward strict reference behavior unless ControlNet mode overrides it to `controlnet`. For strict reference, mask, or grounding alignment, keep `source_dataset_id` traceable to the source dataset.

## Grounding and bbox annotations

For spatial grounding, add a `grounding` block to an image/video source dataset and set the training config's grounding entity limit accordingly. Local sidecar `.bbox` files may be JSON arrays, JSONL objects, or YOLO txt. Bounding boxes are normalized; optional masks point to per-entity mask images.

Auto-detecting bboxes uses model-backed Florence/SAM-style tooling and is only supported for local backends. Treat it as a model-download/GPU workflow unless the user explicitly authorizes that work.

## Hugging Face and Webshart notes

Hugging Face datasets can define nested caption columns, fallback caption columns, quality filters, and composite-image extraction. Each composite half should be a separate dataset entry so caches and captions do not collide.

Webshart datasets point at tar-shard sources plus optional metadata repositories/trees. `webshart.cache_dir` stores SimpleTuner metadata and Webshart caches. `webshart_optimize_captions` can coalesce sidecar captions into metadata once at startup, or the user can perform that step outside SimpleTuner with the Webshart CLI before training.
