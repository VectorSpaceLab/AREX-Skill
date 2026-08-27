# Data and configuration troubleshooting

Start with the safe validator:

```bash
python skills/disco/simple-tuner/sub-skills/data-and-config/scripts/validate_dataloader_config.py \
  --input config/multidatabackend.json --expect-training-set
```

Then use the symptom table below. Keep launch/distributed/runtime fixes in `training-workflows`; keep source-code/test/template updates in `repo-development`.

## Common symptoms

| Symptom | Likely cause | Fix |
|---|---|---|
| Config file not found for an environment | `ENV`/`SIMPLETUNER_ENV` points at a folder without the selected backend file; non-JSON `CONFIG_PATH` may not be honored the way the user expects. | Use `config/<ENV>/config.json`, `config/<ENV>/config.toml`, or `config/<ENV>/config.env`; or switch to `CONFIG_BACKEND=json` with an explicit `CONFIG_PATH`. |
| `data_backend_config` resolves to the wrong file | Mixed `--data_backend_config`, `data_backend_config`, and `DATALOADER_CONFIG` values; WebUI environment copied/rebased a dataloader path. | Resolve the active backend first, then inspect the training config's normalized dataloader path. Keep dataloader next to the environment folder when possible. |
| Empty dataset at startup | Disabled datasets, missing `instance_data_dir`, wrong backend credentials, no primary dataset, all datasets scheduled for later, or filters remove every sample. | Ensure at least one enabled immediate primary dataset exists, paths/prefixes are correct, and filters are not over-tight. |
| Files filtered as `too_small` | `minimum_image_size` is larger than actual samples, or units do not match `resolution_type`. | For `pixel`, compare shorter edge in pixels. For `area`/`pixel_area`, compare area units. Lower the threshold or prepare larger/upscaled data before training. |
| Files filtered as `too_long` | Video/audio files exceed `video.max_frames` or `audio.max_duration_seconds`. | Trim media, increase max duration/frames if hardware allows, or adjust `audio.duration_interval` / video frame bucket settings. |
| Files filtered as `metadata_missing` | Corrupt files, unsupported formats, unreadable permissions, missing table/HF metadata, or broken sidecars. | Open a few failed samples, verify table columns and file names, and rebuild metadata/cache files only after fixing source data. |
| Missing text embed cache | No enabled `text_embeds` entry and validation requires a full training set. | Add a local/AWS/memory `text_embeds` backend with `cache_dir` and `default: true`. |
| Duplicate default text caches | More than one enabled `text_embeds` dataset has `default: true`. | Keep exactly one default; link per-dataset special caches with the source dataset's `text_embeds` field. |
| No default among multiple text caches | Several enabled `text_embeds` entries exist but none is default. | Mark exactly one default. If a source dataset needs a non-default cache, set `text_embeds: "cache-id"` on that source dataset. |
| `caption_filter_list` error | Filter list placed on image/video/audio/conditioning dataset instead of `text_embeds`. | Move `caption_filter_list` to the relevant `text_embeds` cache entry. |
| Caption strategy mismatch | `caption_strategy: "parquet"` with `metadata_backend: "json"`/`"discovery"`; `huggingface` strategy on non-HF backend; `webshart` strategy on non-Webshart backend. | Make strategy and metadata backend match the storage backend. See [dataloader-schema.md](dataloader-schema.md). |
| Parquet captions missing | `parquet.path`, `filename_column`, `caption_column`, `width_column`, or `height_column` mismatch the table. | Inspect the table schema, ensure filenames/extensions match media files, and set `identifier_includes_extension` correctly. |
| Hugging Face dataset too slow or memory-heavy | Streaming is unsuitable; full metadata and bucket lengths must be known. | Filter/select a manageable subset, reduce `num_proc`, or prepare a smaller local/parquet mirror before training. |
| S3/AWS credential or listing failure | Missing bucket, region, endpoint, keys, session token, or expensive repeated listing. | Verify credentials outside training, set endpoint/region correctly, prefer local caches, and use `preserve_data_backend_cache` only when the source is stable. |
| Hugging Face credential failure | Private/gated dataset without a token or local login. | Authenticate outside generated configs; do not embed tokens into shared docs. |
| Webshart initialization failure | Missing `webshart` package, missing `source`, wrong metadata backend, or Webshart build lacks required metadata methods. | Install/verify the correct Webshart build and set `metadata_backend: "webshart"` plus `caption_strategy: "webshart"` or `instanceprompt`. |
| Memory backend misuse | `type: "memory"` on primary image/video/audio/conditioning data; overlapping `memory_filesystem_path` and source `cache_dir`; missing RAM-disk size on macOS. | Use memory only for `text_embeds` or `image_embeds`, separate mount/cache paths, and size memory storage explicitly where required. |
| Cache directory collision | Same path used for text embeds, VAE latents, conditioning image embeds, or multiple datasets unintentionally. | Use role-specific cache roots such as `cache/text/<run>`, `cache/vae/<dataset>`, and `cache/conditioning_image_embeds/<dataset>`. |
| `maximum_image_size` validation error | `maximum_image_size` set without `target_downsample_size`, or units are too large/small for `resolution_type`. | Set both fields and use the same unit family as `resolution_type`. |
| Random/closest crop bucket error | `crop_aspect` is `random` or `closest` without `crop_aspect_buckets`. | Add a list of numeric buckets or weighted bucket dictionaries. |
| Video bucket empty or too many skips | `num_frames`/`min_frames` invalid, model auto-adjusted frames, or fixed `num_frames` with `resolution_frames` leaves one bucket. | Ensure `min_frames >= num_frames`, unset fixed `num_frames` for varied frame buckets, or adjust `frame_interval`. |
| Audio duration buckets empty | `audio.max_duration_seconds` too low, `duration_interval` too coarse, no supported audio files, or S2V auto-split did not create audio data. | Inspect durations, reduce interval, trim files, or explicitly set/verify `s2v_datasets`. |
| S2V audio missing | Model requires S2V but video dataset has no generated or explicit audio dataset; `audio.auto_split` false; existing `s2v_datasets` references wrong ids. | Add `audio: {"auto_split": true}` on the video dataset or create an audio dataset and set `s2v_datasets`. |
| Conditioning source mismatch | `conditioning_data` references missing ids, conditioning stems do not match source stems, or `source_dataset_id` points to the wrong source. | Ensure referenced conditioning datasets exist, use matching stems, and set `source_dataset_id` for strict reference/mask/controlnet pairings. |
| ControlNet validation asks for conditioning block | Training config enables ControlNet but source image dataset lacks `conditioning_data` or inline `conditioning`. | Add explicit paired conditioning datasets or an inline generator such as `{"type": "canny"}`. |
| Canny helper skips files | Output files already exist and `--overwrite` was not set; unsupported image extension; OpenCV/Pillow cannot decode the input. | Use `--dry-run` to inspect, delete/regenerate intentionally with `--overwrite`, or convert images to PNG/JPEG first. |
| Grounding annotations ignored | `grounding.enabled` missing, `max_grounding_entities` not set in training config, bbox sidecars malformed, or auto-detect used on non-local backend. | Enable grounding on the source dataset, set the training grounding limit, validate `.bbox` formats, and keep auto-detect local/model-approved. |

