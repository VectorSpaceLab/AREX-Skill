# FLUX workflow reference

This reference summarizes how to swap Diffusers FLUX-family transformer components for Nunchaku quantized transformer weights. It is intended for a fresh project that already has `nunchaku`, PyTorch, Diffusers, and model access configured.

## Core replacement pattern

```python
import torch
from diffusers import FluxPipeline
from nunchaku import NunchakuFluxTransformer2dModel
from nunchaku.utils import get_precision

precision = get_precision()  # "int4" on most CUDA GPUs, "fp4" on Blackwell-class GPUs
transformer = NunchakuFluxTransformer2dModel.from_pretrained(
    f"nunchaku-tech/nunchaku-flux.1-dev/svdq-{precision}_r32-flux.1-dev.safetensors",
    torch_dtype=torch.bfloat16,
)
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev",
    transformer=transformer,
    torch_dtype=torch.bfloat16,
).to("cuda")
image = pipe("A cat holding a sign that says hello world", num_inference_steps=20, guidance_scale=3.5).images[0]
```

The important part is not the prompt; it is the replacement of `FluxTransformer2DModel` with a Nunchaku transformer object before constructing the Diffusers pipeline.

## Transformer class choices

| Class | Use when | Loader behavior | Important caveats |
| --- | --- | --- | --- |
| `NunchakuFluxTransformer2dModel` | Current high-level FLUX examples, legacy directory-compatible weights, LoRA/adapters handled by sibling skill, transformer-level offload, `return_metadata` inspection. | `from_pretrained(path_or_hf_file, device="cuda", offload=False, torch_dtype=torch.bfloat16, precision="auto")`. Accepts single `.safetensors`/`.sft` model-file paths and a deprecated folder layout. | Requires CUDA for quantized module loading. `return_metadata=True` returns `(transformer, metadata)` only on this class; metadata can be absent for legacy folder loading. |
| `NunchakuFluxTransformer2DModelV2` | FLUX v2/v1 example set under the repository's v1 examples and tests, especially when matching that API surface. | `from_pretrained(path_or_hf_file, device="cpu" by source default, torch_dtype=torch.bfloat16)`. The examples pass the object into a Diffusers pipeline and then move/offload the pipeline. | Source inspection shows `offload=True` raises `NotImplementedError`; only single safetensors-style files are supported. Do not assume `return_metadata` or legacy directory loading. |

## Model and pipeline routing

Use these as starting routes. Hugging Face access, model naming, and license gates may change; if a model id fails, verify the current upstream id and credentials.

| Workflow | Diffusers pipeline | Base model route | Nunchaku transformer route pattern | Typical call kwargs |
| --- | --- | --- | --- | --- |
| FLUX.1-dev text-to-image | `FluxPipeline` | `black-forest-labs/FLUX.1-dev` | `nunchaku-tech/nunchaku-flux.1-dev/svdq-{precision}_r32-flux.1-dev.safetensors` | `num_inference_steps=20` or `50`, `guidance_scale=3.5`. |
| FLUX.1-schnell | `FluxPipeline` | `black-forest-labs/FLUX.1-schnell` | `nunchaku-tech/nunchaku-flux.1-schnell/svdq-{precision}_r32-flux.1-schnell.safetensors` | `num_inference_steps=4`, `guidance_scale=0`, often `width=1024`, `height=1024`. |
| FLUX.1-krea-dev | `FluxPipeline` | Examples use `black-forest-labs/FLUX.1-krea-dev`; some v1 test evidence uses `black-forest-labs/FLUX.1-Krea-dev`. | `nunchaku-tech/nunchaku-flux.1-krea-dev/svdq-{precision}_r32-flux.1-krea-dev.safetensors` | `num_inference_steps=20`, guidance around `3.5` to `4.5`. |
| FLUX.1-Kontext-dev image edit | `FluxKontextPipeline` | `black-forest-labs/FLUX.1-Kontext-dev` | `nunchaku-tech/nunchaku-flux.1-kontext-dev/svdq-{precision}_r32-flux.1-kontext-dev.safetensors` | Pass `image=<PIL image>`, `prompt=<edit instruction>`, `guidance_scale=2.5`, usually `num_inference_steps=20`. |
| FLUX.1-Canny-dev | `FluxControlPipeline` | `black-forest-labs/FLUX.1-Canny-dev` | `nunchaku-tech/nunchaku-flux.1-canny-dev/svdq-{precision}_r32-flux.1-canny-dev.safetensors` | Pass `control_image=<processed canny image>`, `guidance_scale=30`, dimensions matching the control image. |
| FLUX.1-Depth-dev | `FluxControlPipeline` | `black-forest-labs/FLUX.1-Depth-dev` | `nunchaku-tech/nunchaku-flux.1-depth-dev/svdq-{precision}_r32-flux.1-depth-dev.safetensors` | Pass `control_image=<depth RGB image>`, `guidance_scale=10`. |
| FLUX.1-Fill-dev | `FluxFillPipeline` | `black-forest-labs/FLUX.1-Fill-dev` | `nunchaku-tech/nunchaku-flux.1-fill-dev/svdq-{precision}_r32-flux.1-fill-dev.safetensors` | Pass `image=`, `mask_image=`, `guidance_scale=30`, `max_sequence_length=512`. |
| FLUX.1-Redux-dev | `FluxPriorReduxPipeline` then `FluxPipeline` | Prior: `black-forest-labs/FLUX.1-Redux-dev`; generation: `black-forest-labs/FLUX.1-dev`. | Use the FLUX.1-dev Nunchaku transformer in the generation pipeline. | Run `pipe_prior_redux(input_image)` first, then call `FluxPipeline(..., text_encoder=None, text_encoder_2=None, transformer=...)` with `**prior_output`. |
| ControlNet Union Pro over FLUX.1-dev | `FluxControlNetPipeline` with `FluxControlNetModel` and `FluxMultiControlNetModel` | Base: `black-forest-labs/FLUX.1-dev`; ControlNet example evidence uses `Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro`. | Use the FLUX.1-dev Nunchaku transformer. | Pass lists for `control_image`, `control_mode`, and `controlnet_conditioning_scale`; use offload on low-VRAM hosts. |

