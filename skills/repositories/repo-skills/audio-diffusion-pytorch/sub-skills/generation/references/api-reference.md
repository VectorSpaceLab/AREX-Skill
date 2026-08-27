# API reference

The signatures below were verified by source inspection and installed-package inspection.

## DiffusionModel

`DiffusionModel(net_t, diffusion_t=VDiffusion, sampler_t=VSampler, loss_fn=mse_loss, dim=1, **kwargs)`

- Builds `self.net` with `net_t(dim=dim, **kwargs)`.
- Splits keyword arguments by prefix before construction:
  - `diffusion_...` keys go to the diffusion constructor.
  - `sampler_...` keys go to the sampler constructor.
- `forward(*args, **kwargs)` delegates to the diffusion object and returns the diffusion loss.
- `sample(*args, **kwargs)` delegates to the sampler under `torch.no_grad()`.
- Use this route for generator training-smokes and sampling; do not use it for upsampling, vocoding, or autoencoding tasks.

## UNetV0

`UNetV0(dim, in_channels, channels, factors, items, attentions=None, cross_attentions=None, context_channels=None, attention_features=None, attention_heads=None, embedding_features=None, resnet_groups=8, use_modulation=True, modulation_features=1024, embedding_max_length=None, use_time_conditioning=True, use_embedding_cfg=False, use_text_conditioning=False, out_channels=None)`

- `channels`, `factors`, `items`, `attentions`, `cross_attentions`, and `context_channels` must all have the same length.
- `attentions`, `cross_attentions`, and `context_channels` default to zero-filled lists when omitted.
- `use_embedding_cfg=True` requires `embedding_max_length`.
- `use_text_conditioning=True` enables the text-conditioning plugin; installed inspection confirmed that the default T5 path expects `embedding_features=768`.
- When any `cross_attentions` entry is nonzero, provide `attention_heads` and `attention_features`; otherwise a-unet can raise `CrossAttentionItem requires channels, embedding_features, attention_*`.
- `use_time_conditioning=True` requires `use_modulation=True`.
- `resnet_groups=8` is the default and is often too large for tiny smoke configs; use `resnet_groups=1` when channel counts are small.
- `out_channels` is optional and is usually left implicit for generator-style use.

## VDiffusion and friends

`VDiffusion(net, sigma_distribution=UniformDistribution(), loss_fn=mse_loss)`

- Samples one sigma per batch element from `sigma_distribution` on the model device.
- Default `UniformDistribution(vmin=0.0, vmax=1.0)` returns a one-dimensional tensor of random sigmas.
- Combines clean audio and noise with the half-circle parameterization used by the v-objective.
- Calls `net(x_noisy, sigmas, **kwargs)` and returns the loss from `loss_fn`.

`UniformDistribution(vmin=0.0, vmax=1.0)`

- Produces uniform samples in `[vmin, vmax]`.
- Used by default for training-time sigma sampling.

`LinearSchedule(start=1.0, end=0.0)`

- Produces a decreasing linearly spaced sigma ladder.
- Used by default for sampling and inpainting.

`VSampler(net, schedule=LinearSchedule())`

- Expects `x_noisy`, `num_steps`, optional `show_progress`, and any model-specific kwargs.
- Uses a schedule of length `num_steps + 1` and returns a tensor with the same shape as `x_noisy`.
- The sampler is tied to `VDiffusion` in the default workflow.

`VInpainter(net, schedule=LinearSchedule())`

- `forward(source, mask, num_steps, num_resamples, show_progress=False, x_noisy=None, **kwargs)`.
- `mask` must match `source` in shape; `True` marks samples to keep from the source waveform.
- If `x_noisy` is omitted, the inpainter starts from `torch.randn_like(source)`.
- Each step predicts velocity, reconstructs clean/noisy estimates, resamples `num_resamples` times, then blends the re-noised source back into the masked region.
- Returns a tensor with the same shape as `source`.

## DiffusionAR

`DiffusionAR(in_channels, length, num_splits, diffusion_t=ARVDiffusion, sampler_t=ARVSampler, **kwargs)`

- Expert/experimental exported path, not a primary documented workflow.
- `length` must be divisible by `num_splits`.
- Internally uses `in_channels + 1` for the diffusion net input and `out_channels=in_channels` for the output head.
- Disables time conditioning and modulation inside the wrapper.
- The defaults route to `ARVDiffusion` and `ARVSampler` for chunked autoregressive diffusion.
