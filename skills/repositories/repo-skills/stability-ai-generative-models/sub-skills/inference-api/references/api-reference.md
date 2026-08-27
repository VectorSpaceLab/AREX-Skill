# Inference API Reference

This reference covers the installed `sgm.inference.api` and relevant helpers from `sgm.inference.helpers`. The API is importable as package version `0.1.0`; CPU-only inspection was used, so GPU sampling is not claimed as verified here.

## Public API Surface

Import the core objects from `sgm.inference.api`:

```python
from sgm.inference.api import (
    ModelArchitecture,
    SamplingParams,
    SamplingPipeline,
    Sampler,
    Discretization,
    Guider,
    model_specs,
)
```

`SamplingPipeline` loads the model during construction:

```python
SamplingPipeline(
    model_id: ModelArchitecture,
    model_path="checkpoints",
    config_path="configs/inference",
    device="cuda",
    use_fp16=True,
)
```

The constructor verifies `model_id in model_specs`, builds `config_path / spec.config` and `model_path / spec.ckpt`, then calls `_load_model`. It therefore requires the matching YAML config and checkpoint before any sampling method can be used.

Sampling methods:

```python
text_to_image(params, prompt, negative_prompt="", samples=1, return_latents=False)
image_to_image(params, image, prompt, negative_prompt="", samples=1, return_latents=False)
refiner(params, image, prompt, negative_prompt=None, samples=1, return_latents=False)
```

- `text_to_image` returns decoded samples, or `(samples, samples_z)` when `return_latents=True`.
- `image_to_image` expects a preprocessed image tensor, normally from `get_input_image_tensor`, and returns decoded samples, or `(samples, samples_z)` with latents.
- `refiner` expects latent input from the base pipeline. It calls img2img with `skip_encode=True`, so pass the base `samples_z`, not the decoded RGB samples.

## Model Architectures And Specs

`ModelArchitecture` values:

| Enum | Value | Config | Checkpoint | Notes |
| --- | --- | --- | --- | --- |
| `SDXL_V0_9_BASE` | `stable-diffusion-xl-v0-9-base` | `sd_xl_base.yaml` | `sd_xl_base_0.9.safetensors` | Base, non-legacy conditioning |
| `SDXL_V0_9_REFINER` | `stable-diffusion-xl-v0-9-refiner` | `sd_xl_refiner.yaml` | `sd_xl_refiner_0.9.safetensors` | Refiner, legacy conditioning |
| `SDXL_V1_BASE` | `stable-diffusion-xl-v1-base` | `sd_xl_base.yaml` | `sd_xl_base_1.0.safetensors` | Base, non-legacy conditioning |
| `SDXL_V1_REFINER` | `stable-diffusion-xl-v1-refiner` | `sd_xl_refiner.yaml` | `sd_xl_refiner_1.0.safetensors` | Refiner, legacy conditioning |

All bundled specs use `width=1024`, `height=1024`, `channels=4`, `factor=8`, and `is_guided=True`. The default config directory is `configs/inference`, and the default checkpoint directory is `checkpoints`. A mismatch between `model_id`, config filename, and checkpoint filename commonly appears as missing keys, unexpected keys, or model-load failure.

## SamplingParams Defaults

`SamplingParams` is a dataclass. Defaults:

| Field | Default | Purpose |
| --- | --- | --- |
| `width` / `height` | `1024` / `1024` | Output dimensions for txt2img and target dimensions for conditioning |
| `steps` | `50` | Sampler step count |
| `sampler` | `Sampler.DPMPP2M` | Sampler implementation |
| `discretization` | `Discretization.LEGACY_DDPM` | Sigma discretization |
| `guider` | `Guider.VANILLA` | Guidance implementation |
| `thresholder` | `Thresholder.NONE` | Only no dynamic thresholding is implemented |
| `scale` | `6.0` | Classifier-free guidance scale for `VanillaCFG` |
| `aesthetic_score` / `negative_aesthetic_score` | `5.0` / `5.0` | Refiner/base conditioning values when applicable |
| `img2img_strength` | `1.0` | `1.0` uses full sampling; values below `1.0` prune sigmas through `Img2ImgDiscretizationWrapper` |
| `orig_width` / `orig_height` | `1024` / `1024` | Original-size conditioning |
| `crop_coords_top` / `crop_coords_left` | `0` / `0` | Crop conditioning |
| `sigma_min` / `sigma_max` / `rho` | `0.0292` / `14.6146` / `3.0` | EDM discretization parameters |
| `s_churn` / `s_tmin` / `s_tmax` / `s_noise` | `0.0` / `0.0` / `999.0` / `1.0` | EDM and ancestral sampler noise controls |
| `eta` | `1.0` | Ancestral sampler eta |
| `order` | `4` | Linear multistep order |

The source tests pass sampler values as strings, for example `SamplingParams(sampler=sampler_enum.value, steps=10)`. Because these enums subclass `str`, comparing a string such as `"DPMPP2MSampler"` to `Sampler.DPMPP2M` works. Prefer enum members in new code for clarity, and validate user-supplied strings before constructing plans.

## Sampler, Discretization, And Guider Choices

`Sampler` values and extra parameters:

| Value | Constructed class | Extra fields used |
| --- | --- | --- |
| `EulerEDMSampler` | `EulerEDMSampler` | `s_churn`, `s_tmin`, `s_tmax`, `s_noise` |
| `HeunEDMSampler` | `HeunEDMSampler` | `s_churn`, `s_tmin`, `s_tmax`, `s_noise` |
| `EulerAncestralSampler` | `EulerAncestralSampler` | `eta`, `s_noise` |
| `DPMPP2SAncestralSampler` | `DPMPP2SAncestralSampler` | `eta`, `s_noise` |
| `DPMPP2MSampler` | `DPMPP2MSampler` | none beyond steps/configs |
| `LinearMultistepSampler` | `LinearMultistepSampler` | `order` |

`Discretization` values:

- `LegacyDDPMDiscretization`: no extra params.
- `EDMDiscretization`: uses `sigma_min`, `sigma_max`, and `rho`.

`Guider` values:

- `VanillaCFG`: uses `scale` and `NoDynamicThresholding` when `thresholder` is `None`.
- `IdentityGuider`: disables classifier-free guidance behavior.

Unknown sampler or discretization values raise `ValueError`. Unknown guider or unsupported thresholder choices raise `NotImplementedError`.

## Helper Behavior

Use `sgm.inference.helpers.get_input_image_tensor(image, device="cuda")` for PIL image inputs. It:

1. Reads the PIL image size as `(width, height)`.
2. Rounds both dimensions down to multiples of 64.
3. Converts to RGB, arranges as a tensor with shape `[1, 3, H, W]`.
4. Scales pixel values from `[0, 255]` to `[-1, 1]`.
5. Moves the tensor to the requested device.

`image_to_image` reads `height, width = image.shape[2], image.shape[3]`, so input tensors must be 4-D `[batch, channels, height, width]`. The generated latents returned by `return_latents=True` have latent dimensions scaled by the model factor, usually `[samples, 4, height // 8, width // 8]`.

`Img2ImgDiscretizationWrapper` asserts `0.0 <= strength <= 1.0`. In `image_to_image`, the wrapper is only applied when `params.img2img_strength < 1.0`; invalid low values still assert, while values above `1.0` bypass the wrapper and should be rejected by caller-side validation.

`do_sample`, `do_img2img`, and `get_batch` default their internal device arguments to `"cuda"`, and the public `SamplingPipeline` methods do not forward the constructor device into those helper calls. Treat CPU-only environments as introspection and planning environments unless you intentionally patch or wrap the helper path and verify compatible precision/dependency behavior.
