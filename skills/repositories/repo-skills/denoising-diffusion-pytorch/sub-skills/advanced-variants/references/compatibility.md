# Advanced Variants Compatibility

This file records runtime compatibility expectations for advanced APIs in `denoising-diffusion-pytorch` 2.3.1. Treat public package installation and CPU PyTorch as the minimum required backend. CUDA and flash attention are optional accelerators unless a downstream task explicitly requires them.

## Package and dependency facts

- Distribution name: `denoising-diffusion-pytorch`.
- Import package: `denoising_diffusion_pytorch`.
- Inspected version: `2.3.1`.
- Python requirement: `>=3.8`.
- Runtime dependency includes `torch>=2.0`, `torchvision`, `accelerate`, `einops`, `ema-pytorch`, `numpy`, `pillow`, `pytorch-fid`, `scipy`, and `tqdm`.

## Backend support matrix

| Capability | CPU | CUDA | Notes |
| --- | --- | --- | --- |
| Karras 2D/1D shape checks | Required and supported | Optional | Tiny CPU checks are sufficient for API correctness. |
| Karras 3D shape check | Optional CPU check | Optional | Video convolutions can be slow; keep opt-in with `--include-3d`. |
| Continuous-time / v-param / EDM losses | CPU-compatible | Optional | Requires correctly configured `Unet` time conditioning. |
| Learned variance / weighted objective losses | CPU-compatible | Optional | Inherits root image diffusion requirements. |
| simple diffusion UViT loss | CPU-compatible | Optional | Keep dimensions small. |
| Flash / SDPA attention | Constructible on CPU with PyTorch >= 2.0 | Optional acceleration | `flash_attn=True` uses PyTorch SDPA; no extra `flash-attn` dependency. |

## Attention and flash behavior

`Attend(flash=True)` asserts PyTorch >= 2.0. On CUDA, the module chooses CUDA SDPA backend lists only when CUDA is available at construction time and `flash=True`. CPU execution checks correctness but not GPU flash-kernel speed.

`KarrasUnet` and `KarrasUnet1D` use `attn_flash`; root image `Unet` uses `flash_attn`; Karras 3D also has `attn_flash`.

## Shape and divisibility rules

- Karras 2D: `(batch, channels, image_size, image_size)`; prefer image sizes divisible by `2 ** num_downsamples`.
- Karras 1D: `(batch, channels, seq_len)`; prefer sequence lengths divisible by `2 ** num_downsamples`.
- Karras 3D: `(batch, channels, frames, image_size, image_size)`. `downsample_types='all'` halves frames and image axes; `'frame'` halves frames; `'image'` halves height/width. Selected axes must be divisible by 2 stage by stage.

## Wrapper compatibility

| Wrapper | Compatible base model | Incompatible settings |
| --- | --- | --- |
| Root `GaussianDiffusion` | Root `Unet` with no random/learned sinusoidal conditioning and normal `out_dim` | Continuous-time-conditioned `Unet`. |
| `ContinuousTimeGaussianDiffusion` | Root `Unet(..., learned_sinusoidal_cond=True or random_fourier_features=True, self_condition=False)` | Default root `Unet`; any `self_condition=True`. |
| `VParamContinuousTimeGaussianDiffusion` | Same as continuous-time wrapper | Default root `Unet`; any `self_condition=True`. |
| `ElucidatedDiffusion` | Root `Unet` with learned/random Fourier conditioning | Default root `Unet` without that conditioning. |
| `LearnedGaussianDiffusion` | `Unet(..., learned_variance=True, self_condition=False)` | Standard `out_dim=channels`; self-conditioning. |
| `WeightedObjectiveGaussianDiffusion` | `out_dim=channels*2+2`, no self-conditioning, `sampling_timesteps == timesteps` | Standard `out_dim`; DDIM; self-conditioning. |
| `simple_diffusion.GaussianDiffusion` | `simple_diffusion.UViT` or compatible `(x, time)` model | Root `Unet` assumptions and root objective strings. |
