# LoRA and adapter workflows

This reference covers FLUX LoRA loading, independent LoRA composition, conversion/export, split-safetensors merging, IP-Adapter, and PuLID. It assumes `nunchaku`, `torch`, `diffusers`, and required optional adapter dependencies are installed in a CUDA-capable environment.

## API map

| API or entry point | Purpose | Key inputs | Notes |
| --- | --- | --- | --- |
| `NunchakuFluxTransformer2dModel.update_lora_params(path_or_state_dict)` | Load or replace FLUX LoRA parameters on a quantized Nunchaku FLUX transformer. | Local safetensors path, Hugging Face `repo/file.safetensors`, or a state dict. | Non-Nunchaku LoRAs are converted internally through Diffusers format and then to Nunchaku format against the transformer's quantized base state. |
| `NunchakuFluxTransformer2dModel.set_lora_strength(strength=1)` | Apply a global scale to the currently loaded LoRA branch. | Float strength. | Intended for a single LoRA. For multiple LoRAs, bake individual strengths into `compose_lora(...)`. |
| `compose_lora(loras, output_path=None)` | Combine one or more FLUX LoRAs into a single Diffusers-format LoRA state dict. | `[(path_or_state_dict, strength), ...]`; optional output safetensors path. | Converts inputs to Diffusers format, applies per-LoRA scales, fuses QKV-style keys, and saves if `output_path` is set. Rejects Nunchaku-format inputs except the no-op single-LoRA strength-1 case. |
| `to_nunchaku(input_lora, base_sd, dtype=torch.bfloat16, output_path=None)` | Convert a Diffusers-format FLUX LoRA to Nunchaku format for a specific quantized base checkpoint. | LoRA path/dict, quantized base safetensors path/dict, dtype `bfloat16` or `float16`, optional output path. | Use when conversion cost should be paid once. The result is tied to the quantized base format and should not be composed again. |
| `python -m nunchaku.lora.flux.compose` | Package CLI for pre-composing LoRAs. | `-i/--input-paths`, `-s/--strengths`, `-o/--output-path`. | Input count and strengths count must match. The bundled wrapper performs the same cardinality check with clearer errors. |
| `python -m nunchaku.lora.flux.convert` | Package CLI for exporting a LoRA to Nunchaku format. | `--lora-path`, `--quant-path`, `--output-root`, optional `--lora-name`, `--dtype`. | Defaults to the FLUX.1-dev quantized transformer file path on Hugging Face. Choose a quant path matching the pipeline/model variant. |
| `merge_safetensors(pretrained_model_name_or_path, model_class, **kwargs)` | Merge split quantized model files into one safetensors state dict plus metadata. | Local directory or Hugging Face model repo, model class string, optional hub/subfolder args. | This is for quantized model packaging, not for LoRA composition. CLI requires `-m/--model-class`. |
| `apply_IPA_on_pipe(pipe, ip_adapter_scale=..., repo_id=...)` | Patch a compatible FLUX-style Diffusers pipeline for IP-Adapter conditioning. | Pipeline already initialized and loaded with Diffusers `load_ip_adapter(...)`; adapter scale and repo ID. | Supports pipeline class names starting with `Flux` or `IPAFlux`. IP-Adapter support is documented as deprecated in March 2026. |
| `PuLIDFluxPipeline` and `pulid_forward` | Add PuLID identity conditioning to FLUX generation. | Nunchaku FLUX transformer, PuLID pipeline, bound `pulid_forward`, RGB identity image, `id_weight`. | Requires extra face/vision dependencies and model assets such as InsightFace, FaceXLib, EVA-CLIP, and PuLID weights. |

## Single FLUX LoRA

Use this when one style/control LoRA should be loaded on a Nunchaku FLUX transformer and controlled by one global scale.

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

transformer.update_lora_params("owner/repo/style_lora.safetensors")
transformer.set_lora_strength(0.9)
result = pipe(
    "a studio portrait in the selected style",
    num_inference_steps=25,
    guidance_scale=3.5,
).images[0]
```

Operational notes:

- `update_lora_params` accepts a path-like string or a state dict. A Hugging Face value should include the repository and filename, for example `owner/repo/file.safetensors`.
- `set_lora_strength` changes every currently loaded LoRA scale. Use it only when that global behavior is intended.
- Re-calling `update_lora_params` replaces the active LoRA branch rather than stacking independently managed adapters.
- FLUX.1-tools LoRAs such as Canny or Depth follow the same load/update/strength pattern, but the surrounding pipeline is a control pipeline with `control_image` inputs.

## Multiple FLUX LoRAs

Use `compose_lora` when several LoRAs need independent strengths. Compose first, then load the composed result once.

```python
from nunchaku.lora.flux.compose import compose_lora

