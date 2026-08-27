# Performance and memory controls

This reference summarizes composable Nunchaku controls for cache, offload, attention, quantized text encoders, precision selection, and verification planning. The snippets assume `nunchaku`, `torch`, `diffusers`, and any optional packages are already installed in the active environment. They intentionally omit full pipeline setup and model-asset credentials.

## Precision and device selection

`nunchaku.utils.get_precision()` is the canonical public helper for choosing quantized weight precision.

```python
from nunchaku.utils import get_precision

precision = get_precision(device="cuda:0")  # "int4" on SM 75/80/86/89, "fp4" on SM 120/121
```

| GPU family | Compute capability | Model precision | Typical dtype | Notes |
| --- | --- | --- | --- | --- |
| Turing / RTX 20-series | SM 75 | `int4` | `torch.float16` | Use FP16 attention; offload may be required. Quantized T5 encoder is not a Turing default. |
| Ampere A100 / RTX 30 | SM 80 / 86 | `int4` | `torch.bfloat16` unless Turing-only workaround applies | Default candidate for Nunchaku quantized FLUX/Qwen workflows. |
| Ada / RTX 40 | SM 89 | `int4` | `torch.bfloat16` | FP16 attention can be a speed candidate. |
| Blackwell / RTX 50 | SM 120 / 121 | `fp4` | `torch.bfloat16` unless a workflow requires otherwise | Requires PyTorch >= 2.7 and CUDA >= 12.8. |
| Other / CPU-only | any other value | unsupported for 4-bit kernels | n/a | Report backend block; do not claim CPU replacement. |

When the checkpoint path is known, pass it to `get_precision(..., pretrained_model_name_or_path=...)` to receive a warning if the filename precision appears inconsistent with the selected architecture.

## FLUX First-Block Cache

Evidence from `docs/source/usage/cache.rst`, `examples/flux.1-dev-cache.py`, `examples/flux.1-dev-double_cache.py`, `nunchaku/caching/diffusers_adapters/flux.py`, and `nunchaku/caching/fbcache.py` shows the stable public entry point:

```python
from nunchaku.caching.diffusers_adapters import apply_cache_on_pipe

apply_cache_on_pipe(pipe, residual_diff_threshold=0.12)
```

Operational notes:

- `apply_cache_on_pipe` mutates the pipeline class call path and wraps each pipeline call in a cache context.
- Higher `residual_diff_threshold` values are faster but risk more output drift. The docs present `0.12` as a recommended starting point for long-step FLUX denoising.
- Enable cache after the pipeline has its Nunchaku transformer installed and before invoking the pipeline.
- Do not present the docs' speedup numbers as verified in a new environment unless a bounded benchmark has actually been run.

### Double First-Block Cache

Double FB cache separates thresholds for multi-block and single-block residuals:

```python
apply_cache_on_pipe(
    pipe,
    use_double_fb_cache=True,
    residual_diff_threshold_multi=0.09,
    residual_diff_threshold_single=0.12,
)
```

V2 FLUX examples import `apply_cache_on_pipe` from `nunchaku.caching.diffusers_adapters.flux_v2` and use Nunchaku's V2 transformer class. Keep V1 and V2 imports aligned with the transformer class selected by the pipeline sub-skill.

## Cache-DiT integration

Cache-DiT is optional and external. Evidence from `docs/source/usage/cache.rst`, `examples/v1/flux.1-dev-cache-dit.py`, and `examples/v1/qwen-image-cache-dit.py` uses:

```python
# pip install cache-dit
import cache_dit
from cache_dit import DBCacheConfig

cache_dit.enable_cache(
    pipe,
    cache_config=DBCacheConfig(
        Fn_compute_blocks=1,
        Bn_compute_blocks=0,
        residual_diff_threshold=0.12,
    ),
)
```

Qwen-Image examples use larger `Fn_compute_blocks` such as `8`. Treat these values as starting points, not universal defaults. Run quality checks when changing cache policy.

## TeaCache legacy/deprecated context

`nunchaku/caching/teacache.py` is marked deprecated in source but examples still show it as a context manager for FLUX and FLUX-Kontext:

```python
from nunchaku.caching.teacache import TeaCache

with TeaCache(model=transformer, num_steps=50, rel_l1_thresh=0.3, enabled=True, model_name="flux"):
    result = pipe(...)
```

Prefer the documented `apply_cache_on_pipe` or Cache-DiT routes for new guidance. If a user specifically asks about old TeaCache examples, mention that source marks it deprecated and requires matching `num_steps` to the denoising call.

## FLUX offload

Evidence from `docs/source/usage/offload.rst`, `examples/flux.1-dev-offload.py`, and memory tests uses two layers of offload together:

```python
from nunchaku import NunchakuFluxTransformer2dModel

transformer = NunchakuFluxTransformer2dModel.from_pretrained(
    quantized_transformer_path_or_id,
    offload=True,
    torch_dtype=torch.bfloat16,  # use torch.float16 on Turing
)
# Build the Diffusers pipeline with this transformer, but do not call .to("cuda").
pipe.enable_sequential_cpu_offload()
```

Rules:

- `offload=True` is Nunchaku's transformer-level CPU offload setting.
- `pipeline.enable_sequential_cpu_offload()` delegates placement to Diffusers/Accelerate.
- Avoid manual `pipe.to("cuda")` when sequential offload is active; it defeats or conflicts with offload placement.
- On Turing, use `torch.float16` for both transformer and pipeline and enable FP16 attention.

