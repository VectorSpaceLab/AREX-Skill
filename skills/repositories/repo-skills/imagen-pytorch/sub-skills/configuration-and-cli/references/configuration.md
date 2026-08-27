# Configuration reference

This reference distills the config and CLI-facing schema for `imagen-pytorch` 2.1.0. Future agents should be able to author and validate configs from this file without reopening the original repository.

## Top-level CLI JSON shape

The CLI `imagen train` command expects a JSON object with these keys:

| Key | Required for CLI train | Meaning and safe notes |
| --- | --- | --- |
| `type` | yes | Use exactly `"original"` or `"elucidated"`. The implementation treats only `"elucidated"` specially and otherwise falls back to original; prefer strict validation so typos do not silently select the wrong decoder. |
| `imagen` | yes | Decoder config consumed by `ImagenConfig` or `ElucidatedImagenConfig`. Must include `unets` and `image_sizes`. |
| `trainer` | yes | Keyword args passed to `ImagenTrainer`. `split_valid_from_train: true` is needed if you use `validate_at_every` with CLI training. |
| `dataset_name` | yes | Hugging Face dataset name passed to `load_dataset`; may require network, credentials, and large disk/cache. |
| `dataset` | yes | Keyword args for `trainer.add_train_dataset`; must include positive integer `batch_size`. |
| `image_label` | yes | Dataset field containing PIL images when `url_label` is `null`; default template uses `null` because it downloads images by URL. |
| `url_label` | yes | Dataset field containing image URLs. If non-null, the collator downloads images. If null, `image_label` must name an image field. |
| `text_label` | yes | Dataset text field encoded by T5 in the CLI collator. |
| `checkpoint_path` | yes | Path used for resume-if-existing and final trainer save. A missing file means start new training; a missing parent directory can still break saving. |
| `max_batch_size` | optional | Microbatch size for gradient accumulation in `train_step`; defaults to 1 in CLI code. |
| `validate_at_every` | practically required by CLI train | Must be an integer; use a positive integer with `trainer.split_valid_from_train: true` to avoid the CLI's modulo-before-guard failure. |
| `save_at_every` | practically required by CLI train | Must be a positive integer; the CLI evaluates modulo before checking the save guard. |
| `sample_at_every` | optional but coupled | Must be an integer when sampling is enabled. The current CLI computes `sample_at_every` but the sample block uses `save_at_every` for the modulo check, so keep `save_at_every` positive if sampling during training. |
| `sample_texts` | optional but coupled | A non-empty list of prompt strings is required when `sample_at_every` is present. In-loop sampling is expensive and can expose CLI bugs; consider disabling it for first preflight runs. |

## Pydantic config classes

The package root exposes `UnetConfig`, `ImagenConfig`, `ElucidatedImagenConfig`, and `ImagenTrainerConfig`. `NullUnetConfig` and `Unet3DConfig` are defined in the config module; use them through config JSON or import them from the config module when a Python-side factory is required.

### `NullUnetConfig`

Use a null unet as a placeholder for cascade stages you do not train directly.

```json
{ "is_null": true }
```

### `UnetConfig`

Required fields:

- `dim`: integer base dimension.
- `dim_mults`: list/tuple of integer multipliers.

Defaults and common fields:

| Field | Default | Notes |
| --- | --- | --- |
| `text_embed_dim` | default T5 encoded dimension | Avoid relying on implicit model-config downloads in offline validation; supply an explicit value if creating tiny local configs. |
| `cond_dim` | `null` | Optional conditioning dimension. |
| `channels` | `3` | Often set at the top-level `imagen.channels`; unets are recast by the decoder to match. |
| `attn_dim_head` | `32` | Attention head dimension. |
| `attn_heads` | `16` | Default template overrides to `8`. |
| extra kwargs | allowed | Passed through to `Unet`; common template keys include `num_resnet_blocks`, `layer_attns`, and `layer_cross_attns`. Unknown extras can still fail at runtime if the model constructor does not accept them. |

### `Unet3DConfig`

Same declared fields and defaults as `UnetConfig`, but creates a `Unet3D`. In the decoder config, `video: true` also makes non-null unet entries instantiate as 3D unets. Route video tensor semantics and temporal choices to `../video-and-inpainting/SKILL.md`.

### `ImagenConfig` (`type: "original"`)

Required fields:

- `unets`: list of `UnetConfig`, `Unet3DConfig`, or `NullUnetConfig` objects.
- `image_sizes`: list of image resolutions, one per unet.

Declared defaults:

| Field | Default | Notes |
| --- | --- | --- |
| `video` | `false` | When true, non-null unets become `Unet3D`. |
| `timesteps` | `1000` | Integer for all unets or list matching cascade length. |
| `noise_schedules` | `"cosine"` | Accepted enum values are `"cosine"` and `"linear"`; list values are padded internally for cascades. |
| `text_encoder_name` | `"google/t5-v1_1-base"` | Default template uses `"google/t5-v1_1-large"`, which is heavier. |
| `channels` | `3` | CLI supports counts 1 to 4 for collator conversion. |
| `loss_type` | `"l2"` | Runtime supports `"l1"`, `"l2"`, or `"huber"`. |
| `cond_drop_prob` | `0.5` | Default package JSON uses `0.1`. |

Validation assertions to preserve:

- `len(image_sizes) == len(unets)`.
- If `random_crop_sizes` is supplied, its first element should be `null`; base unet should not random-crop.
- For CLI train, `image_sizes` must be a list because the command indexes it by `unet - 1`.

### `ElucidatedImagenConfig` (`type: "elucidated"`)

Required fields are the same as `ImagenConfig`: `unets` and `image_sizes`.

Declared defaults:

| Field | Default | Notes |
| --- | --- | --- |
| `video` | `false` | When true, non-null unets become `Unet3D`. |
| `text_encoder_name` | `"google/t5-v1_1-base"` | Same caveat about offline model config. |
| `channels` | `3` | Same CLI channel restrictions. |
| `cond_drop_prob` | `0.5` | Classifier-free guidance dropout. |
| `num_sample_steps` | `32` | Scalar or list matching cascade length. |
| `sigma_min` | `0.002` | Scalar or cascade-length list. |
| `sigma_max` | `80` | Scalar or cascade-length list. |
| `sigma_data` | `0.5` | Scalar or cascade-length list. |
| `rho` | `7` | Scalar or cascade-length list. |
| `P_mean` | `-1.2` | Scalar or cascade-length list. |
| `P_std` | `1.2` | Scalar or cascade-length list. |
| `S_churn` | `80` | Scalar or cascade-length list. |
| `S_tmin` | `0.05` | Scalar or cascade-length list. |
| `S_tmax` | `50` | Scalar or cascade-length list. |
| `S_noise` | `1.003` | Scalar or cascade-length list. |

Do not copy original-only keys such as `timesteps`, `noise_schedules`, or `loss_type` into an elucidated config unless you have confirmed that the installed constructor accepts them; the static validator treats them as suspicious.

### `ImagenTrainerConfig`

Declared fields include:

- `imagen`: nested decoder dict.
- `elucidated`: boolean, default `false`.
- `video`: boolean, default `false`.
- `use_ema`: boolean, default `true`.
- `lr`: float or list/tuple of floats, default `1e-4`.
- `eps`: float or list/tuple of floats, default `1e-8`.
- `beta1`: float, default `0.9`.
- `beta2`: float, default `0.99`.
- `max_grad_norm`: float or null.
- `group_wd_params`: boolean, default `true`.
- `warmup_steps`: integer/null or list/tuple.
- `cosine_decay_max_steps`: integer/null or list/tuple.

For CLI training, the `trainer` top-level object is passed directly to `ImagenTrainer`, not through `ImagenTrainerConfig.create`. Avoid relying on `ImagenTrainerConfig.create` as a high-level factory in generated guidance because the 2.1.0 source contains an unresolved `video` variable inside that method.

## Channel count mapping in CLI training

The CLI validates `imagen.channels` as `0 < channels < 5` and intends this mapping for PIL conversion:

| `imagen.channels` | Intended PIL mode | CLI note |
| --- | --- | --- |
| `1` | `L` | Grayscale. |
| `2` | `LA` | The CLI source has a comparison typo instead of assignment for this branch, so mode may remain `RGB`; avoid channel 2 through the CLI unless patched. |
| `3` | `RGB` | Default and safest. |
| `4` | `RGBA` | Color with alpha. |

## Default config template cautions

The bundled [default-config-template.json](default-config-template.json) mirrors the package default config but should be treated as a scaffold, not a local run recipe:

- It targets `laion/laion2B-en` with URL downloads, `google/t5-v1_1-large`, three unets up to `1024`, and `dataset.batch_size` 2048.
- It can require network, large caches, high disk throughput, and practical CUDA-scale compute.
- It is useful for key names and cascade structure, but first convert it to a tiny local validation config before attempting a new dataset or hardware setup.
- The default has three unets, while CLI `imagen train --unet` accepts only `1` or `2` (`[1<=x<3]`); use a custom training script or patch CLI if you need CLI coverage for the third stage.

## Minimal static-validation template

This is a tiny config for static preflight only. It is not a meaningful training recipe and should not be used with `imagen train` until dataset labels and compute are intentionally replaced.

```json
{
  "type": "original",
  "imagen": {
    "condition_on_text": true,
    "text_embed_dim": 768,
    "text_encoder_name": "google/t5-v1_1-base",
    "timesteps": [4],
    "image_sizes": [32],
    "channels": 3,
    "cond_drop_prob": 0.1,
    "unets": [
      {
        "dim": 8,
        "dim_mults": [1, 1],
        "num_resnet_blocks": 1,
        "layer_attns": false,
        "layer_cross_attns": false,
        "attn_heads": 2,
        "text_embed_dim": 768
      }
    ]
  },
  "trainer": {
    "lr": 0.0001,
    "split_valid_from_train": true,
    "split_valid_fraction": 0.1
  },
  "dataset_name": "replace/me-before-training",
  "dataset": {
    "batch_size": 1,
    "shuffle": true
  },
  "image_label": "image",
  "url_label": null,
  "text_label": "text",
  "checkpoint_path": "./imagen-tiny.pt",
  "save_at_every": 1,
  "validate_at_every": 1
}
```

For actual local data and collator details, route to `../data-and-text-conditioning/SKILL.md`. For writing a robust custom loop instead of using the CLI loop, route to `../training-and-checkpointing/SKILL.md`.
