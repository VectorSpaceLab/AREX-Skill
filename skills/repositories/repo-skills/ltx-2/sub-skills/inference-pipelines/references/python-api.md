# Python API reference

The public inference classes accept a `ModelPaths` object plus pipeline-specific asset paths. Constructors load model components; `__call__` performs generation. For planning, validate paths and signatures first and avoid instantiating pipelines until the user has approved a real generation environment.

Imports used below:

```python
import torch
from ltx_core.components.guiders import MultiModalGuiderParams
from ltx_core.loader import LoraPathStrengthAndSDOps
from ltx_core.loader.sd_ops import LTXV_LORA_COMFY_RENAMING_MAP
from ltx_pipelines.utils.args import ImageConditioningInput
from ltx_pipelines.utils.media_io import HDRColorSpace, encode_audio, encode_video
from ltx_pipelines.utils.model_paths import ModelPaths
```

Create LoRA records for Python constructors with:

```python
def lora(path: str, strength: float = 1.0) -> LoraPathStrengthAndSDOps:
    return LoraPathStrengthAndSDOps(path, strength, LTXV_LORA_COMFY_RENAMING_MAP)
```

## ModelPaths

`ModelPaths` is the normalized component-path contract consumed by pipeline constructors.

```python
ModelPaths(
    mode: Literal["monolith", "split"],
    transformer_path: str | None,
    text_encoder_path: str | None,
    video_vae_path: str | None,
    audio_vae_path: str | None,
    duration_head_path: str | None,
    embeddings_weight_paths: tuple[str, ...],
)
```

Prefer the factories:

```python
# LTX-2.5 split/component layout
paths = ModelPaths.from_split(
    transformer_path="models/ltx-2.5/diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors",
    text_encoder_path="models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors",
    video_vae_path="models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors",
    audio_vae_path="models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors",
    duration_head_path=None,
)

# LTX-2.3/legacy monolith layout
paths = ModelPaths.from_monolith(
    checkpoint_path="models/ltx-2.3/ltx-2.3-22b-dev.safetensors",
    gemma_root="models/gemma-3-12b-it-qat-q4_0-unquantized",
)
```

Accessor methods `transformer()`, `text_encoder()`, `video_vae()`, `audio_vae()`, and `duration_head()` return strings or raise if that component is missing. Use them to fail early when a planned pipeline needs a component omitted from split mode.

## Common Python output pattern

Most video pipelines return an iterator of decoded video chunks plus audio and a tiling config. Encode with the public media I/O helper rather than assuming a tensor is fully materialized.

```python
from ltx_core.model.video_vae import get_video_chunks_number

video, audio, num_frames, tiling = pipe(...)
encode_video(
    video=video,
    fps=24,
    audio=audio,
    output_path="outputs/result.mp4",
    video_chunks_number=get_video_chunks_number(num_frames, tiling),
)
```

Some classes return no `num_frames`; in those cases pass the requested/source frame count to `get_video_chunks_number`. `T2AOneStagePipeline` returns `Audio` and should be saved with `encode_audio(audio=audio, output_path="...")`. `HDRICLoraPipeline.__call__` returns a linear HDR float tensor; use its CLI or explicit HDR/EXR handling when file output is needed.

## Verified signatures

Signatures below were captured from the installed public package inspection.

### DistilledPipeline

```python
from ltx_pipelines.distilled import DistilledPipeline

DistilledPipeline(
    model_paths: ModelPaths,
    spatial_upsampler_path: str,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    seed: int,
    height: int,
    width: int,
    frame_rate: float,
    images: list[ImageConditioningInput],
    num_frames: int | AutoDuration = AutoDuration(...),
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    stage_1_sigmas: torch.Tensor = DISTILLED_SIGMAS,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
    color_space: HDRColorSpace | None = None,
    generated_keyframes: int | Sequence[int] = 0,
) -> tuple[Iterator[torch.Tensor], Audio, int, TilingConfig | None]
```

