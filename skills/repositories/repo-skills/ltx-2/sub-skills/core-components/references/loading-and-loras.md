# Loading, ModelPaths, LoRAs, Block Streaming, and Quantization

Use this reference when custom code needs to load LTX-2 components, inspect safetensors metadata, fuse LoRAs, or wire quantization policies. Examples use placeholder paths and do not load real checkpoints unless you provide actual files.

## ModelPaths contract

`ltx_pipelines.utils.model_paths.ModelPaths` is the normalized component-path contract shared by CLI parsing and Python pipeline constructors. It supports two modes.

### Monolith mode

```python
from ltx_pipelines.utils.model_paths import ModelPaths

paths = ModelPaths.from_monolith(
    checkpoint_path="/models/ltx_checkpoint.safetensors",
    gemma_root="/models/gemma_root",          # may be None only when no prompt encoding is needed
    video_vae_path=None,                      # optional override; defaults to checkpoint_path
)
```

Semantics:

- `transformer_path`, `audio_vae_path`, and `duration_head_path` point to the monolith checkpoint.
- `text_encoder_path` is the Gemma root directory.
- `video_vae_path` is the monolith checkpoint unless overridden.
- `embeddings_weight_paths == (checkpoint_path,)`.

Monolith CLIs generally require `--checkpoint-path` or `--distilled-checkpoint-path` plus `--gemma-root`; `--video-vae-path` is a shared optional override and does not by itself select split mode.

### Split mode

```python
paths = ModelPaths.from_split(
    transformer_path="/models/split/transformer.safetensors",
    text_encoder_path="/models/split/text_encoder.safetensors",
    video_vae_path="/models/split/vae.safetensors",
    audio_vae_path="/models/split/audio_vae.safetensors",
    duration_head_path="/models/split/duration_head.safetensors",
)
```

Semantics:

- Omitted component slots stay `None`; do not fill unused slots with dummy strings.
- If both `transformer_path` and `text_encoder_path` are present, `embeddings_weight_paths == (transformer_path, text_encoder_path)`.
- If only `transformer_path` is present, `embeddings_weight_paths == (transformer_path,)`.
- If `transformer_path` is absent, `embeddings_weight_paths == ()`.

Typed accessors fail where the missing slot is actually needed:

```python
paths.transformer()    # returns str or raises ValueError
paths.text_encoder()  # returns str or raises ValueError
paths.video_vae()     # returns str or raises ValueError
paths.audio_vae()     # returns str or raises ValueError
paths.duration_head() # returns str or raises ValueError
```

### Split/monolith misuse

`model_paths_from_namespace(namespace)` enforces XOR rules:

- Split pack flags are `transformer_path`, `text_encoder_path`, `audio_vae_path`, and `duration_head_path`.
- `video_vae_path` is shared and intentionally does not flip into split mode by itself.
- Split pack flags cannot be combined with monolith checkpoint/Gemma flags.
- Monolith mode needs a checkpoint plus Gemma root.

If a user sees a `SystemExit` mentioning split pack flags or monolith args, inspect their path mode first; do not debug it as a missing file issue.

## SingleGPUModelBuilder

`SingleGPUModelBuilder` builds one model on a single target device from safetensors metadata and weights. It is immutable: `.with_*` and `.lora(...)` return shallow clones.

```python
import torch
from ltx_core.loader import SingleGPUModelBuilder
from ltx_core.model.transformer import LTXModelConfigurator, LTXV_MODEL_COMFY_RENAMING_MAP

builder = SingleGPUModelBuilder(
    model_class_configurator=LTXModelConfigurator,
    model_path="/models/transformer.safetensors",       # or tuple of shard paths
    model_sd_ops=LTXV_MODEL_COMFY_RENAMING_MAP,
)

# This loads a real checkpoint; use only when files exist and the user requested it.
model = builder.build(device=torch.device("cuda"), dtype=torch.bfloat16)
```

Important behaviors:

