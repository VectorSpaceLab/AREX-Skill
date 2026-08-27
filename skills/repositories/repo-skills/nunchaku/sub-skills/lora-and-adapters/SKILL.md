---
name: lora-and-adapters
description: "Operate FLUX LoRA loading, composition, conversion, safetensor
  merge, IP-Adapter, and PuLID workflows with Nunchaku."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LoRA and adapters with Nunchaku

Use this sub-skill when a task involves FLUX-family LoRA loading, LoRA strength control, multi-LoRA composition, conversion to Nunchaku LoRA format, split-safetensors model merging, FLUX IP-Adapter image prompts, or FLUX PuLID identity conditioning in an installed `nunchaku` environment.

Do not use this sub-skill for Qwen custom LoRA loading/training. The Qwen docs describe custom LoRA support as under development; route Qwen-Image base and Lightning workflows to the Qwen sub-skill instead.

## Fast routing

| Need | Start here |
| --- | --- |
| Load one FLUX LoRA and tune its global strength | `references/lora-adapter-workflows.md#single-flux-lora` |
| Combine several FLUX LoRAs with independent strengths | `references/lora-adapter-workflows.md#multiple-flux-loras` |
| Pre-compose LoRAs from a shell command | `scripts/compose_lora_cli.py` and `references/lora-adapter-workflows.md#compose-cli` |
| Convert a Diffusers-format FLUX LoRA to Nunchaku format | `references/lora-adapter-workflows.md#conversion-to-nunchaku-format` |
| Merge split quantized model safetensors | `references/lora-adapter-workflows.md#merge-safetensors-utility` |
| Add IP-Adapter image prompt conditioning | `references/lora-adapter-workflows.md#ip-adapter-image-prompts` |
| Add PuLID identity conditioning | `references/lora-adapter-workflows.md#pulid-identity-conditioning` |
| Diagnose format, strength, asset, or adapter failures | `references/troubleshooting.md` |

## Core operating pattern

1. Build the FLUX pipeline with `NunchakuFluxTransformer2dModel.from_pretrained(...)` and a compatible Diffusers FLUX pipeline class.
2. For a single LoRA, call `transformer.update_lora_params(lora_path_or_state_dict)` and then `transformer.set_lora_strength(strength)`.
3. For multiple LoRAs, call `compose_lora([(path_or_state_dict, strength), ...])`, then pass the returned dict or saved composed safetensors to `update_lora_params`. Do not rely on `set_lora_strength` for per-LoRA control after composition.
4. Use `python -m nunchaku.lora.flux.compose` or the bundled `scripts/compose_lora_cli.py` to save a reusable composed Diffusers-format LoRA. Use `python -m nunchaku.lora.flux.convert` or `to_nunchaku(...)` only when you intentionally want Nunchaku-format LoRA weights tied to a quantized base checkpoint.
5. Treat Nunchaku-format LoRAs as terminal artifacts: do not compose them with other LoRAs, and remember that composition strengths are baked into the composed weights.
6. For IP-Adapter, initialize the pipeline, call Diffusers `load_ip_adapter(...)`, then call `apply_IPA_on_pipe(...)`; pass an RGB `ip_adapter_image` during generation. IP-Adapter support is documented as deprecated in March 2026.
7. For PuLID, instantiate `PuLIDFluxPipeline`, then bind `pulid_forward` onto `pipeline.transformer.forward` with `MethodType` before generation; pass an identity reference image as `id_image` and tune `id_weight`.

## Minimal snippets

Single LoRA:

```python
import torch
from diffusers import FluxPipeline
from nunchaku import NunchakuFluxTransformer2dModel
from nunchaku.utils import get_precision

precision = get_precision()
transformer = NunchakuFluxTransformer2dModel.from_pretrained(
    f"nunchaku-tech/nunchaku-flux.1-dev/svdq-{precision}_r32-flux.1-dev.safetensors"
)
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", transformer=transformer, torch_dtype=torch.bfloat16
).to("cuda")

transformer.update_lora_params("owner/repo/my_lora.safetensors")
transformer.set_lora_strength(0.8)
image = pipe("a compact product photo of a blue ceramic teapot", num_inference_steps=25, guidance_scale=3.5).images[0]
```

Multiple LoRAs:

```python
from nunchaku.lora.flux.compose import compose_lora

composed = compose_lora([
    ("owner/style-lora/style.safetensors", 0.7),
    ("owner/speed-lora/turbo.safetensors", 1.0),
])
transformer.update_lora_params(composed)
```

For complete adapter workflows, CLI syntax, and caveats, use `references/lora-adapter-workflows.md`.

## Evidence base

Distilled from `docs/source/usage/lora.rst`, `docs/source/usage/ip_adapter.rst`, `docs/source/usage/pulid.rst`, LoRA/IP-Adapter/PuLID source modules, live public API inspection, and native test/example candidates. Native tests and examples are verification candidates for later integration; this sub-skill does not claim they were run during drafting.
