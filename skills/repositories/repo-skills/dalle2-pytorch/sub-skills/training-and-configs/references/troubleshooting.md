# Troubleshooting

Use this page when config validation or training launch fails. Dataset shard/key layout and credentialed trackers are intentionally routed to `../data-and-tracking/`.

## JSON or Pydantic Validation Fails

Symptoms:

- `json.JSONDecodeError`.
- Pydantic `ValidationError` for missing blocks such as `decoder`, `data`, `train`, or `tracker`.
- A nonfatal warning about Pydantic validator return values appears while an otherwise valid config parses.

Fix:

1. Run `inspect_training_config.py` for the exact kind.
2. Compare the top-level shape with the templates in `references/config-templates/`.
3. Keep `TrainSplitConfig` values simple and summing to exactly `1.0`.
4. Treat Pydantic validator warnings observed during valid parsing as warnings, not a hard failure, unless the process exits nonzero.

## `train`, `val`, and `test` Splits Do Not Sum to `1.0`

Symptom:

```text
train/val/test must sum to 1.0
```

Fix: edit the `splits` block, for example:

```json
{"train": 0.8, "val": 0.1, "test": 0.1}
```

## Decoder `image_size` / `image_sizes` Error

Symptom:

```text
either image_size or image_sizes is required, but not both
```

Fix: set exactly one of these keys in `decoder`. For cascaded UNets, prefer `image_sizes`, ordered from low resolution to high resolution and matching the UNet order.

## Decoder Missing Embeddings or CLIP

Symptoms:

- `If text conditioning, either clip or text_embeddings_url must be provided`.
- `No image embeddings source specified`.
- Assertions about redundant CLIP and embedding URL combinations.

Fix:

- If any UNet uses `cond_on_text_encodings: true`, provide either `decoder.clip` or `data.text_embeddings_url`.
- Provide an image embedding source through either `decoder.clip` or `data.img_embeddings_url`.
- Do not combine `decoder.clip` with both image and text sidecar embeddings; pick on-the-fly CLIP or precomputed embeddings.
- Do not provide `text_embeddings_url` when no UNet uses text conditioning.

## Decoder `unet_training_mask` Length Mismatch

Symptom:

```text
The unet training mask should be the same length as the number of unets
```

Fix: remove `unet_training_mask` to train all UNets, or set one boolean per configured UNet:

```json
"unet_training_mask": [true, false]
```

The decoder wrapper only trains UNets marked `true` and temporarily replaces frozen UNets with identity modules for that training task.

## Resampling Makes Epochs Infinite

Symptom: training appears to never finish an epoch when `resample_train` is true.

Fix: set `train.epoch_samples` to a finite positive integer. Also set `validation_samples` for smoke runs if validation should be bounded. Avoid enabling both `shuffle_train` and `resample_train` while debugging dataloaders.

## DeepSpeed fp16 and Learned Variance

Symptom:

```text
DeepSpeed fp16 mode does not support learned variance
```

Fix: for decoder training with DeepSpeed fp16, set:

```json
"learned_variance": false
```

If `learned_variance` is a list, set every trained UNet entry to `false`. Alternatively use non-fp16 precision or a non-DeepSpeed launcher.

## Prior `eval_timesteps` Outside Allowed Range

Symptom:

```text
all timesteps values must be between ...
```

The native prior eval loop requires each `train.eval_timesteps` value to be between `prior.sample_timesteps` and `prior.timesteps` inclusive.

Fix:

```json
"prior": {"timesteps": 1000, "sample_timesteps": 64, ...},
"train": {"eval_timesteps": [64, 1000], ...}
```

For short smoke configs, use a consistent small range such as `timesteps: 8`, `sample_timesteps: 4`, `eval_timesteps: [4, 8]`.

## Prior CLIP / Metadata Mismatch

Symptoms:

- Errors from `EmbeddingReader` about missing image embeddings or metadata.
- Attribute errors when the prior has no CLIP but the launcher passes tokenized captions.

Fix:

- For the bundled JSON prior launcher, use `condition_on_text_encodings: true`, provide a `clip` adapter, and set both `data.image_url` and `data.meta_url`.
- If you want to train from precomputed text embeddings instead of caption metadata, use a custom direct `DiffusionPriorTrainer` loop and route dataset layout details to `../data-and-tracking/`.

## `pkg_resources` Warning From CLIP Import

Symptom:

```text
pkg_resources is deprecated as an API
```

This warning can appear from the CLIP dependency during import or help commands. It was observed as nonfatal in verified config parsing. If import breaks because `pkg_resources` is missing, install a setuptools version that still provides it or otherwise repair the Python environment before rerunning validation.

## Torchmetrics Image Metric Downloads

Symptoms:

- Decoder evaluation stalls or fails while enabling `FID`, `IS`, `KID`, or `LPIPS`.
- Network access is attempted during a supposedly small run.

Fix: set all decoder `evaluate` metric blocks to `null` for smoke tests. Enable metrics only after dataset loading and checkpointing are working and downloads are allowed.

## Tracker Data Path Already Exists

Symptom:

```text
Data path ... already exists. Set overwrite_data_path to True to overwrite.
```

Fix: for disposable runs set `tracker.overwrite_data_path: true`; for resumable or production runs, choose a fresh `data_path` or intentionally configure `tracker.load`/logger resume options. Route provider-specific W&B/HuggingFace resume and credential behavior to `../data-and-tracking/`.

## Remote Data or Credential Failures

Symptoms:

- S3/fsspec loader failures.
- W&B login or run path errors.
- HuggingFace token or repo upload errors.
- EmbeddingReader cannot find captions or arrays.

Fix: switch to local/console settings while debugging training config shape, then route data layout or tracker credential work to `../data-and-tracking/`.