- `model_metadata()` reads the full safetensors metadata from the first shard.
- `model_config()` returns `metadata.get("config", {})`.
- `meta_model(metadata, module_ops)` creates the model on `meta` and applies module ops.
- `build(device=None, dtype=None)` defaults `device` to `cuda` when omitted.
- If no LoRA strengths are active, state dict tensors are loaded and optionally cast; quantized dtypes and scalar FP32 scale values are protected from generic dtype casting.
- Default registry caches model shells but not weights (`ModelRegistry(cache_models=True, cache_weights=False)`).
- Default `lora_load_device` is CPU, which keeps peak GPU memory lower while fusing adapters.

## Component configurators and key maps

Choose configurator and SDOps map together:

| Component | Configurator | Typical SDOps map |
|---|---|---|
| Audio-video transformer | `ltx_core.model.transformer.LTXModelConfigurator` | `LTXV_MODEL_COMFY_RENAMING_MAP` for raw `model.diffusion_model.*` keys. |
| Video-only transformer | `LTXVideoOnlyModelConfigurator` | `LTXV_MODEL_COMFY_RENAMING_MAP`. |
| Audio-only transformer | `LTXAudioOnlyModelConfigurator` | `LTXV_AUDIO_ONLY_MODEL_COMFY_RENAMING_MAP`. |
| Video VAE encoder | `VideoEncoderConfigurator` | `VAE_ENCODER_COMFY_KEYS_FILTER`. |
| Video VAE decoder | `VideoDecoderConfigurator` | `video_decoder_sd_ops_for_checkpoint(path)` or decoder-specific maps. |
| Audio VAE encoder | `AudioEncoderConfigurator` | `AUDIO_VAE_ENCODER_COMFY_KEYS_FILTER`. |
| Audio VAE decoder | `AudioDecoderConfigurator` | `AUDIO_VAE_DECODER_COMFY_KEYS_FILTER`. |
| Vocoder | `VocoderConfigurator` | `VOCODER_COMFY_KEYS_FILTER`. |
| Gemma text encoder/processor | `GemmaTextEncoderConfigurator`, `EmbeddingsProcessorConfigurator` | Use `get_gemma_ops(...)`, `module_ops_from_gemma_root(...)`, or the embeddings processor key ops as appropriate. |

`VideoDecoderConfigurator` chooses conv versus DiffVAE from checkpoint metadata field `config.vae._class_name`. Use `is_diffusion_video_vae(checkpoint_path)` when you need a metadata-only decision.

## SDOps basics

`SDOps` filters, renames, and transforms state-dict keys as safetensors are loaded.

```python
from ltx_core.loader import SDOps

ops = (
    SDOps("MY_MAP")
    .with_matching(prefix="model.diffusion_model.")
    .with_replacement("model.diffusion_model.", "")
)
```

Rules:

- At least one `with_matching(...)` matcher must match for `apply_to_key(...)` to keep a key.
- Replacements are applied in mapping order after a key is accepted.
- `allowed_keys` can further restrict the post-replacement names.
- `with_kv_operation(...)` can split, fold, drop, or transform values. Returning an empty list drops the tensor.

Common wrong assumption: `SDOps("identity")` alone is not an identity map because it has no matcher. Use `SDOps("identity").with_matching()` for pass-through matching.

## LoRA fusion policy

LoRAs are represented as `LoraPathStrengthAndSDOps(path, strength, sd_ops)`. The `sd_ops` must map the adapter's keys to the target model's post-renamed key layout.

```python
from ltx_core.loader import LTXV_LORA_COMFY_RENAMING_MAP, LoraPathStrengthAndSDOps

loras = (
    LoraPathStrengthAndSDOps(
        path="/models/adapters/style_lora.safetensors",
        strength=0.8,
        sd_ops=LTXV_LORA_COMFY_RENAMING_MAP,
    ),
)

builder = builder.with_loras(loras)
```

