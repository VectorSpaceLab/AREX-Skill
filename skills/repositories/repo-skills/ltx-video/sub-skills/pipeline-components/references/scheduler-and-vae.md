# Scheduler, VAE, Transformer, and Upsampler Details

Use this reference for component-level diagnostics and direct loading behavior. Heavy checkpoint inference, output quality, and model/config choice are outside this file's verification claims.

## `RectifiedFlowScheduler`

Verified constructor signature:

```python
RectifiedFlowScheduler(
    num_train_timesteps=1000,
    shifting=None,
    base_resolution=1024,
    target_shift_terminal=None,
    sampler='Uniform',
    shift=None,
)
```

Verified step signature:

```python
RectifiedFlowScheduler.step(
    model_output,
    timestep,
    sample,
    return_dict=True,
    stochastic_sampling=False,
    **kwargs,
)
```

Core behavior:

- `init_noise_sigma == 1.0` and `order == 1`.
- `set_timesteps(...)` must be called before `step(...)`; otherwise `step` raises a `ValueError` because `num_inference_steps` is `None`.
- Default `sampler='Uniform'` creates linearly spaced timesteps from `1` to `1 / num_steps`.
- `sampler='LinearQuadratic'` uses the repository's linear/quadratic schedule.
- `sampler='Constant'` requires `shift` and applies `time_shift(shift, 1, linspace(...))`.
- `set_timesteps` accepts either `num_inference_steps` or explicit `timesteps`, but not both.
- `timesteps` are also assigned to `sigmas`.

### Timestep shifting

The scheduler implements `TimestepShifter`:

```python
scheduler.set_timesteps(num_inference_steps=20, samples_shape=latent_shape)
```

When `shifting` is:

- `None`: timesteps are unchanged.
- `'SD3'`: `sd3_resolution_dependent_timestep_shift(samples_shape, timesteps, target_shift_terminal)` is applied. It computes token count from `(B, tokens, C)`, `(B, C, H, W)`, or `(B, C, F, H, W)` sample shapes and may stretch the terminal value.
- `'SimpleDiffusion'`: `simple_diffusion_resolution_dependent_timestep_shift(samples_shape, timesteps, base_resolution)` is applied.

If a shape has a rank other than 3, 4, or 5, the shift helper raises a `ValueError`.

### Step math

For deterministic sampling (`stochastic_sampling=False`):

```python
prev_sample = sample - dt * model_output
```

where `dt` is the difference between the current timestep and the next lower timestep in the scheduler's current schedule. The current timestep does not need to be exactly present in the schedule; the scheduler finds the closest lower scheduled value.

Supported timestep forms:

- Scalar timestep: global timestep for all tokens.
- Rank-2 tensor: per-token timestep with shape `(batch, tokens)`. The scheduler computes `dt[..., None]` so token 0 can remain unchanged when its timestep is 0.

For stochastic sampling:

```python
x0 = sample - timestep[..., None] * model_output
next_timestep = timestep[..., None] - dt
prev_sample = scheduler.add_noise(x0, torch.randn_like(sample), next_timestep)
```

`return_dict=False` returns `(prev_sample,)`; otherwise a `RectifiedFlowSchedulerOutput(prev_sample=..., pred_original_sample=None)` object is returned.

### Scheduler loading

```python
RectifiedFlowScheduler.from_pretrained(path)
```

Supported paths:

- Single `.safetensors`: reads metadata field `config`, expects JSON with a `scheduler` entry, and constructs from that config.
- Diffusers-style directory: reads `scheduler/scheduler_config.json`, hashes it, and looks up a supported mapping in `ltx_video.utils.diffusers_config_mapping`.

Failure modes:

- Missing safetensors metadata key `config` or missing nested `scheduler` config will fail during load.
- An unmapped diffusers scheduler config leaves no valid config to construct. Use a known LTX-Video checkpoint/config or update the mapping; do not guess incompatible scheduler settings.

## VAE: `CausalVideoAutoencoder`

Verified APIs:

```python
CausalVideoAutoencoder.from_config(config)
CausalVideoAutoencoder.from_pretrained(pretrained_model_name_or_path, *args, **kwargs)
create_video_autoencoder_demo_config(latent_channels=64)
```

Properties:

