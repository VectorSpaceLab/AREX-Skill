# Non-FLUX Nunchaku model families

This reference covers Nunchaku's Sana, Z-Image, SDXL, and SDXL-Turbo Diffusers replacement patterns. It intentionally excludes FLUX, Qwen-Image, LoRA/adapters, and general performance/cache APIs.

## Evidence anchor

Distilled from these repository evidence paths:

- `docs/source/usage/sdxl.rst`
- `docs/source/usage/zimage.rst`
- `examples/sana1.6b.py`, `examples/sana1.6b_pag.py`
- `examples/v1/sdxl.py`, `examples/v1/sdxl-turbo.py`, `examples/v1/z-image-turbo.py`
- `nunchaku/models/transformers/transformer_sana.py`
- `nunchaku/models/transformers/transformer_zimage.py`
- `nunchaku/models/unets/unet_sdxl.py`
- `tests/sana/test_examples.py`, `tests/v1/sdxl/test_sdxl.py`, `tests/v1/z_image/test_z_image_turbo.py`

Native tests/examples are verification candidates; they are not represented as checks already run.

## API and pipeline replacement matrix

| Family | Nunchaku replacement | Diffusers pipeline slot | Typical base pipeline | Quantized asset expectations |
| --- | --- | --- | --- | --- |
| Sana | `nunchaku.NunchakuSanaTransformer2DModel` | `transformer=` | `diffusers.SanaPipeline` | Prefer a single `.safetensors` or `.sft`; legacy two-file folders are supported by source but warned as deprecated. |
| Sana PAG | `nunchaku.NunchakuSanaTransformer2DModel` with `pag_layers` | `transformer=` | `diffusers.SanaPAGPipeline` | Same Sana asset; `pag_layers` must align with `pag_applied_layers`. |
| Z-Image-Turbo | `nunchaku.NunchakuZImageTransformer2DModel` | `transformer=` | `diffusers.ZImagePipeline` | Safetensors-like file only; `offload=True` is not supported on the replacement class. |
| SDXL | `nunchaku.models.unets.unet_sdxl.NunchakuSDXLUNet2DConditionModel` | `unet=` | `diffusers.StableDiffusionXLPipeline` | Safetensors-like file only; `offload=True` is not supported on the replacement class. |
| SDXL-Turbo | Same SDXL UNet class | `unet=` | `diffusers.StableDiffusionXLPipeline` | Use an SDXL-Turbo-specific quantized UNet asset with the SDXL-Turbo base pipeline. |

## Common operating rules

- Require explicit asset inputs: a Diffusers base model ID/path and a Nunchaku quantized checkpoint path. Do not silently fall back to local repo examples.
- Use CUDA-capable hardware. CPU-only operation is not a complete substitute for Nunchaku's compiled 4-bit CUDA kernels.
- Match the class to the Diffusers component slot: transformer replacements go into `transformer=`, SDXL UNet replacement goes into `unet=`.
- Match the quantized asset to the family and variant. A file name containing `sana`, `z-image`, `sdxl`, or `sdxl-turbo` should agree with the selected family.
- Prefer `.safetensors` or `.sft` assets. Z-Image and SDXL loader code asserts this; Sana supports legacy folders but the common loader warns that folder-style loading is deprecated.
- For Turbo variants, use the Turbo guidance/step regime rather than the base-model regime.

## Precision and device constraints

| Situation | Recommended handling |
| --- | --- |
| Ampere/Ada CUDA GPUs | `torch.bfloat16` is the normal dtype path in the examples. Auto precision resolves to INT4 on these architectures. |
| Blackwell CUDA GPUs | Auto precision resolves to FP4. Confirm the quantized asset is an FP4 asset; do not load an INT4 file by accident. |
| Turing CUDA GPUs | Z-Image examples/tests use `torch.float16`. Sana and SDXL native candidates skip Turing; do not assume they are supported without separate validation. |
| `get_precision()` returns FP4 for Sana/SDXL native candidates | Native candidate tests skip those paths; treat them as unverified unless separately validated. |
| Diffusers sequential CPU offload | This is pipeline memory placement, not CPU inference. Z-Image examples use `pipe.enable_sequential_cpu_offload()` as a low-VRAM option. |
| Replacement-class `offload=True` | Z-Image and SDXL replacement loaders raise `NotImplementedError`; do not pass that kwarg to those classes. |

