# Model API Reference

This reference records the verified runtime surface for the repo's diffusion wrapper and its two UNet/diffusion families.

## Loader and object graph

The common path is:

```text
config file -> core.logger.parse -> model.create_model -> DDPM wrapper
           -> model.networks.define_G -> ddpm_modules or sr3_modules
           -> set_loss / set_new_noise_schedule / load_network
```

The scripts `sr.py`, `sample.py`, and `infer.py` all create the model the same way and then apply the phase-specific noise schedule after construction.

## Verified signatures

### Public factory

```python
model.create_model(opt)
```

- Returns the repo's `DDPM` wrapper.
- Logs the created model class name.

### Model wrapper

```python
class DDPM(BaseModel):
    def __init__(self, opt)
    def feed_data(self, data)
    def optimize_parameters(self)
    def test(self, continous=False)
    def sample(self, batch_size=1, continous=False)
    def set_loss(self)
    def set_new_noise_schedule(self, schedule_opt, schedule_phase='train')
    def get_current_log(self)
    def get_current_visuals(self, need_LR=True, sample=False)
    def print_network(self)
    def save_network(self, epoch, iter_step)
    def load_network(self)
```

Key behavior:

- `feed_data` moves tensors to the selected device.
- `optimize_parameters` computes the diffusion loss, normalizes it by `b * c * h * w`, and steps the Adam optimizer.
- `test(continous=False)` calls `super_resolution` on the underlying diffusion model.
- `sample(batch_size=1, continous=False)` calls `sample` on the underlying diffusion model.
- `get_current_visuals(sample=False)` returns `SR`, `INF`, `HR`, and optionally `LR`; with `sample=True` it returns `SAM`.
- `save_network` writes `I{iter}_E{epoch}_gen.pth` and `I{iter}_E{epoch}_opt.pth`.
- `load_network` expects `path.resume_state` to be the stem without suffix and appends `_gen.pth` / `_opt.pth` itself.

### Base model helpers

```python
class BaseModel:
    def __init__(self, opt)
    def feed_data(self, data)
    def optimize_parameters(self)
    def get_current_visuals(self)
    def get_current_losses(self)
    def print_network(self)
    def set_device(self, x)
    def get_network_description(self, network)
```

Relevant helper behavior:

- `set_device` moves every non-`None` tensor in a dict or list to `self.device`.
- `get_network_description` unwraps `nn.DataParallel` before counting parameters.

### Network factory

```python
model.networks.define_G(opt)
```

Behavior:

- Imports `model.ddpm_modules.*` when `which_model_G == 'ddpm'`.
- Imports `model.sr3_modules.*` when `which_model_G == 'sr3'`.
- Defaults `unet.norm_groups` to `32` when the field is missing or `null`.
- Builds `unet.UNet(...)` followed by `diffusion.GaussianDiffusion(...)`.
- Uses orthogonal init during training.
- Wraps the generator in `nn.DataParallel` when the run is distributed.

### Diffusion family constructor

Both diffusion families expose the same constructor shape:

```python
GaussianDiffusion(
    denoise_fn,
    image_size,
    channels=3,
    loss_type='l1',
    conditional=True,
    schedule_opt=None,
)
```

Shared methods include:

```python
set_loss(device)
set_new_noise_schedule(schedule_opt, device)
sample(batch_size=1, continous=False)
super_resolution(x_in, continous=False)
forward(x, *args, **kwargs)
```

## DDPM family details

The DDPM variant in `model/ddpm_modules/` uses integer timesteps and a positional embedding over `t`.

Important methods and behavior:

- `p_losses` samples `t` with `torch.randint(0, self.num_timesteps, ...)`.
- `p_losses` expects `x_in['HR']` and, when conditional, `x_in['SR']`.
- `p_sample_loop` samples from noise, then iteratively denoises through the entire schedule.
- When `conditional=True`, the denoiser is called with `torch.cat([condition_x, x], dim=1)`.
- `q_sample` uses the fixed gamma / alpha-cumprod path described in the source.

### DDPM UNet signature

```python
UNet(
    in_channel=6,
    out_channel=3,
    inner_channel=32,
    norm_groups=32,
    channel_mults=(1, 2, 4, 8, 8),
    attn_res=(8),
    res_blocks=3,
    dropout=0,
    with_time_emb=True,
    image_size=128,
)
```

The DDPM UNet uses `TimeEmbedding` plus residual blocks with attention at selected resolutions.

## SR3 family details

The SR3 variant in `model/sr3_modules/` uses a continuous noise-level embedding and feature-wise affine conditioning.

Important differences from DDPM:

- `p_losses` samples a continuous noise level between adjacent alpha-cumprod values.
- The denoiser receives `noise_level` instead of raw integer timesteps.
- The residual block uses `FeatureWiseAffine` and `PositionalEncoding`.
- `p_sample_loop` follows the same conditional/unconditional branching but uses the SR3 embedding path.

### SR3 UNet signature

```python
UNet(
    in_channel=6,
    out_channel=3,
    inner_channel=32,
    norm_groups=32,
    channel_mults=(1, 2, 4, 8, 8),
    attn_res=(8),
    res_blocks=3,
    dropout=0,
    with_noise_level_emb=True,
    image_size=128,
)
```

## Shared module notes

- `GaussianDiffusion.set_loss` accepts only `l1` and `l2`.
- `make_beta_schedule` accepts `quad`, `linear`, `warmup10`, `warmup50`, `const`, `jsd`, and `cosine`.
- `SelfAttention` is resolution-gated by the `attn_res` list.
- `norm_groups` must divide every stage width used by `GroupNorm`.
- The model API spellings use `continous` in several places; keep that spelling when calling the methods directly.

## Operational consequences

- `conditional=true` implies a 6-channel denoiser input, because the code concatenates conditioning and noisy sample tensors.
- `conditional=false` implies a 3-channel denoiser input and unconditional sampling.
- `diffusion.channels` should match the predicted sample channels; the current configs keep it at `3`.
- Resume checkpoints must be loaded by stem; the wrapper adds the file suffixes.