Use for fastest split LTX-2.5 T2V/I2V. `images` may be empty or contain `ImageConditioningInput(path, frame_idx, strength, crf=None)`. If `num_frames` is omitted/auto, a duration head must be available.

### TI2VidTwoStagesPipeline

```python
from ltx_pipelines.ti2vid_two_stages import TI2VidTwoStagesPipeline

TI2VidTwoStagesPipeline(
    model_paths: ModelPaths,
    distilled_lora: list[LoraPathStrengthAndSDOps],
    spatial_upsampler_path: str,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    negative_prompt: str,
    seed: int,
    height: int,
    width: int,
    frame_rate: float,
    num_inference_steps: int,
    video_guider_params: MultiModalGuiderParams | MultiModalGuiderFactory,
    audio_guider_params: MultiModalGuiderParams | MultiModalGuiderFactory,
    images: list[ImageConditioningInput],
    num_frames: int | AutoDuration = AutoDuration(...),
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    max_batch_size: int = 1,
    stage_1_sigmas: torch.Tensor | None = None,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
    color_space: HDRColorSpace | None = None,
    generated_keyframes: int | Sequence[int] = 0,
) -> tuple[Iterator[torch.Tensor], Audio, int, TilingConfig | None]
```

Use for guided production-quality T2V/I2V. Build guidance with `MultiModalGuiderParams(cfg_scale=..., stg_scale=..., rescale_scale=..., modality_scale=..., stg_blocks=[...])`.

### TI2VidTwoStagesHQPipeline

`TI2VidTwoStagesHQPipeline` has the same `__call__` shape as `TI2VidTwoStagesPipeline`, but its constructor additionally requires stage-specific distilled LoRA strengths:

```python
TI2VidTwoStagesHQPipeline(
    model_paths: ModelPaths,
    distilled_lora: list[LoraPathStrengthAndSDOps],
    distilled_lora_strength_stage_1: float,
    distilled_lora_strength_stage_2: float,
    spatial_upsampler_path: str,
    loras: tuple[LoraPathStrengthAndSDOps, ...],
    ...
)
```

Use when the res_2s sampler/HQ CLI is specifically requested.

### TI2VidOneStagePipeline

```python
from ltx_pipelines.ti2vid_one_stage import TI2VidOneStagePipeline

TI2VidOneStagePipeline(
    model_paths: ModelPaths,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    negative_prompt: str,
    seed: int,
    height: int,
    width: int,
    frame_rate: float,
    num_inference_steps: int,
    video_guider_params: MultiModalGuiderParams | MultiModalGuiderFactory,
    audio_guider_params: MultiModalGuiderParams | MultiModalGuiderFactory,
    images: list[ImageConditioningInput],
    num_frames: int | AutoDuration = AutoDuration(...),
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    max_batch_size: int = 1,
    sigmas: torch.Tensor | None = None,
    color_space: HDRColorSpace | None = None,
    generated_keyframes: int | Sequence[int] = 0,
) -> tuple[Iterator[torch.Tensor], Audio, TilingConfig | None]
```

Use for prototypes only; two-stage or distilled pipelines are usually better.

### ICLoraPipeline

```python
from ltx_pipelines.ic_lora import ICLoraPipeline

ICLoraPipeline(
    model_paths: ModelPaths,
    spatial_upsampler_path: str,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    seed: int,
    height: int,
    width: int,
    num_frames: int,
    frame_rate: float,
    images: list[ImageConditioningInput],
    video_conditioning: list[tuple[str, float]],
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    conditioning_attention_strength: float = 1.0,
    skip_stage_2: bool = False,
    conditioning_attention_mask: torch.Tensor | None = None,
    stage_1_sigmas: torch.Tensor = DISTILLED_SIGMAS,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
    color_space: HDRColorSpace | None = None,
) -> tuple[Iterator[torch.Tensor], Audio, TilingConfig | None]
```

`video_conditioning` contains `(path, strength)` pairs. The constructor reads IC-LoRA metadata for reference downscale/temporal scale and raises on conflicting LoRA scale metadata.