## Sana

### Minimal replacement pattern

```python
import torch
from diffusers import SanaPipeline
from nunchaku import NunchakuSanaTransformer2DModel

transformer = NunchakuSanaTransformer2DModel.from_pretrained(
    quantized_sana_path,
    device="cuda",
    precision="auto",  # or "int4"/"fp4" when explicitly matching the asset
)
pipe = SanaPipeline.from_pretrained(
    sana_base_model,
    transformer=transformer,
    variant="bf16",
    torch_dtype=torch.bfloat16,
).to("cuda")
pipe.vae.to(torch.bfloat16)
pipe.text_encoder.to(torch.bfloat16)

image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    guidance_scale=4.5,
    num_inference_steps=20,
).images[0]
```

### Loader notes

- `NunchakuSanaTransformer2DModel.from_pretrained(pretrained_model_name_or_path, **kwargs)` accepts `device`, `precision`, `pag_layers`, and `return_metadata` among other Hub/loading kwargs.
- The quantized Sana module loader asserts a CUDA device. Keep `device="cuda"` or a specific CUDA device such as `cuda:0`.
- If `pag_layers` is an integer, the source normalizes it to a one-item list before loading the quantized module.
- The source supports a legacy folder flow, but the common loader warns it will be deprecated. Prefer current single-file safetensors assets.

## Sana PAG

Sana PAG uses the same Nunchaku transformer class but routes through `SanaPAGPipeline` and needs the PAG layer configured in both places.

```python
import torch
from diffusers import SanaPAGPipeline
from nunchaku import NunchakuSanaTransformer2DModel

pag_layer = 8
transformer = NunchakuSanaTransformer2DModel.from_pretrained(
    quantized_sana_path,
    device="cuda",
    pag_layers=pag_layer,
)
pipe = SanaPAGPipeline.from_pretrained(
    sana_base_model,
    transformer=transformer,
    variant="bf16",
    torch_dtype=torch.bfloat16,
    pag_applied_layers=f"transformer_blocks.{pag_layer}",
).to("cuda")

# The native example disables Diffusers' PAG attention processor reset so the
# Nunchaku quantized blocks remain installed. Treat this as a compatibility
# workaround and re-check it when upgrading Diffusers.
pipe._set_pag_attn_processor = lambda *args, **kwargs: None

image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    guidance_scale=5.0,
    pag_scale=2.0,
    num_inference_steps=20,
).images[0]
```

PAG failure usually means the layer number, `pag_applied_layers`, or Diffusers processor override is inconsistent with the Nunchaku transformer blocks.

## Z-Image-Turbo

### Minimal replacement pattern

```python
import torch
try:
    from diffusers import ZImagePipeline
except ImportError:
    from diffusers.pipelines.z_image.pipeline_z_image import ZImagePipeline
from nunchaku import NunchakuZImageTransformer2DModel
from nunchaku.utils import is_turing

dtype = torch.float16 if is_turing() else torch.bfloat16
transformer = NunchakuZImageTransformer2DModel.from_pretrained(
    quantized_zimage_path,
    torch_dtype=dtype,
)
pipe = ZImagePipeline.from_pretrained(
    zimage_base_model,
    transformer=transformer,
    torch_dtype=dtype,
    low_cpu_mem_usage=False,
)
pipe = pipe.to("cuda")  # or use pipe.enable_sequential_cpu_offload() for low VRAM

image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    num_inference_steps=8,
    guidance_scale=0.0,
).images[0]
```

