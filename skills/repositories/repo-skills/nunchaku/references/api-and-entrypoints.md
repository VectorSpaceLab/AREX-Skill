# API and entry points

This reference maps the repo-specific public APIs and reusable command surfaces that future agents should prefer when operating Nunchaku.

## Root exports

`nunchaku.__all__` exposes these classes:

| Export | Use |
| --- | --- |
| `NunchakuFluxTransformer2dModel` | Main FLUX quantized transformer replacement for Diffusers FLUX workflows. |
| `NunchakuFluxTransformer2DModelV2` | FLUX v2 transformer replacement; use when v2 examples/tests require it. |
| `NunchakuQwenImageTransformer2DModel` | Qwen-Image and Qwen-Image-Edit quantized transformer replacement. |
| `NunchakuSanaTransformer2DModel` | Sana/Sana PAG quantized transformer replacement. |
| `NunchakuZImageTransformer2DModel` | Z-Image quantized transformer replacement. |
| `NunchakuT5EncoderModel` | Quantized T5 encoder for FLUX qencoder workflows. |

## Live-inspected signatures

These signatures were checked in a private installed package environment:

```text
NunchakuFluxTransformer2dModel.from_pretrained(pretrained_model_name_or_path: str | os.PathLike[str], **kwargs)
NunchakuFluxTransformer2dModel.set_attention_impl(self, impl: str, attn_func: Optional[Callable[[torch.Tensor], torch.Tensor]] = None)
NunchakuFluxTransformer2dModel.update_lora_params(self, path_or_state_dict: str | dict[str, torch.Tensor])
NunchakuFluxTransformer2dModel.set_lora_strength(self, strength: float = 1)
NunchakuFluxTransformer2DModelV2.from_pretrained(pretrained_model_name_or_path: str | os.PathLike[str], **kwargs)
NunchakuQwenImageTransformer2DModel.from_pretrained(pretrained_model_name_or_path: str | os.PathLike[str], **kwargs)
NunchakuQwenImageTransformer2DModel.set_offload(self, offload: bool, **kwargs)
NunchakuSanaTransformer2DModel.from_pretrained(pretrained_model_name_or_path: str | os.PathLike[str], **kwargs)
NunchakuZImageTransformer2DModel.from_pretrained(pretrained_model_name_or_path: str | os.PathLike[str], **kwargs)
NunchakuT5EncoderModel.from_pretrained(pretrained_model_name_or_path: str | os.PathLike[str], **kwargs)
apply_cache_on_pipe(pipe: diffusers.pipelines.pipeline_utils.DiffusionPipeline, *args, **kwargs)
apply_IPA_on_pipe(pipe: diffusers.pipelines.pipeline_utils.DiffusionPipeline, *args, **kwargs)
compose_lora(loras: list[tuple[str | dict[str, torch.Tensor], float]], output_path: str | None = None) -> dict[str, torch.Tensor]
to_nunchaku(input_lora: str | dict[str, torch.Tensor], base_sd: str | dict[str, torch.Tensor], dtype: str | torch.dtype = torch.bfloat16, output_path: str | None = None) -> dict[str, torch.Tensor]
merge_safetensors(pretrained_model_name_or_path: str | os.PathLike[str], model_class: str, **kwargs) -> tuple[dict[str, torch.Tensor], dict[str, str]]
```

## Helper modules

| Helper | Import | Notes |
| --- | --- | --- |
| First-Block Cache / model-family cache adapters | `from nunchaku.caching.diffusers_adapters import apply_cache_on_pipe` | Dispatches by Diffusers pipeline family; FLUX/Sana variants also exist in submodules. |
| IP-Adapter patching | `from nunchaku.models.ip_adapter.diffusers_adapters import apply_IPA_on_pipe` | Use after Diffusers `load_ip_adapter(...)`; support is documented as deprecated in March 2026. |
| FLUX LoRA composition | `from nunchaku.lora.flux.compose import compose_lora` | Accepts `(path_or_state_dict, strength)` tuples; optional output path saves composed weights. |
| FLUX LoRA conversion | `from nunchaku.lora.flux.nunchaku_converter import to_nunchaku` | Converts Diffusers-format LoRA into Nunchaku format against a quantized base state. |
| Split safetensors merge | `from nunchaku.merge_safetensors import merge_safetensors` | Merges split quantized model assets for supported model classes. |
| Precision and hardware helpers | `from nunchaku.utils import get_precision, is_turing, get_gpu_memory, check_hardware_compatibility` | Prefer `get_precision(device=...)` before choosing INT4/FP4 assets. |

## CLI/module entry points

| Command | Use | Notes |
| --- | --- | --- |
| `python -m nunchaku.lora.flux.compose -i lora1.safetensors lora2.safetensors -s 0.8 0.6 -o composed_lora.safetensors` | Compose multiple FLUX LoRAs with per-LoRA strengths. | See `sub-skills/lora-and-adapters/scripts/compose_lora_cli.py` for a validated wrapper. |
| `python -m nunchaku.lora.flux.convert --lora-path composed_lora.safetensors --quant-path <quantized-base.safetensors> --output-root ./converted --dtype bfloat16` | Convert composed/diffusers-format LoRA to Nunchaku format. | Nunchaku-format LoRAs should not be composed with other LoRAs. |
| `python -m nunchaku.merge_safetensors ...` | Package-owned utility for merged safetensor artifacts. | Prefer the package module or API because supported arguments can evolve. |
| `python -m nunchaku.test ...` | Package-owned test/generation utility. | Treat as a native verification candidate, not a default runtime script. |

## Bundled skill scripts

| Script | Use |
| --- | --- |
| `scripts/inspect_nunchaku_install.py` | Safe JSON probe for installed package, CUDA, public API availability, and precision. |
| `sub-skills/flux-pipelines/scripts/flux_minimal_template.py` | Parameterized one-image FLUX template. |
| `sub-skills/qwen-image-workflows/scripts/qwen_image_template.py` | Parameterized Qwen text-to-image/edit template. |
| `sub-skills/sana-zimage-sdxl/scripts/non_flux_template.py` | Parameterized Sana/Z-Image/SDXL template. |
| `sub-skills/performance-and-memory/scripts/check_nunchaku_cuda.py` | Detailed CUDA/API checker for performance planning. |
| `sub-skills/lora-and-adapters/scripts/compose_lora_cli.py` | Validated FLUX LoRA composition wrapper. |

## Native verification candidates

Use these only after task-specific setup, model assets, credentials, and runtime budget are clear:

- FLUX: `tests/flux/test_flux_examples.py`, `tests/v1/flux/*.py`, representative `examples/flux*.py`.
- Qwen: `tests/v1/qwenimage/*.py`, representative `examples/v1/qwen-image*.py`.
- Sana/Z-Image/SDXL: `tests/sana/test_examples.py`, `tests/v1/z_image/test_z_image_turbo.py`, `tests/v1/sdxl/test_sdxl.py`.
- Performance: `tests/flux/test_device_id.py`, cache/memory/speed tests as bounded optional candidates.
- LoRA/adapters: `tests/flux/test_flux_dev_loras.py`, `tests/flux/test_flux_dev_IPA.py`, `tests/flux/test_flux_dev_pulid.py`.

Do not report these candidates as executed unless the current task actually ran them and captured outputs.