## Local and Hugging Face asset paths

`from_pretrained` can receive either a remote Hugging Face model-file path or a local path supplied by the caller:

```python
# Hugging Face model-file path
transformer_path = "nunchaku-tech/nunchaku-flux.1-dev/svdq-int4_r32-flux.1-dev.safetensors"

# Local single-file asset supplied by the caller
transformer_path = "relative/path/to/svdq-int4_r32-flux.1-dev.safetensors"  # replace with your path
```

For public templates, never hard-code private caches or credentials. Accept paths via CLI flags or environment already understood by Hugging Face tooling. The non-V2 class also has a deprecated folder-loading path that expects separate `unquantized_layers.safetensors` and `transformer_blocks.safetensors`; prefer modern single safetensors assets.

## Dtype, device, precision, and offload defaults

| Situation | Recommended settings | Why |
| --- | --- | --- |
| Ampere/Ada/Hopper-class CUDA GPU | `torch_dtype=torch.bfloat16`, `device="cuda"`, `precision=get_precision()`. | Matches examples and modern CUDA GPUs. |
| Blackwell-class CUDA GPU | `get_precision()` should choose `fp4`; use an FP4 asset path. | Source `get_precision` maps SM 120/121 to `fp4`. |
| Turing GPU, e.g. RTX 20-series | `torch_dtype=torch.float16`, `offload=True` for `NunchakuFluxTransformer2dModel`, `transformer.set_attention_impl("nunchaku-fp16")`, then Diffusers sequential CPU offload if needed. | Docs state Turing requires FP16 dtype and FP16 attention. |
| Low VRAM with non-V2 transformer | Load with `offload=True`, avoid eager `.to("cuda")`, and call `pipeline.enable_sequential_cpu_offload()`. | Keeps quantized weights and Diffusers modules from all residing on GPU at once. |
| Low VRAM with V2 transformer | Do not pass `offload=True` to V2 `from_pretrained`; use Diffusers pipeline offload or switch to `NunchakuFluxTransformer2dModel` if transformer-level offload is required. | Source raises `NotImplementedError` for V2 offload. |

## Kontext workflow shape

```python
import torch
from diffusers import FluxKontextPipeline
from diffusers.utils import load_image
from nunchaku import NunchakuFluxTransformer2dModel
from nunchaku.utils import get_precision

precision = get_precision()
transformer = NunchakuFluxTransformer2dModel.from_pretrained(
    f"nunchaku-tech/nunchaku-flux.1-kontext-dev/svdq-{precision}_r32-flux.1-kontext-dev.safetensors",
    torch_dtype=torch.bfloat16,
)
pipe = FluxKontextPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-Kontext-dev",
    transformer=transformer,
    torch_dtype=torch.bfloat16,
).to("cuda")
source_image = load_image("https://example.invalid/replace-with-accessible-image.png").convert("RGB")
result = pipe(image=source_image, prompt="Describe the requested edit", num_inference_steps=20, guidance_scale=2.5)
```

Replace the image URL/path with a caller-provided asset. Do not assume network access in offline workflows.

## FLUX v2 class shape

```python
import torch
from diffusers import FluxPipeline
from nunchaku import NunchakuFluxTransformer2DModelV2
from nunchaku.utils import get_precision

precision = get_precision()
transformer = NunchakuFluxTransformer2DModelV2.from_pretrained(
    f"nunchaku-tech/nunchaku-flux.1-dev/svdq-{precision}_r32-flux.1-dev.safetensors",
    torch_dtype=torch.bfloat16,
    device="cuda",
)
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev",
    transformer=transformer,
    torch_dtype=torch.bfloat16,
).to("cuda")
```

Do not pass `offload=True` to `NunchakuFluxTransformer2DModelV2.from_pretrained`. If a verifier needs to cover low-memory V2 behavior, treat it as a separate backend case and document the exact Diffusers offload path used.

## `return_metadata` caveat

For metadata-aware tools, only use the non-V2 class:

```python
loaded = NunchakuFluxTransformer2dModel.from_pretrained(transformer_path, return_metadata=True)
transformer, metadata = loaded
metadata = metadata or {}
```

Never pass the tuple directly into `FluxPipeline.from_pretrained`; unpack it first. V2 loader evidence does not expose `return_metadata` as a public return contract.

## What belongs in sibling sub-skills

- LoRA loading, multiple LoRA strength composition, LoRA conversion, IP-Adapter, and PuLID: use the `lora-and-adapters` sibling.
- Cache-DiT, TeaCache, FP16 attention benchmarking, quantized T5 encoder, and deeper offload tuning: use the `performance-and-memory` sibling.
- Qwen-Image, Sana, Z-Image, and SDXL routes: use their respective sibling sub-skills.
