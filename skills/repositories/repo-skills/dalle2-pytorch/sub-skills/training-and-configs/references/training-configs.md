# Training Configs

DALLE2-pytorch 1.15.6 uses Pydantic v2 `BaseModel` config classes in `dalle2_pytorch.train_configs`. Import them from the installed package:

```python
from dalle2_pytorch.train_configs import TrainDecoderConfig, TrainDiffusionPriorConfig
```

Both top-level config classes provide `from_json_path(path)`, but using `json.load()` plus class construction is often quieter because the decoder helper prints the parsed JSON.

## Validation First

Before launching training, validate the file with the bundled inspector:

```bash
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/inspect_training_config.py --kind decoder --config decoder.json
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/inspect_training_config.py --kind prior --config prior.json
```

The inspector performs package import, Pydantic validation, and extra launch-safety checks that the native config models leave until training time.

## Common Config Blocks

### `TrainSplitConfig`

Used by both decoder and prior data configs:

```json
{"train": 0.75, "val": 0.15, "test": 0.10}
```

The validator requires the three values to sum exactly to `1.0`. Use simple decimal values such as `0.8`, `0.1`, `0.1` or `0.75`, `0.15`, `0.1` to avoid surprising floating-point sums.

### `TrackerConfig`

The top-level `tracker` block creates a `Tracker` with a logger, optional loader, and one or more savers:

```json
{
  "data_path": "./runs/dalle2-decoder-tracker",
  "overwrite_data_path": true,
  "log": {"log_type": "console", "verbose": true},
  "load": null,
  "save": {"save_to": "local", "save_latest_to": "./runs/dalle2-decoder/latest.pth", "save_type": "checkpoint"}
}
```

Use `console` and `local` first for credential-free debugging. W&B and HuggingFace destinations belong to the data/tracking sub-skill because they require provider credentials and upload policies.

## Decoder Config

Top-level shape:

```json
{
  "decoder": {...},
  "data": {...},
  "train": {...},
  "evaluate": {...},
  "tracker": {...},
  "seed": 0
}
```

### `decoder`: `DecoderConfig`

Important keys:

| Key | Meaning | Safety rule |
| --- | --- | --- |
| `unets` | List of `UnetConfig` objects used by the decoder cascade. | The order must match low-to-high `image_sizes`. |
| `image_size` / `image_sizes` | Final size or per-UNet sizes. | Exactly one must be set. Although older docs say `image_size` is not used, the source validator enforces either `image_size` or `image_sizes`, but not both. |
| `clip` | Adapter config for on-the-fly CLIP image/text embeddings. | May download weights. Omit only if training uses precomputed image embeddings and no text conditioning that needs CLIP. |
| `timesteps` | Training diffusion timesteps. | Keep small only for smoke configs; real training typically uses larger values. |
| `sample_timesteps` | Optional DDIM sampling timesteps, scalar or per-UNET list. | If set, each value must be `<= timesteps`. |
| `learned_variance` | Boolean or per-UNET booleans. | DeepSpeed fp16 launcher refuses `true`; set `false` for DeepSpeed fp16. |
| `beta_schedule`, `loss_type` | Noise schedule and loss. | `beta_schedule` may be a list matching unets. |

`UnetConfig` accepts constructor-compatible keys such as `dim`, `dim_mults`, `image_embed_dim`, `text_embed_dim`, `cond_on_text_encodings`, `cond_dim`, `channels`, `self_attn`, `attn_dim_head`, and `attn_heads`.

### Decoder embedding rules

`TrainDecoderConfig.check_has_embeddings` enforces part of the embedding contract:

- If any UNet has `cond_on_text_encodings: true`, either `decoder.clip` or `data.text_embeddings_url` must be provided.
- If `decoder.clip` is present and text conditioning is enabled, providing both `img_embeddings_url` and `text_embeddings_url` is redundant and rejected.
- If `decoder.clip` is present and text conditioning is disabled, providing `img_embeddings_url` is redundant and rejected.
- If `data.text_embeddings_url` is provided, at least one UNet must have `cond_on_text_encodings: true`.

The training launcher also needs an image embedding source. In practice, provide either `decoder.clip` or `data.img_embeddings_url`; otherwise the launcher can fail with `No image embeddings source specified`.

### `data`: `DecoderDataConfig`

Important keys:

| Key | Meaning |
| --- | --- |
| `webdataset_base_url` | URL/path template for image shards, with `{}` where the zero-padded shard id is inserted. |
| `img_embeddings_url` | Optional sidecar image embedding folder. |
| `text_embeddings_url` | Optional sidecar text embedding folder. |
| `num_workers`, `batch_size` | Per-process dataloader workers and batch size. |
| `start_shard`, `end_shard`, `shard_width`, `index_width` | Shard range and key-width mapping used by the decoder dataloader. |
| `splits` | `TrainSplitConfig`; must sum to `1.0`. |
| `shuffle_train` | Shuffle training shards. |
| `resample_train` | Randomly resample train shards with replacement. This makes the epoch effectively infinite unless `train.epoch_samples` is set. |
| `preprocessing` | Image transform map. Supported built-ins include `RandomResizedCrop`, `RandomHorizontalFlip`, and `ToTensor`. |