- `is_video_supported`: true unless `dims == 2`.
- `spatial_downscale_factor`: `2 ** count(spatial-compressing encoder blocks) * patch_size`.
- `temporal_downscale_factor`: `2 ** count(temporal-compressing encoder blocks)`.
- `config`: a namespace containing `_class_name='CausalVideoAutoencoder'`, dims, channels, block descriptions, normalization, patch size, latent variance, and related settings.

`from_config(config)` requirements and checks:

- `config['_class_name']` must be `CausalVideoAutoencoder`.
- `dims` can be `2`, `3`, or `(2, 1)`; lists are converted to tuples.
- `latent_log_var='uniform'` or `'constant'` requires `use_quant_conv=False`.
- Encoder/decoder block descriptions drive both network construction and downscale-factor properties.

Demo config facts verified by component smoke:

- `create_video_autoencoder_demo_config(...)` constructs a 3D video VAE config.
- With the demo config, `spatial_downscale_factor == 32` and `temporal_downscale_factor == 8`.
- `is_video_supported is True`.

Native VAE tests show:

- Demo VAE encode/decode shape test expects input `(B, 3, 17, 64, 64)` and latent shape `(B, latent_channels, ceil(F / temporal_factor), H / spatial_factor, W / spatial_factor)`.
- Temporal causality test checks that encoding the first frame or first 9 frames matches the corresponding prefix of the full-video latent.
- Downscale-factor parametrization maps single compression blocks as:

| Encoder block | Expected temporal factor | Expected spatial factor before patch size | With `patch_size=4` spatial factor |
| --- | ---: | ---: | ---: |
| `compress_space_res` | 1 | 2 | 8 |
| `compress_space` | 1 | 2 | 8 |
| `compress_time_res` | 2 | 1 | 4 |
| `compress_time` | 2 | 1 | 4 |
| `compress_all_res` | 2 | 2 | 8 |
| `compress_all` | 2 | 2 | 8 |

### VAE loading

`CausalVideoAutoencoder.from_pretrained(path)` supports:

1. Native directory containing `autoencoder.pth` and `config.json`; optional `per_channel_statistics.json` is loaded into `std-of-means` and `mean-of-means` buffers.
2. Diffusers-style directory containing `vae/config.json` and `vae/diffusion_pytorch_model.safetensors`; the config must match a supported mapping and state-dict keys are renamed according to the LTX mapping.
3. Single `.safetensors` checkpoint with metadata field `config`; JSON metadata must contain a `vae` config. State dicts with `vae.` prefixes are stripped by `load_state_dict`.

If `torch_dtype` appears in kwargs, the created VAE is moved to that dtype before loading state dict.

### VAE encode/decode helpers

The pipeline uses helper functions from `ltx_video.models.autoencoders.vae_encode`:

- `vae_encode(media_items, vae, split_size=1, vae_per_channel_normalize=False)` expects 3 channels and supports 4D images or 5D videos.
- `vae_decode(latents, vae, is_video=True, split_size=1, vae_per_channel_normalize=False, timestep=None)` decodes video latents with a target shape derived from temporal/spatial scale.
- `get_vae_size_scale_factor(vae)` returns `(temporal, spatial, spatial)`.
- `latent_to_pixel_coords(latent_coords, vae, causal_fix=False)` maps latent token coordinates into pixel/frame coordinates.
- `normalize_latents` and `un_normalize_latents` use per-channel buffers when `vae_per_channel_normalize=True`; otherwise they use `vae.config.scaling_factor`.

A common direct-use bug is enabling `vae_per_channel_normalize=True` on a VAE that lacks `mean_of_means`/`std_of_means` buffers. Check those attributes if loading custom weights.

## Transformer: `Transformer3DModel`

Key construction API:

```python
Transformer3DModel.from_pretrained(pretrained_model_path, *args, **kwargs)
```

Constructor highlights:

- Important config fields include `in_channels`, `out_channels`, `num_layers`, `num_attention_heads`, `attention_head_dim`, `cross_attention_dim`, `caption_channels`, `qk_norm`, `standardization_norm`, and RoPE fields.
- `positional_embedding_type='rope'` requires both `positional_embedding_theta` and `positional_embedding_max_pos`.
- `positional_embedding_type='absolute'` is rejected.
- `create_skip_layer_mask(batch_size, num_conds, ptb_index, skip_block_list=None)` creates layer/batch masks for STG.
- `forward(...)` consumes patchified latent tokens `hidden_states`, `indices_grid`, text embeddings/masks, timestep, optional skip-layer mask, and `SkipLayerStrategy`.

Forward signature essentials:

```python
transformer(
    hidden_states,
    indices_grid,
    encoder_hidden_states=None,
    timestep=None,
    class_labels=None,
    cross_attention_kwargs=None,
    attention_mask=None,
    encoder_attention_mask=None,
    skip_layer_mask=None,
    skip_layer_strategy=None,
    return_dict=True,
)
```

Shape expectations:

- `hidden_states`: patchified token tensor, typically `(B, N_tokens, in_channels)` when patch size is 1.
- `indices_grid`: shape `(B, 3, N_tokens)` containing frame/y/x token coordinates, later converted to fractional positions.
- `encoder_hidden_states`: text conditioning, projected if `caption_channels` is set.
- `encoder_attention_mask`: either a mask `(B, sequence_length)` or bias `(B, 1, sequence_length)`.
- `timestep`: flattened into AdaLN and reshaped by batch; direct pipeline commonly passes `(effective_batch, 1)` or per-token adjusted timesteps.

### Transformer loading

`Transformer3DModel.from_pretrained(path)` supports:

- Diffusers-style directory: reads `transformer/config.json`, maps a supported config hash to LTX's internal config, reads all `transformer/diffusion_pytorch_model*.safetensors` shards, renames mapped keys, constructs on `meta`, then loads with `assign=True, strict=True`.
- Single `.safetensors`: reads metadata field `config`, expects JSON with `transformer`, constructs from that config, and loads the single-file state dict. State dicts with `model.diffusion_model.` prefixes are stripped in `load_state_dict`.

Unmapped diffusers configs, missing metadata, absent shard files, or incompatible state-dict keys are checkpoint/config problems rather than scheduler or pipeline-call problems. Route YAML selection questions to `../model-configs/SKILL.md`.

## Latent upsampler

APIs:

```python
LatentUpsampler(
    in_channels=128,
    mid_channels=512,
    num_blocks_per_stage=4,
    dims=3,
    spatial_upsample=True,
    temporal_upsample=False,
)
LatentUpsampler.from_config(config)
LatentUpsampler.from_pretrained(pretrained_model_path, *args, **kwargs)
```

Behavior:

- Input and output tensors are latent videos with shape `(B, C, F, H, W)`.
- With `dims=2`, it rearranges frames into image batches, spatially upsamples H/W, then restores `(B, C, F, H, W)`.
- With `dims=3` and `temporal_upsample=False`, it still spatially upsamples per frame after 3D residual processing.
- With `temporal_upsample=True`, it applies a 3D upsampler and drops the duplicated first temporal slice.
- Either `spatial_upsample` or `temporal_upsample` must be true.

`from_pretrained` currently supports single `.safetensors` files with metadata field `config`; it constructs on `meta` and loads with `assign=True`. If the path is not a matching safetensors file, no valid `latent_upsampler` is produced.

## Diffusers config mapping

`ltx_video.utils.diffusers_config_mapping` contains the supported Diffusers-to-LTX config hashes and key rename maps for:

- `FlowMatchEulerDiscreteScheduler` -> `RectifiedFlowScheduler` with SD3 shift and target terminal.
- `LTXVideoTransformer3DModel` -> `Transformer3DModel` with LTX RoPE and normalization fields.
- `AutoencoderKLLTXVideo` -> `CausalVideoAutoencoder` with LTX blocks.

If a Diffusers checkpoint directory is from a newer or incompatible model family and its config hash is not in the mapping, direct component loaders may fail even though the file layout looks correct. Do not hand-edit random configs without verifying state-dict compatibility.

## Safe component testing facts

The bundled script `../scripts/check_components.py` is designed to run without checkpoint downloads. It can validate:

- Scheduler import, schedule setup, deterministic step shape preservation, and optional CUDA tensor placement.
- Demo VAE config construction, downscale factors, and video-support flag.
- Optional CUDA availability/allocation only when requested.

Already verified facts for this sub-skill:

- A `RectifiedFlowScheduler` with `sampler='LinearQuadratic'` can set timesteps and step a tensor while preserving shape.
- The demo VAE config produces `spatial_downscale_factor=32`, `temporal_downscale_factor=8`, and `is_video_supported=True`.

What this does not verify:

- Full LTX checkpoint inference.
- Hugging Face checkpoint or text encoder download.
- Prompt enhancement model loading.
- FP8/q8 kernel execution.
- Multi-scale latent upscaler checkpoint compatibility.
- Visual quality or speed.