composed_lora = compose_lora([
    ("owner/style_lora/style.safetensors", 0.7),
    ("owner/turbo_lora/turbo.safetensors", 1.0),
])
transformer.update_lora_params(composed_lora)
```

To save the composed LoRA for reuse:

```python
from nunchaku.lora.flux.compose import compose_lora

compose_lora(
    [
        ("owner/style_lora/style.safetensors", 0.7),
        ("owner/turbo_lora/turbo.safetensors", 1.0),
    ],
    output_path="artifacts/composed_style_turbo.safetensors",
)
```

Strength semantics:

- The strength in each tuple is multiplied into that LoRA during composition.
- After composition, `set_lora_strength(x)` is a uniform post-scale for the entire composed adapter. It cannot recover separate per-LoRA sliders.
- Nunchaku-format LoRAs should not be composed with other LoRAs. Keep a Diffusers-format composed artifact if future recomposition with different strengths is expected.
- Large total rank can reduce inference speed because the LoRA branch remains separate from the main quantized branch.

## Compose CLI

Package CLI syntax:

```bash
python -m nunchaku.lora.flux.compose \
  -i style_lora.safetensors turbo_lora.safetensors \
  -s 0.7 1.0 \
  -o artifacts/composed_style_turbo.safetensors
```

Bundled wrapper syntax:

```bash
python scripts/compose_lora_cli.py \
  --input-paths style_lora.safetensors turbo_lora.safetensors \
  --strengths 0.7 1.0 \
  --output-path artifacts/composed_style_turbo.safetensors
```

The wrapper validates that `--input-paths` and `--strengths` have exactly the same length before calling `nunchaku.lora.flux.compose.compose_lora`.

## Conversion to Nunchaku format

Convert when repeated runs should avoid runtime conversion cost or when a deployment process expects Nunchaku-format LoRA weights. The base quantized safetensors must correspond to the target model family and precision.

Python API:

```python
from nunchaku.lora.flux.nunchaku_converter import to_nunchaku

converted = to_nunchaku(
    input_lora="artifacts/composed_style_turbo.safetensors",
    base_sd="model_assets/transformer_blocks.safetensors",
    dtype="bfloat16",
    output_path="artifacts/svdq-int4-composed_style_turbo.safetensors",
)
```

Package CLI:

```bash
python -m nunchaku.lora.flux.convert \
  --lora-path artifacts/composed_style_turbo.safetensors \
  --quant-path model_assets/transformer_blocks.safetensors \
  --output-root artifacts/converted \
  --lora-name composed_style_turbo \
  --dtype bfloat16
```

Conversion caveats:

- `--dtype` accepts `bfloat16` or `float16`.
- If `--lora-name` is omitted, the CLI derives a name and includes `fp4` or `int4` based on the quant path string.
- If the input is already Nunchaku format, conversion is skipped.
- Do not feed a Nunchaku-format LoRA back into multi-LoRA composition.

## Merge safetensors utility

`merge_safetensors` combines split quantized model artifacts such as `unquantized_layers.safetensors`, `transformer_blocks.safetensors`, and associated config metadata into one safetensors file. It is useful for packaging old or split model layouts; it is not a LoRA merge function.

Python API:

```python
from safetensors.torch import save_file
from nunchaku.merge_safetensors import merge_safetensors

state_dict, metadata = merge_safetensors(
    "owner/quantized-model-repo",
    model_class="NunchakuFluxTransformer2dModel",
)
save_file(state_dict, "artifacts/merged_transformer.safetensors", metadata=metadata)
```

Package CLI:

```bash
python -m nunchaku.merge_safetensors \
  --input-path owner/quantized-model-repo \
  --model-class NunchakuFluxTransformer2dModel \
  --output-path artifacts/merged_transformer.safetensors