`SingleGPUModelBuilder.lora(path, strength, sd_ops)` appends one adapter and returns a clone. Default LoRA loading stages adapter weights on CPU and fuses sequentially. You can call `with_lora_load_device(torch.device("cuda"))` only after deciding that faster loading is worth higher peak GPU memory.

### LoRA key and metadata notes

- Built-in fusion looks for LoRA tensors ending in `.lora_A.weight` and `.lora_B.weight`; affected base weights are the same prefix with `.weight`.
- `LTXV_LORA_COMFY_RENAMING_MAP` strips `diffusion_model.` from Comfy-style LoRA keys.
- `LTXV_LORA_COMFY_TARGET_MAP` also maps `.lora_A.weight`/`.lora_B.weight` to `.weight`; use it only for workflows that explicitly need target-key derivation, not as a default adapter loader replacement.
- IC-LoRA pipelines read safetensors metadata keys such as `reference_downscale_factor` and `reference_temporal_scale_factor`; missing metadata defaults to `1` in those helpers but may make reference conditioning wrong for a trained adapter.
- HDR IC-LoRA metadata may include `hdr_transform`, `use_hdr_transform`, and reference scale metadata. Route complete HDR IC-LoRA workflows to `inference-pipelines`.

Troubleshoot LoRA failures by checking all three layers: adapter file exists and opens as safetensors, metadata matches workflow assumptions, and `sd_ops.apply_to_key(...)` maps adapter keys into existing target model keys.

## QuantizationPolicy wiring

`QuantizationPolicy` packages three things that must stay together:

- `sd_ops`: state-dict operations applied while loading weights.
- `module_ops`: module mutations applied on the meta model before weights are assigned.
- `fuse_rule`: how LoRA deltas are merged into the policy's weight layout.

Do not pass only one field and forget the others.

### FP8 cast

```python
from ltx_core.quantization.fp8_cast import build_policy as build_fp8_cast_policy

policy = build_fp8_cast_policy("/models/transformer_or_checkpoint.safetensors")
builder = SingleGPUModelBuilder(
    model_class_configurator=LTXModelConfigurator,
    model_path="/models/transformer_or_checkpoint.safetensors",
    model_sd_ops=policy.sd_ops,
    module_ops=policy.module_ops,
    fuse_rule=policy.fuse_rule,
)
```

`fp8_cast.build_policy(path)` reads safetensors scale-key metadata/header information. It supports prequantized FP8 checkpoints by folding sibling `*_scale` tensors into parent weights at load time, then uses module ops so selected linear layers store FP8 weights and upcast during forward.

### FP8 scaled matmul

```python
from ltx_core.quantization.fp8_scaled_mm import build_policy as build_fp8_scaled_mm_policy

policy = build_fp8_scaled_mm_policy("/models/prequant_fp8_transformer.safetensors")
```

This policy requires a pre-quantized checkpoint with `F8_E4M3` `.weight` tensors and sibling `.weight_scale` tensors. If no such layers are found, the factory raises `ValueError` and tells you to use `fp8_cast` for BF16 checkpoints.

### CLI string dispatch

`ltx_pipelines.utils.quantization_factory.QuantizationKind` maps user-facing strings to policies:

- `fp8-cast`
- `fp8-scaled-mm`
- `nvfp4-cast`
- `nvfp4-prequant`

NVFP4 paths rely on optional backend/hardware constraints; route NVFP4 build/run claims to `performance-backends`. Core code may construct the policy object, but should not claim it will run on unsupported hardware.

## Block streaming

`ltx_core.block_streaming.StreamingModelBuilder` returns a `BlockStreamingWrapper` that streams sequential transformer blocks from pinned CPU RAM or disk into reusable GPU buffers.

