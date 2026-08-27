# MIMIC-IT data formats for Otter

This reference is the self-contained operating contract for data files consumed by Otter's MIMIC-IT loader.

## Training data YAML

A training YAML is a mapping from task group to named datasets. The recognized groups are exactly:

- `IMAGE_TEXT`
- `TEXT_ONLY`
- `VIDEO_TEXT`
- `IMAGE_TEXT_IN_CONTEXT`

Use `{}` for an intentionally empty group. A blank group value becomes `null` in YAML and is not iterable by the loader.

```yaml
IMAGE_TEXT:
  EXAMPLE_CAPTIONING:
    mimicit_path: /data/example/example_instructions.json
    images_path: /data/example/example_images.parquet
    num_samples: -1
    task_description:
      - "Answer the question using the image."
TEXT_ONLY: {}
VIDEO_TEXT: {}
IMAGE_TEXT_IN_CONTEXT: {}
```

### Dataset entry fields

| Field | Required? | Loader behavior |
|---|---:|---|
| `mimicit_path` | Yes | Must point to an instruction JSON with a top-level `data` object. The preloader checks that every value whose key ends in `_path` exists. |
| `images_path` | Required for `IMAGE_TEXT`, `VIDEO_TEXT`, and `IMAGE_TEXT_IN_CONTEXT`; omit for `TEXT_ONLY` | Supports `.parquet` and legacy `.json`. Parquet is preferred. Unsupported extensions drop into a hard loader failure. |
| `train_config_path` | Optional | If supplied, must point to a JSON object mapping instruction id to a list of related instruction ids. If omitted and `populate_rel_ins` is enabled, the loader uses each record's `rel_ins_ids`; otherwise it uses empty context lists. Do not include this key with an empty string because path preflight treats empty `_path` values as missing paths. |
| `num_samples` | Strongly recommended | Must be an integer. `-1` means use all. Positive values downsample or upsample deterministically from instruction ids. Current loader behavior also treats `0` like use-all, but `-1` is clearer and should be preferred. |
| `task_description` | Optional | A string or list of strings describing the task. During sampling, a non-empty list may be randomly selected and prepended when training uses task descriptions. |

Path values may be absolute or relative to the process working directory used for validation/training. Prefer paths that will remain valid for the later training job.

## Instruction JSON

The instruction file must contain a top-level `data` object. A minimal multimodal entry is:

```json
{
  "meta": {"version": "0.0.1", "time": "2023-10-29", "author": "dataset-owner"},
  "data": {
    "EX_INS_000001": {
      "instruction": "What is shown in the image?",
      "answer": "A small test image.",
      "image_ids": ["EX_IMG_000001"],
      "rel_ins_ids": []
    }
  }
}
```

A text-only entry may omit `image_ids`, but should still provide `instruction`, `answer`, and `rel_ins_ids` for consistent validation.

### Required record keys

| Key | Type | Notes |
|---|---|---|
| `instruction` | string | Cleaned by the loader before formatting. |
| `answer` | string | Cleaned by the loader before formatting. |
| `image_ids` | list of strings | Used to index the image parquet/JSON. May be omitted or empty for `TEXT_ONLY`. For `VIDEO_TEXT`, ids are resampled to the configured frame count. |
| `rel_ins_ids` | list of strings | Used as in-context ids when `populate_rel_ins` is enabled and no train config is supplied. |

## Image parquet and legacy image JSON

Preferred image storage is a parquet file or parquet directory whose row index is image id and whose required column is named `base64`:

```text
index            base64
EX_IMG_000001    iVBORw0KGgoAAAANSUhEUg...
```

The loader reads parquet in batches, concatenates the batches into a pandas DataFrame, and later fetches images with `images.loc[image_id]["base64"]`. This means:

- every `image_ids` value in instruction JSON must appear in the parquet index;
- duplicate image ids can make lookup ambiguous;
- large parquet files are still eventually concatenated in memory, so partitioning helps write/read robustness but does not make training memory-free;
- the base64 content should decode to image bytes accepted by Pillow and then convert to RGB.

Legacy image JSON maps image id to base64 string:

```json
{
  "EX_IMG_000001": "iVBORw0KGgoAAAANSUhEUg..."
}
```

JSON is memory-heavy and slower for large datasets. Convert it to parquet with [convert_base64_json_to_parquet.py](../scripts/convert_base64_json_to_parquet.py) before large training jobs.

## Group-specific loader behavior

| Group | Images required? | Text/image formatting behavior |
|---|---:|---|
| `IMAGE_TEXT` | Yes | Inserts image tokens for the first instruction in a conversation, then appends related instruction-answer turns if present. |
| `TEXT_ONLY` | No | Creates a zero image tensor placeholder and formats text without image placeholders. |
| `VIDEO_TEXT` | Yes | Treats `image_ids` as ordered frames and resamples them to the configured frame count. |
| `IMAGE_TEXT_IN_CONTEXT` | Yes | Inserts image placeholders for in-context examples as well as the target instruction. |

The dataset object tokenizes formatted text, adds BOS/EOS tokens, constructs `patch_images`, and collates samples into `net_input.input_ids`, `net_input.attention_masks`, and optionally `net_input.patch_images`.

## Validation checklist

Before routing to training:

1. YAML contains only recognized groups, and every non-empty group maps dataset name to object.
2. Every dataset has `mimicit_path`; every non-text group has `images_path`.
3. Every `_path` value exists and is a file or directory expected by the field.
4. Every `num_samples` value is an integer.
5. Instruction JSON has top-level `data`; sampled entries have `instruction` and `answer` strings.
6. Multimodal `image_ids` are present and link to rows in the image parquet/JSON.
7. Parquet image assets expose a `base64` column.
8. `train_config_path`, when provided, maps known instruction ids to lists of known related instruction ids.

Use [validate_mimicit_yaml.py](../scripts/validate_mimicit_yaml.py) for automated checks.
