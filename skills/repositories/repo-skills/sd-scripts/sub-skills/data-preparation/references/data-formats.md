# sd-scripts Data Formats

## Dataset Config Shape

sd-scripts accepts a dataset config through `--dataset_config`. JSON and TOML are supported, but TOML is the practical format. A config has three precedence levels:

1. `[general]`: defaults for all datasets and subsets.
2. `[[datasets]]`: per-dataset settings such as `resolution`, `batch_size`, bucketing, and validation split.
3. `[[datasets.subsets]]`: per-directory or per-metadata settings such as `image_dir`, `metadata_file`, captions, repeats, and masking flags.

Lower levels override higher levels for options available at both levels. For example, subset `keep_tokens` overrides dataset `keep_tokens`, which overrides `[general].keep_tokens`.

## Dataset and Subset Modes

Mode is selected per `[[datasets]]` block by the keys present in all of its subsets:

- DreamBooth subset: has `image_dir` and does not have `metadata_file`.
- Fine-tuning subset: has `metadata_file`; `image_dir` is optional only when every metadata image path is absolute or cache-only, but it is recommended and required for relative image paths.
- ControlNet subset: has `image_dir` and `conditioning_data_dir`; conditioning images must match training image basenames.

Do not mix subset modes inside one `[[datasets]]` block. If one subset has `metadata_file` and another does not, sd-scripts rejects the config with a DreamBooth/fine-tuning mixing error. Put the modes in separate `[[datasets]]` blocks only when the selected training script supports both.

## Minimal DreamBooth TOML

```toml
[general]
shuffle_caption = true
caption_extension = ".txt"
keep_tokens = 1

[[datasets]]
resolution = [512, 512]
batch_size = 2
enable_bucket = true
bucket_reso_steps = 64

  [[datasets.subsets]]
  image_dir = "train/character"
  class_tokens = "sks character"
  num_repeats = 10

  [[datasets.subsets]]
  image_dir = "train/regularization"
  class_tokens = "person"
  is_reg = true
  num_repeats = 1
```

DreamBooth images are read directly under `image_dir`. Captions are read from sibling files with `caption_extension`; if a caption file is missing, `class_tokens` is used when present, otherwise training continues with an empty caption and a warning.

## Minimal Fine-tuning TOML

```toml
[general]
shuffle_caption = true
caption_separator = ", "

[[datasets]]
resolution = 768
batch_size = 1
enable_bucket = true
min_bucket_reso = 256
max_bucket_reso = 1536
bucket_reso_steps = 64

  [[datasets.subsets]]
  image_dir = "train/images"
  metadata_file = "train/metadata.jsonl"
  num_repeats = 1
```

Fine-tuning subsets are selected by `metadata_file`. Relative `metadata_file` and `image_dir` values in the dataset config follow the process working directory used to launch sd-scripts, so run from a deliberate project root or use absolute paths. Metadata image paths inside the metadata file are resolved against `image_dir` when they are relative. If a relative metadata image path appears and `image_dir` is absent, loading fails.

## Metadata JSON

A `.json` metadata file is one object keyed by image path. Each value is an object. sd-scripts reads only `caption`, `tags`, and `image_size`; other fields are ignored.

```json
{
  "001.png": {
    "caption": "a cat sitting on a sofa",
    "tags": "cat, sofa, indoor",
    "image_size": [1024, 768]
  },
  "nested/002.jpg": {
    "caption": "a dog running on a beach"
  }
}
```

## Metadata JSONL

A `.jsonl` file has one JSON object per line. `image_path` is required per line.

```jsonl
{"image_path":"001.png","caption":"a cat sitting on a sofa","image_size":[1024,768]}
{"image_path":"002.jpg","tags":"dog, beach","width":768,"height":1024}
```

`width` plus `height` is accepted as an alternative to `image_size`; when both are present, width/height wins. `tags` must be a string, not an array.

## Caption and Tag Combination

For fine-tuning metadata, sd-scripts combines `caption` and `tags` based on subset caption options:

- Default mode: if `tags` is non-empty, append it to `caption` using `caption_separator` (default comma). If `caption` is empty, tags become the caption.
- `enable_wildcard = true`: `tags` newlines are converted to `caption_separator`, then appended to each non-empty caption line. If no caption lines exist, tags are used alone.

For DreamBooth, captions come from sidecar caption files. With wildcard mode, non-empty caption file lines are preserved as separate alternatives; without wildcard mode, the first line is used.

## Image Size and Cache Resolution

`image_size = [width, height]` is optional but strongly recommended in fine-tuning metadata. When absent, sd-scripts tries to infer size from a matching latents cache file and then from the source image. If neither image nor cache exists, the entry cannot train.

Supported source image extensions include common PNG/JPEG/WebP/BMP variants, plus optional AVIF/JPEG-XL support when the relevant Python packages are installed.

## Validation Split Precedence

Validation can be configured from CLI or config, but config values take precedence over the CLI `--validation_split`. In the current dataset blueprint path, validation dataset construction uses the dataset-level `validation_split` value. Keep `validation_split` on `[[datasets]]` for predictable behavior; do not rely on subset-level validation split unless you have verified the exact script path.

```toml
[[datasets]]
resolution = 1024
validation_split = 0.1
validation_seed = 42

  [[datasets.subsets]]
  image_dir = "train/images"
  caption_extension = ".txt"
```

DreamBooth regularization subsets (`is_reg = true`) are not split into validation data; they remain training-only.

## Mask and Inpainting Data Notes

`alpha_mask = true` on a subset uses transparent PNG alpha as a masked-loss weight. A separate mask directory uses ControlNet-like `conditioning_data_dir` with matching basenames. These are different from `--train_inpainting`, which changes the model input and generates procedural masks during training. `--train_inpainting` requires source images and must not be combined with latent caching.