### KeyframeInterpolationPipeline

```python
from ltx_pipelines.keyframe_interpolation import KeyframeInterpolationPipeline

KeyframeInterpolationPipeline(
    model_paths: ModelPaths,
    distilled_lora: list[LoraPathStrengthAndSDOps],
    spatial_upsampler_path: str,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    negative_prompt: str,
    seed: int,
    height: int,
    width: int,
    num_frames: int,
    frame_rate: float,
    num_inference_steps: int,
    video_guider_params: MultiModalGuiderParams | MultiModalGuiderFactory,
    audio_guider_params: MultiModalGuiderParams | MultiModalGuiderFactory,
    images: list[ImageConditioningInput],
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    max_batch_size: int = 1,
    stage_1_sigmas: torch.Tensor | None = None,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
    color_space: HDRColorSpace | None = None,
) -> tuple[Iterator[torch.Tensor], Audio, TilingConfig | None]
```

Pass keyframes as multiple `ImageConditioningInput` entries at desired frame indices.

### A2VidPipelineTwoStage

```python
from ltx_pipelines.a2vid_two_stage import A2VidPipelineTwoStage

A2VidPipelineTwoStage(
    model_paths: ModelPaths,
    distilled_lora: list[LoraPathStrengthAndSDOps],
    spatial_upsampler_path: str,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    negative_prompt: str,
    seed: int,
    height: int,
    width: int,
    num_frames: int,
    frame_rate: float,
    num_inference_steps: int,
    video_guider_params: MultiModalGuiderParams,
    images: list[ImageConditioningInput],
    audio_path: str,
    audio_start_time: float = 0.0,
    audio_max_duration: float | None = None,
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    max_batch_size: int = 1,
    stage_1_sigmas: torch.Tensor | None = None,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
    color_space: HDRColorSpace | None = None,
) -> tuple[Iterator[torch.Tensor], Audio, TilingConfig | None]
```

The input audio is decoded, encoded to the audio latent, frozen during video denoising, and passed through for output fidelity.

### RetakePipeline

```python
from ltx_pipelines.retake import RetakePipeline

RetakePipeline(
    model_paths: ModelPaths,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    distilled: bool = True,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    video_path: str,
    prompt: str,
    start_time: float,
    end_time: float,
    seed: int,
    *,
    fps: float | None = None,
    negative_prompt: str = "",
    num_inference_steps: int = 40,
    video_guider_params: MultiModalGuiderParams | None = None,
    audio_guider_params: MultiModalGuiderParams | None = None,
    regenerate_video: bool = True,
    regenerate_audio: bool = True,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    max_batch_size: int = 1,
    sigmas: torch.Tensor | None = None,
    color_space: HDRColorSpace | None = None,
) -> tuple[Iterator[torch.Tensor], torch.Tensor, TilingConfig | None]
```

`start_time` must be less than `end_time`. For EXR folders, pass `fps`; for video files, leave it `None` and use container fps.

### T2AOneStagePipeline

```python
from ltx_pipelines.t2a_one_stage import T2AOneStagePipeline

T2AOneStagePipeline(
    model_paths: ModelPaths,
    loras: list[LoraPathStrengthAndSDOps],
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
)

pipe(
    prompt: str,
    negative_prompt: str,
    seed: int,
    frame_rate: float,
    num_inference_steps: int,
    audio_guider_params: MultiModalGuiderParams | MultiModalGuiderFactory,
    num_frames: int | AutoDuration = AutoDuration(...),
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    max_batch_size: int = 1,
    sigmas: torch.Tensor | None = None,
) -> Audio
```

This is audio-only: no height, width, image, or video output.

### DFRPipeline

