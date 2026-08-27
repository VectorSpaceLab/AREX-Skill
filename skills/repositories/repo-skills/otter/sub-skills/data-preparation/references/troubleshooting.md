# Data preparation troubleshooting

Use this guide when MIMIC-IT validation, JSON/parquet conversion, Convert-It planning, or Syphus preflight fails.

## YAML failures

### Unexpected group

Error shape: `Unexpected category 'X'`.

Fix: use only these top-level groups:

- `IMAGE_TEXT`
- `TEXT_ONLY`
- `VIDEO_TEXT`
- `IMAGE_TEXT_IN_CONTEXT`

If a group has no datasets, write `GROUP: {}` rather than leaving it blank.

### Dataset entry is not an object

Fix: each dataset name must map to a dictionary of fields. This is invalid:

```yaml
IMAGE_TEXT:
  COCO
```

Use:

```yaml
IMAGE_TEXT:
  COCO:
    mimicit_path: /data/coco_instructions.json
    images_path: /data/coco.parquet
    num_samples: -1
```

### Missing path

The loader checks every field ending in `_path`. Do not include optional path fields with an empty string. Omit optional fields instead.

For `TEXT_ONLY`, omit `images_path` unless the dataset genuinely uses images.

### `num_samples` is not an integer

Use integer values only. Quoted numbers may parse as strings and fail validation. Prefer:

```yaml
num_samples: -1
```

not:

```yaml
num_samples: "-1"
```

## Instruction JSON failures

### Missing top-level `data`

Instruction JSON must be:

```json
{"data": {"ID": {"instruction": "...", "answer": "..."}}}
```

not a bare list or a bare id mapping.

### Missing `instruction` or `answer`

Every sampled record must have string `instruction` and `answer` fields. Empty strings are technically strings but usually indicate bad generated data and should be reviewed.

### Broken `rel_ins_ids` or train config

- `rel_ins_ids` should be a list of instruction ids.
- `train_config_path` should map instruction id to a list of related instruction ids.
- Related ids should exist in the same instruction JSON unless intentionally supplied by a merged dataset.

## Image parquet/JSON failures

### Parquet missing `base64`

The loader expects `images.loc[image_id]["base64"]`. Recreate the parquet with a `base64` column and image ids as the index.

### Image id not found

A multimodal instruction references an image id that is absent from the image table. Fix by regenerating the image parquet/JSON, correcting instruction ids, or removing the bad instruction record.

### Duplicate image ids

Duplicate parquet indexes can make `images.loc[id]` return multiple rows. Deduplicate image ids before training.

### Base64 decode errors

Common causes:

- missing padding;
- URL-safe base64 versus standard base64 mismatch;
- base64 string wraps with whitespace;
- value is a list instead of a string;
- bytes are not a valid image.

The converter accepts list values by using the first element and can validate sample payloads:

```bash
python ../scripts/convert_base64_json_to_parquet.py images.json images.parquet --validate-sample 16
```

### JSON image file is too large

Legacy JSON requires loading the whole object into memory. Convert to parquet in a controlled environment, keep partition sizes below roughly 2 GB, and do not pass giant JSON directly to training when parquet is available.

## Group-specific loader failures

### `TEXT_ONLY` still asks for images

Omit `images_path` and ensure the dataset is under `TEXT_ONLY`. The loader creates a zero image placeholder for text-only samples.

### `VIDEO_TEXT` has too few frames

The loader resamples frame ids to the configured frame count. Ensure each record has enough ordered image ids or choose a lower frame count in the training configuration.

### `IMAGE_TEXT_IN_CONTEXT` has missing related examples

This group inserts images for context examples too. Validate both target and related instruction image ids.

### Unsupported `images_path` extension

Supported image asset extensions are `.parquet` and `.json`. Other extensions trigger a hard failure in the loader. Convert to parquet first.

## Convert-It issues

### Output filename mismatch

Use adapter short names to identify outputs: `LA`, `DC`, `VST`, `TVC`, `SN`, `SD`, `CGD`, and `E4D`. TV Captions may be documented elsewhere as `TV`, but the inspected adapter short name is `TVC`.

### Not enough DenseCaptions videos

The DenseCaptions adapter rejects very small video folders. Use a real source dataset or a custom fixture adapter for tests.

### Missing paired Spot-the-Difference images

Pairs must include both base id and `_2` image. Review the missing-file log and regenerate or filter missing pairs.

## Syphus issues

### Missing `litellm`

Syphus imports `litellm.completion` at file import time. Install the optional dependency in the active environment before real Syphus calls, or use only no-network validation.

### Missing API key or engine

Check:

```bash
python ../scripts/check_syphus_env.py --dataset-name video.DenseCaptions
```

Remote providers usually require `OPENAI_API_KEY` and a provider-specific `OPENAI_API_ENGINE`. Local providers may use an unauthenticated local base URL, but the user must confirm that this is intended.

### Rate limit or transient API errors

Reduce `num_threads`, keep partial output directories, and resume carefully. Do not delete valid partial outputs unless the user asks.

### Invalid generated format

Inspect `invalid_output.json` and prompt examples. Normalize valid outputs into MIMIC-IT instruction JSON before training.

## When to route elsewhere

- Data validates and the user wants to launch training: route to [training](../../training/SKILL.md).
- The user asks to run a model on a prepared sample: route to [model-inference](../../model-inference/SKILL.md).
- The user asks to evaluate benchmarks: route to [benchmark-evaluation](../../benchmark-evaluation/SKILL.md).