```

Use the `model_class` matching the target model implementation, for example `NunchakuFluxTransformer2dModel` for FLUX or `NunchakuZImageTransformer2DModel` for Z-Image packaging.

## IP-Adapter image prompts

IP-Adapter adds visual prompt conditioning to FLUX.1-dev. The documented support is deprecated in March 2026, so prefer it only for maintaining existing workflows or when the user explicitly requests IP-Adapter.

```python
import torch
from diffusers import FluxPipeline
from diffusers.utils import load_image
from nunchaku import NunchakuFluxTransformer2dModel
from nunchaku.models.ip_adapter.diffusers_adapters import apply_IPA_on_pipe
from nunchaku.utils import get_precision

precision = get_precision()
transformer = NunchakuFluxTransformer2dModel.from_pretrained(
    f"nunchaku-tech/nunchaku-flux.1-dev/svdq-{precision}_r32-flux.1-dev.safetensors"
)
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev", transformer=transformer, torch_dtype=torch.bfloat16
).to("cuda")

pipe.load_ip_adapter(
    pretrained_model_name_or_path_or_dict="XLabs-AI/flux-ip-adapter-v2",
    weight_name="ip_adapter.safetensors",
    image_encoder_pretrained_model_name_or_path="openai/clip-vit-large-patch14",
)
apply_IPA_on_pipe(pipe, ip_adapter_scale=1.1, repo_id="XLabs-AI/flux-ip-adapter-v2")

reference = load_image("reference_image.png").convert("RGB")
image = pipe(
    prompt="a character holding a sign with crisp text",
    ip_adapter_image=reference,
    num_inference_steps=50,
).images[0]
```

Ordering rules:

1. Load the Nunchaku FLUX transformer and create the Diffusers pipeline.
2. Call Diffusers `pipeline.load_ip_adapter(...)` so image encoder and adapter state are registered.
3. Call `apply_IPA_on_pipe(pipe, ip_adapter_scale=..., repo_id=...)` so Nunchaku transformer blocks are patched.
4. Pass `ip_adapter_image=reference.convert("RGB")` or precomputed image embeds during generation.
5. If also using cache controls, apply them deliberately and retest the patched pipeline; adapter/cache wrappers mutate the transformer/pipeline state.

## PuLID identity conditioning

PuLID adds identity conditioning from a reference face image. It uses `PuLIDFluxPipeline` and a specialized transformer forward implementation.

```python
from types import MethodType

import torch
from diffusers.utils import load_image
from nunchaku.models.pulid.pulid_forward import pulid_forward
from nunchaku.models.transformers.transformer_flux import NunchakuFluxTransformer2dModel
from nunchaku.pipeline.pipeline_flux_pulid import PuLIDFluxPipeline
from nunchaku.utils import get_precision

precision = get_precision()
transformer = NunchakuFluxTransformer2dModel.from_pretrained(
    f"nunchaku-tech/nunchaku-flux.1-dev/svdq-{precision}_r32-flux.1-dev.safetensors"
)
pipe = PuLIDFluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev",
    transformer=transformer,
    torch_dtype=torch.bfloat16,
).to("cuda")

pipe.transformer.forward = MethodType(pulid_forward, pipe.transformer)
id_image = load_image("identity_reference.png").convert("RGB")
image = pipe(
    "a professional headshot in a cinematic lighting setup",
    id_image=id_image,
    id_weight=1.0,
    num_inference_steps=12,
    guidance_scale=3.5,
).images[0]
```

Ordering and assets:

- Bind `pulid_forward` after `PuLIDFluxPipeline.from_pretrained(...)` creates the pipeline and before the first generation call.
- `PuLIDFluxPipeline` initializes PuLID modules and can fetch or load face/vision assets, including PuLID safetensors, EVA-CLIP weights, InsightFace AntelopeV2 models, and FaceXLib parsing models.
- `id_image` should be a PIL image convertible to RGB and should contain a detectable face. `id_weight` controls identity strength.
- Advanced `pulid_forward` parameters such as `start_timestep` and `end_timestep` can gate identity conditioning by denoising timestep if passed through compatible call paths.

## Native verification candidates

The following native files are useful candidates for later verifier runs when CUDA, model assets, and credentials are available: `tests/flux/test_flux_dev_loras.py`, `tests/flux/test_flux_dev_IPA.py`, `tests/flux/test_flux_dev_pulid.py`, `examples/flux.1-dev-lora.py`, `examples/flux.1-dev-multiple-lora.py`, `examples/flux.1-dev-IP-adapter.py`, and `examples/flux.1-dev-pulid.py`. They are candidates only; this reference does not claim they were executed during skill drafting.