Raw shard/key diagnosis belongs to `../data-and-tracking/`, but config validation should still catch impossible training loops such as `resample_train: true` without `train.epoch_samples`.

### `train`: `DecoderTrainConfig`

Important keys:

| Key | Default | Notes |
| --- | --- | --- |
| `device` | `cuda:0` | Set `cpu` for smoke validation or CPU-only hosts. |
| `epochs` | `20` | Full runs may take a long time. |
| `lr`, `wd`, `warmup_steps`, `max_grad_norm` | Optimizer/scheduler controls. | Scalars apply to all UNets; lists/tuples can tune per UNet. |
| `save_every_n_samples` | `100000` | Snapshot cadence. |
| `n_sample_images` | `6` | Sampling previews can be expensive and may use metric/model downloads. |
| `epoch_samples` | `null` | Required when `data.resample_train` is true. |
| `validation_samples` | `null` | Limit validation passes for smoke runs. |
| `use_ema`, `ema_beta` | EMA controls. | EMA weights are used for sampling and optional model-only saves. |
| `amp` | `false` | Trainer mixed precision flag; Accelerate mixed precision is configured outside JSON. |
| `unet_training_mask` | `null` | If set, length must equal the number of configured UNets. `false` freezes a UNet in the wrapper by replacing it with an identity module for that training task. |

### `evaluate`: `DecoderEvaluateConfig`

Set any metric block to `null` to disable it. Enabling `FID`, `IS`, `KID`, or `LPIPS` uses `torchmetrics[image]` and may trigger model/metric weight downloads. For smoke configs, keep all metrics disabled.

## Diffusion Prior Config

Top-level shape:

```json
{
  "prior": {...},
  "data": {...},
  "train": {...},
  "tracker": {...}
}
```

### `prior`: `DiffusionPriorConfig`

Important keys:

| Key | Meaning | Safety rule |
| --- | --- | --- |
| `clip` | `AdapterConfig` for CLIP text/image embedding generation. | The native prior launcher uses text-conditioned caption data, so include a CLIP adapter for that workflow. |
| `net` | `DiffusionPriorNetworkConfig`. | `net.dim` must match `image_embed_dim` and the CLIP latent dimension when CLIP is used. |
| `image_embed_dim`, `image_size`, `image_channels` | Embedding and image metadata. | For OpenAI `ViT-L/14`, use `image_embed_dim: 768` and `image_size: 224`. |
| `timesteps` | Training diffusion timesteps. | `train.eval_timesteps` must be within the allowed eval range. |
| `sample_timesteps` | Default sampling timesteps. | Set it explicitly when using the native eval loop. |
| `condition_on_text_encodings` | Whether prior conditions on CLIP text encodings. | The bundled launcher expects `true` with a CLIP adapter because the config has `meta_url` captions rather than a text-embedding URL field. |

`AdapterConfig.make` supports `openai`, `open_clip`, `x-clip`, and `coca`. `open_clip` looks up the configured pretrained checkpoint by model name; `x-clip` and `coca` require `base_model_kwargs` matching those libraries.

### `data`: `DiffusionPriorDataConfig`

| Key | Meaning |
| --- | --- |
| `image_url` | EmbeddingReader folder/URL for image embeddings. |
| `meta_url` | Metadata folder/URL containing captions for text-conditioned prior training. |
| `splits` | `TrainSplitConfig`, used for train/validation/test. |
| `batch_size` | Per-process batch size. |
| `num_data_points` | Total datapoints considered. If larger than the reader count, the loader falls back to the reader count. |
| `eval_every_seconds` | Timed validation cadence. |

The prior launcher uses `EmbeddingReader` and tokenizes captions when `condition_on_text_encodings` is true. Dataset acquisition, metadata schema, and reader layout diagnosis belong to `../data-and-tracking/`.

### `train`: `DiffusionPriorTrainConfig`

Important keys:

| Key | Default | Notes |
| --- | --- | --- |
| `epochs` | `1` | Number of passes through configured data. |
| `lr`, `wd`, `max_grad_norm` | Optimizer controls. | Native defaults are approximately `1.1e-4`, `6.02e-2`, `0.5`. |
| `use_ema`, `ema_beta` | EMA prior controls. | EMA validation and sampling metrics are tracked. |
| `warmup_steps` | `null` | Linear warmup when set. |
| `save_every_seconds` | `3600` | Timed latest checkpoint cadence. |
| `eval_timesteps` | `[64]` | Each value must be between `prior.sample_timesteps` and `prior.timesteps` inclusive during evaluation. |
| `best_validation_loss`, `current_epoch`, `num_samples_seen` | Resume state fields. | The launcher updates them after a tracker recall. |
| `random_seed` | `0` | Passed through Accelerate seed helper. |

## Template Workflow

1. Copy the closest template from `references/config-templates/` to a project config file.
2. Replace every placeholder URL/path and choose credential-free `console`/`local` tracker settings until data loading works.
3. Run `inspect_training_config.py` and fix all errors before launching.
4. Use `training_command_builder.py` to print a `python` or `accelerate launch` command that targets the bundled wrapper.
5. Launch only after confirming that the dataset, tracker destinations, CLIP/metric downloads, and expected runtime are acceptable.