```python
from ltx_pipelines.dfr_pipeline import DFRPipeline

DFRPipeline(
    model_paths: ModelPaths,
    distilled_lora: list[LoraPathStrengthAndSDOps],
    spatial_upsampler_path: str,
    loras: list[LoraPathStrengthAndSDOps],
    detailing_lora: list[LoraPathStrengthAndSDOps] | None = None,
    temporal_upsampler_path: str | None = None,
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    seed: int,
    height: int,
    width: int,
    frame_rate: float,
    images: list[ImageConditioningInput],
    num_frames: int | AutoDuration = AutoDuration(...),
    temporal_upsample_rounds: int = 0,
    tiling_config = AUTO_TILING,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    stage_1_sigmas: torch.Tensor = DISTILLED_SIGMAS,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
) -> tuple[Iterator[torch.Tensor], Audio, int, TilingConfig | None]
```

DFR derives keyframe slot positions internally. If `temporal_upsample_rounds > 0`, provide `temporal_upsampler_path` at construction.

### DubItPipeline

```python
from ltx_pipelines.dubit import DubItPipeline

DubItPipeline(
    model_paths: ModelPaths,
    spatial_upsampler_path: str,
    ic_lora: LoraPathStrengthAndSDOps,
    device: torch.device | None = None,
    quantization: QuantizationPolicy | None = None,
    registry: Registry | None = None,
    compilation_config: CompilationConfig | None = None,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    prompt_enhancer_gemma_root: str | None = None,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    prompt: str,
    seed: int,
    height: int,
    width: int,
    images: list[ImageConditioningInput],
    reference_video_path: str,
    reference_strength: float = 1.0,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    vae_dtype: torch.dtype | None = None,
    tiling_config = AUTO_TILING,
    stage_1_sigmas: torch.Tensor = DISTILLED_SIGMAS,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
    color_space: HDRColorSpace | None = None,
) -> tuple[Iterator[torch.Tensor], Audio, TilingConfig | None]
```

The reference video supplies frame count, fps, and audio identity. It must have an audio stream.

### HDRICLoraPipeline

```python
from ltx_pipelines.hdr_ic_lora import HDRICLoraPipeline

HDRICLoraPipeline(
    model_paths: ModelPaths,
    spatial_upsampler_path: str,
    hdr_lora: str | Path,
    text_embeddings_path: str | Path,
    device: torch.device | None = None,
    quantization: QuantizationPolicy | QuantizationKind | None = QuantizationKind.FP8_CAST,
    registry: Registry | None = None,
    hdr_lora_config: HdrLoraConfig | None = None,
    tiled_vae_encode_pixel_threshold: int = 393216,
    offload_mode: OffloadMode = OffloadMode.NONE,
    alloc_trim_strategy: AllocatorTrimStrategy = AllocatorTrimStrategy.TRIM,
    diffvae_optimization: DiffVAEMode = DiffVAEMode.CHUNKED_EAGER,
)

pipe(
    seed: int,
    height: int,
    width: int,
    num_frames: int,
    frame_rate: float,
    video_conditioning: list[tuple[str, float]],
    tiling_config = AUTO_TILING,
    high_quality_hdr: bool = False,
    stage2_tilings: list[TileCountConfig] | None = None,
    stage2_sigmas: list[list[float]] | None = None,
    stage2_use_ic_lora: list[bool] | None = None,
) -> torch.Tensor
```

The return tensor is linear HDR float with shape `[frames, height, width, channels]`. Tonemapping and EXR/video saving are caller responsibilities unless using the CLI.

## Programmatic planning tips

- Use `ModelPaths.from_split` for LTX-2.5 and only pass components the chosen pipeline will need; call accessors to validate required slots before instantiating.
- Keep two-stage resolutions multiples of 64 and one-stage/retake dimensions multiples of 32.
- Use `ImageConditioningInput(path, frame_idx, strength, crf=None)` instead of raw tuples for image inputs.
- For native HDR, pass `color_space=HDRColorSpace.SRGB_LINEAR`, `ACESCG`, or `ACESCCT`, set `vae_dtype` with the HDR helper when encoding output, and keep all conditioning media EXR or all SDR.
- For memory/backends, wire `quantization`, `offload_mode`, `compilation_config`, and `diffvae_optimization` at construction, but route installation and tradeoff decisions to `performance-backends`.
