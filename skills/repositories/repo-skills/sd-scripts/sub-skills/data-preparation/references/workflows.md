# Data Preparation Workflows

## Preflight Any Dataset Config

Run the bundled read-only validator before launching training:

```bash
python skills/sd-scripts/sub-skills/data-preparation/scripts/validate_dataset_inputs.py \
  --dataset-config dataset_config.toml
```

Use `--strict` when preparing production data to treat warnings as failure. Use `--metadata-root` if metadata files are intentionally outside the config directory and use relative paths that should resolve from another base.

The validator checks parseability, expected top-level keys, subset mode consistency, directory/file existence, common metadata field types, JSONL `image_path`, missing image/cache candidates, unsupported image suffixes, and likely path-resolution mistakes. It does not import sd-scripts or load models.

## DreamBooth Directory Data

1. Place images directly under each `image_dir`; avoid relying on nested folders unless a separate preprocessing step flattens or indexes them.
2. Add sidecar captions with the same basename and `caption_extension`, such as `image_001.txt`.
3. If caption files are incomplete, set `class_tokens` so missing captions get a fallback.
4. Put regularization images in their own subset with `is_reg = true`.
5. Use `num_repeats` on each subset instead of encoding repeats in folder names.

Suggested safe checks:

```bash
python skills/sd-scripts/sub-skills/data-preparation/scripts/validate_dataset_inputs.py --dataset-config dataset_config.toml --strict
```

Then route to `../training` to build the actual command.

## Fine-tuning Metadata Data

1. Build metadata as `.json` or `.jsonl`.
2. Include `image_size = [width, height]` whenever possible so bucketing does not need to open every image.
3. Keep `tags` as a string. Put all freeform text in `caption` if tag/caption merging is not needed.
4. Set `image_dir` whenever metadata image paths are relative.
5. Keep all fine-tuning subsets in a dataset block metadata-based; do not mix a directory-only subset into the same dataset.

Minimal JSONL entry:

```jsonl
{"image_path":"001.png","caption":"subject token, red dress","image_size":[1024,1024]}
```

## Caption and Tag Generation Utilities

sd-scripts includes caption/tag utilities under its fine-tuning scripts. They are useful but not safe as automatic validation because they can load large models, download weights, and write caption or metadata files.

Common patterns:

- BLIP captions: run a captioning script over an image directory, producing sidecar text files or metadata that can be merged later.
- WD14 tags: run a tagger with ONNX or TensorFlow prerequisites; output sidecar `.txt` tag files with optional tag filtering/replacement.
- Merge utilities: combine generated captions/tags into metadata JSON.
- Cleanup utilities: normalize or remove unwanted caption/tag text before metadata is consumed by training.

Before running these tools, confirm model download location, output extension, overwrite/append behavior, recursion, batch size, and GPU/CPU backend requirements with the user.

## Resize and Bucketing Prep

Prefer leaving source images untouched and using sd-scripts bucketing:

```toml
[[datasets]]
resolution = [1024, 1024]
enable_bucket = true
min_bucket_reso = 256
max_bucket_reso = 1536
bucket_reso_steps = 64
bucket_no_upscale = false
```

Use an image resizing/copying utility only when the user explicitly wants a derived image set. Treat resize tools as mutating or copying preprocessing, not validation. If resizing occurs, validate the new derived dataset config afterward.

Use `skip_image_resolution` to exclude images whose original area is too small for a higher-resolution dataset:

```toml
[[datasets]]
resolution = 1024
skip_image_resolution = [768, 768]
```

## Latent Cache Workflow

Latent cache tools load a VAE/model stack and write `.npz` files. They are appropriate only after the data config is stable.

Typical safe sequence:

1. Validate TOML and metadata with the bundled validator.
2. Confirm the target base model family: SD 1.x/2.x, SDXL, or FLUX.
3. Build the cache command with the same `--dataset_config` and model flags that training will use.
4. Avoid latent caching when using `--train_inpainting`; inpainting training needs source images every step.
5. After caching, rerun the validator. Missing images without `image_size` may become acceptable if matching cache files exist, but this is only useful for fine-tuning/cache-only workflows.

## Text Encoder Output Cache Workflow

Text encoder output caching is only supported for SDXL and FLUX paths. It loads text encoders and writes text-encoder cache files.

Checklist:

- Use only after captions/tags are final; changing captions invalidates text caches.
- Confirm SDXL or FLUX mode.
- For FLUX, confirm CLIP-L/T5XXL model arguments and dtype/backend constraints.
- For SDXL weighted captions, keep commas out of weighted parentheses when caption shuffling or dropout is active.

## ControlNet and Masked Loss Data

ControlNet-style subsets require image/control pairs:

```toml
[[datasets]]
resolution = [512, 512]

  [[datasets.subsets]]
  image_dir = "train/images"
  conditioning_data_dir = "train/controls"
  caption_extension = ".txt"
```

The conditioning directory must contain files with basenames matching the training images. Extra conditioning images may only warn; missing conditioning images abort.

For masked loss by alpha channel:

```toml
[[datasets.subsets]]
image_dir = "train/png_with_alpha"
caption_extension = ".txt"
alpha_mask = true
```

For explicit mask images, use matching basenames under `conditioning_data_dir`. The mask should match the source image size; white means train, black means ignore, and grayscale gives proportional loss weight.

## Inpainting Training Data

Inpainting training uses ordinary DreamBooth or fine-tuning data, but the training command includes `--train_inpainting`. No mask files are required because masks are generated procedurally during training. Do not enable latent cache flags with inpainting training.

When sample prompts are used during inpainting training, each prompt line that should produce a sample needs an `--i` reference image directive; generation prompt handling belongs in `../generation`.