```python
import torch
from ltx_core.block_streaming import StreamingModelBuilder, DISK_CPU_SLOTS

stream_builder = StreamingModelBuilder(
    model_class_configurator=LTXModelConfigurator,
    model_path="/models/transformer.safetensors",
    model_sd_ops=LTXV_MODEL_COMFY_RENAMING_MAP,
    module_ops=(),
    loras=(),
    fuse_rule=policy.fuse_rule if policy else bf16_fuse_rule,
    blocks_attr="transformer_blocks",
    blocks_prefix="transformer_blocks",
    cpu_slots_count=DISK_CPU_SLOTS,   # small value selects disk streaming
)

# Loads a real checkpoint; requires actual files.
wrapped = stream_builder.build(
    device=torch.device("cuda"),
    dtype=torch.bfloat16,
    gpu_slots_count=2,
)
try:
    ...  # call wrapped like the underlying model
finally:
    wrapped.teardown()
```

Selection rules:

- `blocks_prefix` must be non-empty.
- `dtype` is required for `build(...)`.
- If `cpu_slots_count >= num_blocks`, the builder preloads all block weights into pinned CPU buffers: faster, higher CPU memory.
- If `cpu_slots_count < num_blocks`, it uses disk streaming with background reads: slower, lower CPU memory.
- LoRAs are fused into pinned buffers for RAM streaming or on H2D copy for disk streaming.
- For FP8 cast streaming, pass the quantization policy's `fuse_rule`; otherwise LoRA deltas may be fused with the wrong dtype/layout assumptions.

## Safetensors metadata inspection

For metadata-only checks, use the loader instead of materializing full weights:

```python
from ltx_core.loader import SafetensorsModelStateDictLoader

loader = SafetensorsModelStateDictLoader()
metadata = loader.metadata("/models/component.safetensors")
config = metadata.get("config", {})
version = metadata.get("model_version")
```

Metadata values are parsed from JSON strings when possible and left as raw strings otherwise. This is safe for path/mode decisions but still requires the local file to exist.

## Custom denoising scaffold without loading checkpoints

The following snippet shows the object wiring shape. It intentionally stops before loading models or running generation.

```python
from ltx_core.components.schedulers import LTX2Scheduler
from ltx_core.components.guiders import MultiModalGuiderParams
from ltx_core.components.patchifiers import VideoLatentPatchifier, AudioPatchifier
from ltx_core.tools import VideoLatentTools, AudioLatentTools
from ltx_core.types import VideoPixelShape, VideoLatentShape, AudioLatentShape
from ltx_pipelines.utils.model_paths import ModelPaths

model_paths = ModelPaths.from_split(
    transformer_path="/models/transformer.safetensors",
    text_encoder_path="/models/text_encoder.safetensors",
    video_vae_path="/models/vae.safetensors",
    audio_vae_path="/models/audio_vae.safetensors",
)

pixel_shape = VideoPixelShape(batch=1, frames=121, height=768, width=1280, fps=24.0)
video_shape = VideoLatentShape.from_pixel_shape(pixel_shape)
audio_shape = AudioLatentShape.from_video_pixel_shape(pixel_shape)

video_tools = VideoLatentTools(VideoLatentPatchifier(1), video_shape, fps=pixel_shape.fps)
audio_tools = AudioLatentTools(AudioPatchifier(1), audio_shape)
video_state = video_tools.create_initial_state(device="cpu", dtype=torch.float32)
audio_state = audio_tools.create_initial_state(device="cpu", dtype=torch.float32)

sigmas = LTX2Scheduler().execute(steps=30, latent=video_state.latent)
video_guidance = MultiModalGuiderParams(cfg_scale=3.0, stg_scale=1.0, stg_blocks=[28], modality_scale=3.0)
audio_guidance = MultiModalGuiderParams(cfg_scale=7.0, stg_scale=1.0, stg_blocks=[28], modality_scale=3.0)
```

For real denoising, use pipeline blocks/denoisers from `ltx_pipelines.utils` or a pipeline class, then route the complete runnable recipe to `inference-pipelines`.

## Safe helper

`../scripts/inspect_core_api.py` can verify imports and signatures in an installed environment and can run tiny CPU shape checks. It never loads checkpoint files by default. Use `--checkpoint-metadata PATH` only when the user provides a local file and wants metadata inspection.