### Loader notes

- `NunchakuZImageTransformer2DModel.from_pretrained(pretrained_model_name_or_path, **kwargs)` supports safetensors-like files only; the source asserts the path is a file or ends with `.safetensors`/`.sft`.
- Do not pass `offload=True` to the transformer loader; it raises `NotImplementedError`. Use Diffusers pipeline offload after pipeline construction if needed.
- Checkpoint metadata drives rank and `skip_refiners`; the loader prints the parsed quantization config.
- Z-Image examples use Turbo behavior: `guidance_scale=0.0`, about 8-9 inference steps, and 1024x1024 generation.
- Rank trade-off from examples/tests: rank 32 is faster, 128 is a common quality setting, and 256 is represented for INT4 quality paths.

## SDXL and SDXL-Turbo

### SDXL base replacement pattern

```python
import torch
from diffusers import StableDiffusionXLPipeline
from nunchaku.models.unets.unet_sdxl import NunchakuSDXLUNet2DConditionModel

unet = NunchakuSDXLUNet2DConditionModel.from_pretrained(
    quantized_sdxl_unet_path,
    torch_dtype=torch.bfloat16,
)
pipe = StableDiffusionXLPipeline.from_pretrained(
    sdxl_base_model,
    unet=unet,
    torch_dtype=torch.bfloat16,
    use_safetensors=True,
    variant="fp16",
).to("cuda")

image = pipe(
    prompt=prompt,
    guidance_scale=5.0,
    num_inference_steps=50,
).images[0]
```

### SDXL-Turbo replacement pattern

```python
import torch
from diffusers import StableDiffusionXLPipeline
from nunchaku.models.unets.unet_sdxl import NunchakuSDXLUNet2DConditionModel

unet = NunchakuSDXLUNet2DConditionModel.from_pretrained(
    quantized_sdxl_turbo_unet_path,
    torch_dtype=torch.bfloat16,
)
pipe = StableDiffusionXLPipeline.from_pretrained(
    sdxl_turbo_base_model,
    unet=unet,
    torch_dtype=torch.bfloat16,
    variant="fp16",
).to("cuda")

image = pipe(
    prompt=prompt,
    guidance_scale=0.0,
    num_inference_steps=4,
).images[0]
```

### Loader notes

- `NunchakuSDXLUNet2DConditionModel.from_pretrained(pretrained_model_path, **kwargs)` supports safetensors-like files only; the source asserts the path is a file or ends with `.safetensors`/`.sft`.
- Do not pass `offload=True` to the UNet loader; it raises `NotImplementedError`.
- The loader patches SDXL attention/feed-forward blocks and converts certain LoRA/smooth key names before loading the state dict.
- Base SDXL native candidates use 50 steps and `guidance_scale=5.0`; SDXL-Turbo examples use 4 steps and `guidance_scale=0.0`.

## Native verification candidates

Use these only when CUDA, model access, output budget, and verification scope are explicitly available:

| Candidate | What it covers | Notes |
| --- | --- | --- |
| `tests/sana/test_examples.py` | Sana and Sana PAG example scripts | Skips Turing and FP4 precision. Requires Sana assets. |
| `tests/v1/z_image/test_z_image_turbo.py` | Z-Image-Turbo ranks, dtype paths, LPIPS comparison | Uses external references/assets and a Turing-specific fp16 branch. |
| `tests/v1/sdxl/test_sdxl.py` | SDXL LPIPS and timing candidate | Skips Turing and FP4 precision. Requires SDXL assets and reference image generation/cache. |
| `examples/sana1.6b.py`, `examples/sana1.6b_pag.py` | Small direct examples for Sana family | Treat as smoke candidates, not as unit tests. |
| `examples/v1/sdxl.py`, `examples/v1/sdxl-turbo.py`, `examples/v1/z-image-turbo.py` | Direct text-to-image examples for each family | Adapt or parameterize; do not copy hard-coded output names into automation. |
