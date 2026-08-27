# Data Preparation Troubleshooting

## Config Fails to Parse

Symptoms:

- TOML parser error.
- Training reports invalid user config.
- Values accepted by CLI fail inside `--dataset_config`.

Fixes:

- Use quoted strings for paths, especially Windows paths.
- Use `resolution = 512` or `resolution = [512, 512]`, not mixed string/list syntax unless the exact script path accepts it.
- Keep `datasets` as an array of tables: `[[datasets]]` and nested `[[datasets.subsets]]`.
- Run the bundled validator first to isolate parse and schema-shape issues.

## DreamBooth and Fine-tuning Mixed in One Dataset

Symptom: error saying DreamBooth and fine-tuning subsets cannot be mixed in the same dataset.

Cause: within one `[[datasets]]`, some subsets have `metadata_file` and others do not.

Fix:

```toml
[[datasets]]
resolution = 512
  [[datasets.subsets]]
  image_dir = "train/db"
  caption_extension = ".txt"

[[datasets]]
resolution = 512
  [[datasets.subsets]]
  image_dir = "train/ft_images"
  metadata_file = "train/metadata.jsonl"
```

Then confirm the selected training script supports both modes. If not, choose one style.

## Missing `image_dir` or `metadata_file`

Symptoms:

- Fine-tuning metadata file not found.
- Relative metadata image path fails with `image_dir is required`.
- DreamBooth subset is ignored as not a directory.

Fixes:

- DreamBooth: every subset needs an existing `image_dir`.
- Fine-tuning: every subset needs an existing `metadata_file`; add `image_dir` when metadata paths are relative.
- Resolve relative paths from the dataset config location, not from an arbitrary shell directory.

## Metadata JSON or JSONL Is Invalid

Symptoms:

- JSON decode errors.
- JSONL load fails on one line.
- Metadata subset is skipped or has no image entries.

Fixes:

- `.json` must be one object mapping image path strings to per-image objects.
- `.jsonl` must have one object per non-empty line and each line must include string `image_path`.
- Keep `caption` and `tags` as strings.
- Keep `image_size` as `[width, height]` integers or provide integer `width` and `height` in JSONL.
- Avoid empty metadata files; sd-scripts skips empty metadata subsets.

## Images Are Missing but Metadata Exists

Symptoms:

- Validator reports metadata entries with no image or cache candidate.
- Training later fails to get image size.
- Fine-tuning paths work on one machine but not another.

Fixes:

- If metadata paths are relative, set `image_dir` and place files relative to it.
- Include file extensions where possible. sd-scripts can glob by basename, but explicit filenames are safer.
- Add `image_size` to metadata if using cache-only workflows.
- Ensure matching latent cache files exist before removing original images.

## Unsupported Image Files

Symptoms:

- Dataset has images but validator reports no supported image files.
- Training silently ignores files with unusual suffixes.

Fixes:

- Use common suffixes: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`.
- AVIF and JPEG-XL support depends on optional Python packages; convert to a common format for portability.
- Keep source images directly under `image_dir` for DreamBooth-style subsets.

## Captions Look Wrong

Symptoms:

- Captions are empty or only class tokens are used.
- Tags are duplicated or merged with unexpected punctuation.
- Wildcard captions collapse unexpectedly.

Fixes:

- DreamBooth sidecar caption files must match image basename and `caption_extension`.
- For DreamBooth without `enable_wildcard`, only the first line is used.
- For fine-tuning metadata, `tags` is appended to `caption` using `caption_separator`; set the separator deliberately.
- Keep `tags` as one string, not a JSON array.
- Be careful with `keep_tokens`, `keep_tokens_separator`, `secondary_separator`, caption dropout, and shuffling because they operate after caption/tag assembly.

## Validation Split Not Taking Effect

Symptoms:

- CLI `--validation_split` appears ignored.
- Subset-level `validation_split` does not create expected validation data.
- Regularization images appear missing from validation.

Fixes:

- Put `validation_split` on `[[datasets]]` for predictable behavior.
- Dataset config values take precedence over CLI `--validation_split`.
- Add `validation_seed` on the dataset for deterministic splitting.
- DreamBooth regularization subsets are training-only and are not split into validation.

## Cache Commands Fail or Produce Stale Caches

Symptoms:

- Latent cache command loads models but fails during dataset prep.
- Text encoder output cache rejects the model family.
- Training uses stale cache after captions changed.

Fixes:

- Run the read-only validator before cache commands.
- Use latent cache only after confirming the same model family and dataset config as training.
- Do not use latent caching with `--train_inpainting`.
- Text encoder output caching is for SDXL and FLUX paths; do not try it for SD 1.x/2.x.
- Rebuild text encoder caches after changing captions, tags, caption separators, wildcard behavior, or weighted-caption settings.

## Masked Loss and Inpainting Are Confused

Symptoms:

- User expects mask files for inpainting training.
- Latent caching is enabled with `--train_inpainting`.
- Alpha PNG mask behavior differs from explicit mask image behavior.

Fixes:

- `--train_inpainting` is a training-mode feature with procedural masks and 9-channel UNet input; no mask files are required.
- `alpha_mask = true` is masked loss from PNG alpha channel; it weights loss but does not switch the model to inpainting mode.
- Explicit mask images use matching basenames in `conditioning_data_dir`; the R channel is used and mask size should match source image size.
- Keep source images available for inpainting training.

## ControlNet Pairing Fails

Symptoms:

- Missing conditioning data assertion.
- Extra conditioning data warning.
- Conditioning image size mismatch under bucketing.

Fixes:

- Ensure every training image basename has one matching conditioning image basename.
- Remove or ignore extra conditioning images that do not correspond to training images.
- Keep control images at the same original size as their paired source images when bucketing is enabled.
- Do not set `random_crop` for ControlNet subsets.