## Qwen-Image offload

Evidence from `examples/v1/qwen-image-cache-dit.py` and `NunchakuQwenImageTransformer2DModel.set_offload` shows two common branches:

```python
# Moderate/high VRAM branch.
pipe.enable_model_cpu_offload()

# Low-VRAM branch.
transformer.set_offload(True, use_pin_memory=False, num_blocks_on_gpu=1)
pipe._exclude_from_cpu_offload.append("transformer")
pipe.enable_sequential_cpu_offload()
```

Notes:

- `set_offload(True, ...)` manages Qwen transformer blocks with a Nunchaku `CPUOffloadManager`.
- `num_blocks_on_gpu` trades VRAM for speed; increase only after measuring available memory.
- `_exclude_from_cpu_offload` is a Diffusers internal list used by the example. Use it cautiously and verify after Diffusers upgrades.

## FP16 attention

Evidence from `docs/source/usage/attention.rst`, `examples/flux.1-dev-fp16attn.py`, and `NunchakuFluxTransformer2dModel.set_attention_impl`:

```python
transformer.set_attention_impl("nunchaku-fp16")
# To revert:
transformer.set_attention_impl("flashattn2")
```

Supported `set_attention_impl` values documented in source:

| Value | Meaning |
| --- | --- |
| `"flashattn2"` | Standard/default FlashAttention-2 path. |
| `"nunchaku-fp16"` | Nunchaku FP16 attention accumulation; documented as a speed candidate on NVIDIA 30-, 40-, and 50-series, and required for Turing examples. |
| `"custom"` | Requires an `attn_func(qkv)` callable returning attention output. Use only for advanced controlled experiments. |

## Quantized T5 encoder for FLUX

Evidence from `docs/source/usage/qencoder.rst`, `examples/flux.1-dev-qencoder.py`, `tests/flux/test_flux_memory.py`, and `nunchaku/models/text_encoders/t5_encoder.py`:

```python
from nunchaku import NunchakuT5EncoderModel

text_encoder_2 = NunchakuT5EncoderModel.from_pretrained(
    quantized_t5_safetensors_path_or_id,
    torch_dtype=torch.bfloat16,
    device="cuda",
)
# Pass as text_encoder_2 when constructing the FLUX pipeline.
```

Caveats:

- The quantized T5 loader expects safetensors metadata containing a T5 config and replaces supported linear layers with Nunchaku W4 linear modules.
- Default device is CUDA; source moves CPU-loaded instances to GPU. Treat CPU as unsupported for this encoder workflow.
- The docs state the quantized T5 encoder currently supports CUDA and that Turing support is pending.

## Memory/speed verification planning

Native repo files to mention only as verification candidates unless a verifier actually runs them:

| Candidate | What it can validate | Why it is not a default always-run check |
| --- | --- | --- |
| `tests/flux/test_device_id.py` | Explicit CUDA device placement, multi-GPU use, dtype selection on non-Turing device. | Requires multi-GPU CUDA and model assets. |
| `tests/flux/test_flux_cache.py` | FB cache quality threshold against LPIPS target. | Downloads/generates assets; skips Turing. |
| `tests/flux/test_flux_memory.py` | VRAM ceilings for qencoder/offload combinations. | Requires quantized FLUX and T5 assets; architecture-sensitive. |
| `tests/flux/test_flux_speed.py` | Bounded latency against expected values. | Only supports named RTX 3090/4090/5090 targets in source; benchmark noise is high. |

Suggested verifier sequence for a fresh environment:

1. Run `scripts/check_nunchaku_cuda.py --pretty` and record CUDA, device capability, selected precision, and API availability.
2. Choose one tiny model-load smoke only if model assets are accessible; avoid benchmark claims at this step.
3. For memory work, compare peak reserved memory for the same prompt/steps with `(qencoder, offload)` toggles and reset CUDA peak stats before each run.
4. For cache work, hold prompt, seed, size, and steps constant; compare image quality or LPIPS-like metric before claiming a threshold is acceptable.
5. For speed work, run warmups, synchronize CUDA before timing, and report hardware, torch/nunchaku versions, precision, dtype, attention implementation, cache settings, resolution, and step count.

## Source evidence used

- `docs/source/usage/cache.rst`, `offload.rst`, `attention.rst`, `qencoder.rst`, `basic_usage.rst`
- `examples/flux.1-dev-cache.py`, `flux.1-dev-double_cache.py`, `flux.1-dev-double_cache_offloading.py`, `flux.1-dev-offload.py`, `flux.1-dev-fp16attn.py`, `flux.1-dev-qencoder.py`, `flux.1-dev-teacache.py`, `flux.1-dev-teacache-batch.py`, `flux.1-kontext-dev-teacache.py`
- `examples/v1/flux.1-dev-cache.py`, `flux.1-dev-cache-dit.py`, `qwen-image-cache-dit.py`
- `nunchaku/caching/`, `nunchaku/models/text_encoders/t5_encoder.py`, `nunchaku/models/transformers/transformer_flux.py`, `nunchaku/models/transformers/transformer_qwenimage.py`, `nunchaku/models/utils.py`, `nunchaku/utils.py`
- `tests/flux/test_device_id.py`, `test_flux_cache.py`, `test_flux_memory.py`, `test_flux_speed.py`