## Duplicate default text cache case

If a dataloader has an image dataset plus two `text_embeds` entries both marked default, the expected fix is not to delete a cache blindly. Decide which cache should hold global/default prompt embeds, keep only that one with `default: true`, and point any special source dataset to the alternate cache:

```json
{
  "id": "train-images",
  "dataset_type": "image",
  "type": "local",
  "text_embeds": "special-text-cache"
}
```

The default text cache still needs to exist for validation/null prompt embeddings.

## ControlNet Canny fixture case

For a small image fixture, generate source-copy and edge directories with relative paths:

```bash
python skills/disco/simple-tuner/sub-skills/data-and-config/scripts/make_controlnet_canny_edges.py \
  --input-dir tests/fixtures/controlnet/source \
  --output-original-dir tests/fixtures/controlnet/images \
  --output-edges-dir tests/fixtures/controlnet/canny \
  --low-threshold 50 \
  --high-threshold 150
```

Then validate the dataloader references the output directories and has a single default `text_embeds` cache.

## Maintainer cross-link

If troubleshooting reveals a missing or stale dataloader field in SimpleTuner code, route to `repo-development`. Code changes must update the WebUI dataset blueprint/template surface, docs, and translations according to repository maintenance policy; do not hide schema drift inside this runtime skill.
