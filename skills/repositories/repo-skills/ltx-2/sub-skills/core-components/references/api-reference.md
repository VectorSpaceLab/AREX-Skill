# Core API Reference

This reference lists verified public import paths and signatures for custom code against LTX-2 core components. Prefer these names over intuitive aliases: the repo uses `LinearQuadraticScheduler`, not `LinearQuadraticSchedule`, and `CFGGuider`, not `ClassifierFreeGuidance`.

## Package/module map

| Need | Import from | Notes |
|---|---|---|
| Diffusion schedulers | `ltx_core.components.schedulers` | `LTX2Scheduler`, `LinearQuadraticScheduler`, `BetaScheduler`; all return sigma tensors from `execute(...)`. |
| Guidance objects | `ltx_core.components.guiders` | `CFGGuider`, `STGGuider`, `LtxAPGGuider`, `MultiModalGuiderParams`, `MultiModalGuiderFactory`. |
| Noise and patchification | `ltx_core.components.noisers`, `ltx_core.components.patchifiers` | `GaussianNoiser`, `VideoLatentPatchifier`, `AudioPatchifier`, `get_pixel_coords`. |
| Latent and media shape types | `ltx_core.types` | `VideoPixelShape`, `VideoLatentShape`, `AudioLatentShape`, `SpatioTemporalScaleFactors`, `LatentState`, `Audio`, `GeneratedKeyframeLayout`. |
| Latent tools | `ltx_core.tools` | `VideoLatentTools`, `AudioLatentTools`; build/patchify/unpatchify `LatentState` objects. |
| Conditioning items | `ltx_core.conditioning` and `ltx_core.conditioning.types.*` | Image/keyframe/reference/mask/audio conditioning and generated keyframe slots. |
| Model builders/loaders | `ltx_core.loader` | `SingleGPUModelBuilder`, `SDOps`, `ModuleOps`, registry types, safetensors loaders, LoRA state wrappers. |
| Block streaming | `ltx_core.block_streaming` | `StreamingModelBuilder`, `BlockStreamingWrapper`, `DISK_CPU_SLOTS`. |
| Transformer configurators | `ltx_core.model.transformer` | `LTXModelConfigurator`, `LTXVideoOnlyModelConfigurator`, `LTXAudioOnlyModelConfigurator`, `LTXModel`, `Modality`, SDOps maps. |
| Video VAE configurators | `ltx_core.model.video_vae` | `VideoEncoderConfigurator`, `VideoDecoderConfigurator`, `ConvVideoDecoder`, `DiffusionVideoDecoder`, VAE SDOps maps and DiffVAE helpers. |
| Audio VAE/vocoder | `ltx_core.model.audio_vae` | `AudioEncoderConfigurator`, `AudioDecoderConfigurator`, `VocoderConfigurator`, SDOps maps. |
| Gemma text encoder | `ltx_core.text_encoders.gemma` | `LTXGemmaTextEncoder`, `EmbeddingsProcessor`, `GemmaTextEncoderConfigurator`, `build_gemma_tokenizer`, `get_gemma_ops`, `module_ops_from_gemma_root`. |
| Quantization policy | `ltx_core.quantization`, `ltx_core.quantization.fp8_cast`, `ltx_core.quantization.fp8_scaled_mm` | `QuantizationPolicy`, FP8 policy factories. Public CLI dispatch lives in `ltx_pipelines.utils.quantization_factory`. |
| Pipeline model paths | `ltx_pipelines.utils.model_paths` | `ModelPaths`, `model_paths_from_namespace`; the canonical split/monolith component contract. |
| Pipeline constructors | `ltx_pipelines` lazy exports or specific modules | Use for custom Python integration only; full runnable recipes route to `inference-pipelines`. |
| Media/HDR utilities | `ltx_pipelines.utils.media_io`, `ltx_core.hdr`, `ltx_core.color` | Safe decode/encode/resize/range/HDR helpers; actual generation recipes route to `inference-pipelines`. |

## Verified signatures: schedulers

```python
from ltx_core.components.schedulers import LTX2Scheduler, LinearQuadraticScheduler, BetaScheduler

LTX2Scheduler().execute(
    steps: int,
    latent: torch.Tensor | None = None,
    max_shift: float = 2.05,
    base_shift: float = 0.95,
    stretch: bool = True,
    terminal: float = 0.1,
    default_number_of_tokens: int = 4096,
    **_kwargs,
) -> torch.FloatTensor

LinearQuadraticScheduler().execute(
    steps: int,
    threshold_noise: float = 0.025,
    linear_steps: int | None = None,
    **_kwargs,
) -> torch.FloatTensor

BetaScheduler().execute(
    steps: int,
    alpha: float = 0.6,
    beta: float = 0.6,
) -> torch.FloatTensor
```

`LTX2Scheduler` adapts shift to token count when `latent` is provided by using `math.prod(latent.shape[2:])`. `BetaScheduler` may return fewer than `steps + 1` sigmas because duplicate timesteps are deduplicated.

## Verified signatures: guiders

```python
from ltx_core.components.guiders import (
    CFGGuider,
    STGGuider,
    LtxAPGGuider,
    MultiModalGuiderParams,
    MultiModalGuider,
    MultiModalGuiderFactory,
    create_multimodal_guider_factory,
)

CFGGuider(scale: float)
CFGGuider.delta(cond: torch.Tensor, uncond: torch.Tensor) -> torch.Tensor
CFGGuider.enabled() -> bool

STGGuider(scale: float)
STGGuider.delta(pos_denoised: torch.Tensor, perturbed_denoised: torch.Tensor) -> torch.Tensor
STGGuider.enabled() -> bool

LtxAPGGuider(scale: float, eta: float = 1.0, norm_threshold: float = 0.0)
LtxAPGGuider.delta(cond: torch.Tensor, uncond: torch.Tensor) -> torch.Tensor
LtxAPGGuider.enabled() -> bool

MultiModalGuiderParams(
    cfg_scale: float = 1.0,
    stg_scale: float = 0.0,
    stg_blocks: list[int] | None = <factory>,
    rescale_scale: float = 0.0,
    modality_scale: float = 1.0,
    skip_step: int = 0,
)

MultiModalGuiderFactory.constant(params: MultiModalGuiderParams, negative_context: torch.Tensor | None = None)
MultiModalGuiderFactory.from_dict(sigma_to_params: Mapping[float, MultiModalGuiderParams], negative_context: torch.Tensor | None = None)
MultiModalGuiderFactory.params(sigma: float | torch.Tensor) -> MultiModalGuiderParams
MultiModalGuiderFactory.build_from_sigma(sigma: float | torch.Tensor) -> MultiModalGuider
create_multimodal_guider_factory(params: MultiModalGuiderParams | MultiModalGuiderFactory, negative_context: torch.Tensor | None = None) -> MultiModalGuiderFactory
```

Use `MultiModalGuiderParams` or `MultiModalGuiderFactory` when adapting high-level pipeline denoisers; simple `CFGGuider`, `STGGuider`, and `LtxAPGGuider` are lower-level delta helpers.

## Verified signatures: noisers and patchifiers

```python
from ltx_core.components.noisers import GaussianNoiser
from ltx_core.components.patchifiers import VideoLatentPatchifier, AudioPatchifier, get_pixel_coords

GaussianNoiser(generator: torch.Generator)
GaussianNoiser.__call__(latent_state: LatentState, noise_scale: float = 1.0) -> LatentState

VideoLatentPatchifier(patch_size: int)
VideoLatentPatchifier.patch_size -> tuple[int, int, int]
VideoLatentPatchifier.get_token_count(tgt_shape: VideoLatentShape) -> int
VideoLatentPatchifier.patchify(latents: torch.Tensor) -> torch.Tensor
VideoLatentPatchifier.unpatchify(latents: torch.Tensor, output_shape: VideoLatentShape) -> torch.Tensor
VideoLatentPatchifier.get_patch_grid_bounds(output_shape: AudioLatentShape | VideoLatentShape, device: torch.device | None = None) -> torch.Tensor

AudioPatchifier(
    patch_size: int,
    sample_rate: int = 16000,
    hop_length: int = 160,
    audio_latent_downsample_factor: int = 4,
    is_causal: bool = True,
    shift: int = 0,
)
AudioPatchifier.get_token_count(tgt_shape: AudioLatentShape) -> int
AudioPatchifier.patchify(audio_latents: torch.Tensor) -> torch.Tensor
AudioPatchifier.unpatchify(audio_latents: torch.Tensor, output_shape: AudioLatentShape) -> torch.Tensor
AudioPatchifier.get_patch_grid_bounds(output_shape: AudioLatentShape | VideoLatentShape, device: torch.device | None = None) -> torch.Tensor

get_pixel_coords(latent_coords: torch.Tensor, scale_factors: SpatioTemporalScaleFactors, causal_fix: bool = False) -> torch.Tensor
```

## Verified signatures: shape/data types

```python
from ltx_core.types import (
    VideoPixelShape,
    VideoLatentShape,
    AudioLatentShape,
    SpatioTemporalScaleFactors,
    GeneratedKeyframeLayout,
    LatentState,
    Audio,
)

VideoPixelShape(batch: int, frames: int, height: int, width: int, fps: float)
SpatioTemporalScaleFactors(time: int, height: int, width: int)
SpatioTemporalScaleFactors.default() -> SpatioTemporalScaleFactors
SpatioTemporalScaleFactors.from_model_config(model_config: dict) -> SpatioTemporalScaleFactors

VideoLatentShape(batch: int, channels: int, frames: int, height: int, width: int)
VideoLatentShape.from_pixel_shape(shape: VideoPixelShape, latent_channels: int = 128, scale_factors: SpatioTemporalScaleFactors = VIDEO_SCALE_FACTORS) -> VideoLatentShape
VideoLatentShape.from_torch_shape(shape: torch.Size) -> VideoLatentShape
VideoLatentShape.to_torch_shape() -> torch.Size
VideoLatentShape.token_count() -> int
VideoLatentShape.mask_shape() -> VideoLatentShape
VideoLatentShape.upscale(scale_factors: SpatioTemporalScaleFactors = VIDEO_SCALE_FACTORS) -> VideoLatentShape

AudioLatentShape(batch: int, channels: int, frames: int, mel_bins: int)
AudioLatentShape.from_duration(batch: int, duration: float, channels: int = 8, mel_bins: int = 16, sample_rate: int = 16000, hop_length: int = 160, audio_latent_downsample_factor: int = 4) -> AudioLatentShape
AudioLatentShape.from_video_pixel_shape(shape: VideoPixelShape, channels: int = 8, mel_bins: int = 16, sample_rate: int = 16000, hop_length: int = 160, audio_latent_downsample_factor: int = 4) -> AudioLatentShape
AudioLatentShape.from_torch_shape(shape: torch.Size) -> AudioLatentShape

GeneratedKeyframeLayout(pixel_frame_indices: tuple[int, ...], tokens_per_keyframe: int, first_token: int)
GeneratedKeyframeLayout.num_keyframes -> int
GeneratedKeyframeLayout.num_tokens -> int
GeneratedKeyframeLayout.token_slice -> slice

LatentState(
    latent: torch.Tensor,
    denoise_mask: torch.Tensor,
    positions: torch.Tensor,
    clean_latent: torch.Tensor,
    attention_mask: torch.Tensor | None = None,
    keyframes_mask: torch.Tensor | None = None,
    generated_keyframe_layout: GeneratedKeyframeLayout | None = None,
    generated_keyframes: torch.Tensor | None = None,
    frozen: bool = False,
)
LatentState.clone() -> LatentState

Audio(waveform: torch.Tensor, sampling_rate: int)
Audio.to(**kwargs: object) -> Audio
```

## Verified signatures: latent tools and conditioning

```python
from ltx_core.tools import VideoLatentTools, AudioLatentTools
from ltx_core.conditioning import (
    VideoConditionByKeyframeIndex,
    VideoConditionByLatentIndex,
    VideoConditionByMask,
    VideoConditionByReferenceLatent,
    AudioConditionByReferenceLatent,
    ConditioningItemAttentionStrengthWrapper,
    VideoGeneratedKeyframeSlots,
)

VideoLatentTools(
    patchifier: VideoLatentPatchifier,
    target_shape: VideoLatentShape,
    fps: float,
    scale_factors: SpatioTemporalScaleFactors = SpatioTemporalScaleFactors(time=8, height=32, width=32),
    causal_fix: bool = True,
)
AudioLatentTools(patchifier: AudioPatchifier, target_shape: AudioLatentShape)

VideoConditionByReferenceLatent(latent: torch.Tensor, downscale_factor: int = 1, temporal_scale_factor: int = 1, strength: float = 1.0)
VideoConditionByKeyframeIndex(keyframes: torch.Tensor, frame_idx: int, strength: float, num_pixel_frames: int = 1)
VideoConditionByLatentIndex(latent: torch.Tensor, strength: float, latent_idx: int)
VideoConditionByMask(latent: torch.Tensor, mask: torch.Tensor, strength: float = 1.0)
AudioConditionByReferenceLatent(patchified: torch.Tensor, positions: torch.Tensor, strength: float = 1.0)
ConditioningItemAttentionStrengthWrapper(conditioning: ConditioningItem, attention_mask: float | torch.Tensor)
VideoGeneratedKeyframeSlots(pixel_frame_indices: Sequence[int], initial_keyframes: torch.Tensor | None = None)
```

## Verified signatures: loaders, state-dict ops, LoRA, and quantization

```python
from ltx_core.loader import SingleGPUModelBuilder, SDOps, ModuleOps, LoraPathStrengthAndSDOps
from ltx_core.quantization.policy import QuantizationPolicy
from ltx_core.quantization.fp8_cast import build_policy as build_fp8_cast_policy
from ltx_core.quantization.fp8_scaled_mm import build_policy as build_fp8_scaled_mm_policy

SingleGPUModelBuilder(
    model_class_configurator: type[ModelConfigurator[ModelType]],
    model_path: str | tuple[str, ...],
    model_sd_ops: SDOps | None = None,
    module_ops: tuple[ModuleOps, ...] = (),
    loras: tuple[LoraPathStrengthAndSDOps, ...] = (),
    model_loader: StateDictLoader | None = None,
    registry: Registry | None = None,
    lora_load_device: torch.device | None = None,
    fuse_rule: FuseRule = bf16_fuse_rule,
) -> None
SingleGPUModelBuilder.build(device: torch.device | None = None, dtype: torch.dtype | None = None, **kwargs: object) -> ModelType
SingleGPUModelBuilder.lora(lora_path: str, strength: float, sd_ops: SDOps) -> Self
SingleGPUModelBuilder.with_sd_ops(sd_ops: SDOps | None) -> Self
SingleGPUModelBuilder.with_module_ops(module_ops: tuple[ModuleOps, ...]) -> Self
SingleGPUModelBuilder.with_loras(loras: tuple[LoraPathStrengthAndSDOps, ...]) -> Self
SingleGPUModelBuilder.with_registry(registry: Registry) -> Self
SingleGPUModelBuilder.with_lora_load_device(device: torch.device) -> Self
SingleGPUModelBuilder.with_fuse_rule(fuse_rule: FuseRule) -> Self
SingleGPUModelBuilder.model_config() -> dict
SingleGPUModelBuilder.model_metadata() -> dict
SingleGPUModelBuilder.meta_model(metadata: dict, module_ops: tuple[ModuleOps, ...]) -> ModelType
SingleGPUModelBuilder.load_sd(paths: list[str], registry: Registry, device: torch.device | None, sd_ops: SDOps | None = None) -> StateDict

SDOps(name: str, mapping: tuple[ContentReplacement | ContentMatching | SDKeyValueOperation, ...] = (), allowed_keys: frozenset[str] | None = None) -> None
SDOps.with_replacement(content: str, replacement: str) -> SDOps
SDOps.with_matching(prefix: str = "", suffix: str = "", contains: str = "") -> SDOps
SDOps.with_additional_allowed_keys(keys: frozenset[str]) -> SDOps
SDOps.with_kv_operation(operation: KeyValueOperation, key_prefix: str = "", key_suffix: str = "") -> SDOps
SDOps.apply_to_key(key: str) -> str | None
SDOps.apply_to_key_value(key: str, value: torch.Tensor) -> list[KeyValueOperationResult]

ModuleOps(name: str, matcher: Callable[[nn.Module], bool], mutator: Callable[[nn.Module], nn.Module])
LoraPathStrengthAndSDOps(path: str, strength: float, sd_ops: SDOps)

QuantizationPolicy(
    sd_ops: SDOps | None = None,
    module_ops: tuple[ModuleOps, ...] = (),
    model_configurator: type[ModelConfigurator[LTXModel]] | None = None,
    fuse_rule: FuseRule = bf16_fuse_rule,
) -> None
build_fp8_cast_policy(checkpoint_path: str | pathlib.Path) -> QuantizationPolicy
build_fp8_scaled_mm_policy(checkpoint_path: str) -> QuantizationPolicy
```

`ltx_core.quantization.__init__` exports `QuantizationPolicy`, `UPCAST_DURING_INFERENCE`, `UpcastWithStochasticRounding`, `TRANSFORMER_LINEAR_DOWNCAST_MAP`, `fp8_cast_fuse_rule`, and `fp8_scaled_mm_fuse_rule`. The two `build_policy` factories are imported from their backend modules, not re-exported from the package root.

## Verified signatures: block streaming

```python
from ltx_core.block_streaming import StreamingModelBuilder, BlockStreamingWrapper, DISK_CPU_SLOTS

StreamingModelBuilder(
    model_class_configurator: type[ModelConfigurator[ModelType]],
    model_path: str | tuple[str, ...],
    model_sd_ops: SDOps | None = None,
    module_ops: tuple[ModuleOps, ...] = (),
    loras: tuple[LoraPathStrengthAndSDOps, ...] = (),
    model_loader: StateDictLoader | None = None,
    registry: Registry | None = None,
    fuse_rule: FuseRule = bf16_fuse_rule,
    blocks_attr: str = "",
    blocks_prefix: str = "",
    cpu_slots_count: int | None = None,
) -> None
StreamingModelBuilder.build(
    device: torch.device | None = None,
    dtype: torch.dtype | None = None,
    cpu_slots_count: int | None = None,
    gpu_slots_count: int | None = None,
    **_kwargs: object,
) -> BlockStreamingWrapper
BlockStreamingWrapper.teardown() -> None
```

`StreamingModelBuilder.build()` requires non-empty `blocks_prefix` and an explicit `dtype`. CPU-slot policy determines RAM streaming versus disk streaming; see [loading and LoRAs](loading-and-loras.md).

## Verified signatures: model configurators and SDOps maps

```python
from ltx_core.model.transformer import (
    LTXModelConfigurator,
    LTXVideoOnlyModelConfigurator,
    LTXAudioOnlyModelConfigurator,
    LTXV_MODEL_COMFY_RENAMING_MAP,
    LTXV_AUDIO_ONLY_MODEL_COMFY_RENAMING_MAP,
    Modality,
)
from ltx_core.model.video_vae import (
    VideoEncoderConfigurator,
    VideoDecoderConfigurator,
    VAE_ENCODER_COMFY_KEYS_FILTER,
    VAE_DECODER_COMFY_KEYS_FILTER,
    DIFFUSION_VAE_DECODER_COMFY_KEYS_FILTER,
    video_decoder_sd_ops_for_checkpoint,
    is_diffusion_video_vae,
)
from ltx_core.model.audio_vae import (
    AudioEncoderConfigurator,
    AudioDecoderConfigurator,
    VocoderConfigurator,
    AUDIO_VAE_ENCODER_COMFY_KEYS_FILTER,
    AUDIO_VAE_DECODER_COMFY_KEYS_FILTER,
    VOCODER_COMFY_KEYS_FILTER,
)

LTXModelConfigurator.from_metadata(metadata: dict, ops: TransformerOpsConfig = DEFAULT_TRANSFORMER_OPS) -> LTXModel
LTXVideoOnlyModelConfigurator.from_metadata(metadata: dict, ops: TransformerOpsConfig = DEFAULT_TRANSFORMER_OPS) -> LTXModel
LTXAudioOnlyModelConfigurator.from_metadata(metadata: dict, ops: TransformerOpsConfig = DEFAULT_TRANSFORMER_OPS) -> LTXModel
VideoEncoderConfigurator.from_metadata(metadata: dict) -> VideoEncoder
VideoDecoderConfigurator.from_metadata(metadata: dict) -> VideoDecoder
AudioEncoderConfigurator.from_metadata(metadata: dict) -> AudioEncoder
AudioDecoderConfigurator.from_metadata(metadata: dict) -> AudioDecoder
VocoderConfigurator.from_metadata(metadata: dict) -> Vocoder | VocoderWithBWE
is_diffusion_video_vae(checkpoint_path: str) -> bool
```

For transformer checkpoints with Comfy-style keys, pair the relevant configurator with `LTXV_MODEL_COMFY_RENAMING_MAP` (or the audio-only variant). For VAE/audio/vocoder component files, use the component-specific key filters.

## Verified signatures: ModelPaths

```python
from ltx_pipelines.utils.model_paths import ModelPaths, model_paths_from_namespace

ModelPaths(
    mode: Literal["monolith", "split"],
    transformer_path: str | None,
    text_encoder_path: str | None,
    video_vae_path: str | None,
    audio_vae_path: str | None,
    duration_head_path: str | None,
    embeddings_weight_paths: tuple[str, ...],
) -> None
ModelPaths.from_monolith(checkpoint_path: str, gemma_root: str | None = None, *, video_vae_path: str | None = None) -> ModelPaths
ModelPaths.from_split(
    *,
    transformer_path: str | None = None,
    text_encoder_path: str | None = None,
    video_vae_path: str | None = None,
    audio_vae_path: str | None = None,
    duration_head_path: str | None = None,
) -> ModelPaths
ModelPaths.transformer() -> str
ModelPaths.text_encoder() -> str
ModelPaths.video_vae() -> str
ModelPaths.audio_vae() -> str
ModelPaths.duration_head() -> str
model_paths_from_namespace(namespace: argparse.Namespace) -> ModelPaths
```

Typed accessors raise `ValueError` when the component slot is missing. `model_paths_from_namespace` raises `SystemExit` on split/monolith mixing or missing required monolith pair.

## Selected pipeline constructors for Python integration

These are constructor/call surfaces that often matter when custom code uses lower-level components. Use `inference-pipelines` for full recipes.

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
DistilledPipeline.__call__(
    prompt: str,
    seed: int,
    height: int,
    width: int,
    frame_rate: float,
    images: list[ImageConditioningInput],
    num_frames: int | AutoDuration = AutoDuration(min_seconds=1.0, max_seconds=20.0),
    vae_dtype: torch.dtype | None = None,
    tiling_config: TilingConfig | AutoTiling | None = AUTO_TILING,
    enhance_prompt: bool = False,
    enhance_static_cache: bool = False,
    stage_1_sigmas: torch.Tensor = DISTILLED_SIGMAS,
    stage_2_sigmas: torch.Tensor = STAGE_2_DISTILLED_SIGMAS,
    color_space: HDRColorSpace | None = None,
    generated_keyframes: int | Sequence[int] = 0,
) -> tuple[Iterator[torch.Tensor], Audio, int, TilingConfig | None]
```

Other verified pipeline class names exported by `ltx_pipelines` are `A2VidPipelineTwoStage`, `DFRPipeline`, `DubItPipeline`, `ICLoraPipeline`, `KeyframeInterpolationPipeline`, `RetakePipeline`, `T2AOneStagePipeline`, `TI2VidOneStagePipeline`, and `TI2VidTwoStagesPipeline`.

## Media and HDR utility signatures

```python
from ltx_pipelines.utils.media_io import (
    HDRColorSpace,
    ResizeMode,
    decode_image,
    decode_video_from_file,
    decode_audio_from_file,
    get_videostream_metadata,
    load_image_and_preprocess,
    read_exr,
    save_exr_tensor,
    encode_video,
    encode_audio,
    align_resolution,
    resize_and_center_crop,
    resize_and_reflect_pad,
    to_vae_range,
    from_vae_range,
    resolve_hdr_color_space,
    vae_dtype_for_hdr,
)
from ltx_core.hdr import HDRTransfer, to_acescct_working_space, to_hdr_linear

decode_image(image_path: str) -> np.ndarray
decode_video_from_file(path: str, device: DeviceLikeType, start_time: float = 0.0, max_duration: float | None = None) -> Generator[torch.Tensor]
decode_audio_from_file(path: str, device: torch.device, start_time: float = 0.0, max_duration: float | None = None) -> Audio | None
get_videostream_metadata(path: str, fps: float | None = None) -> VideoPixelShape
load_image_and_preprocess(image_path: str, height: int, width: int, dtype: torch.dtype, device: torch.device, crf: int, color_space: HDRColorSpace | None = None) -> torch.Tensor
read_exr(path: str | Path) -> torch.Tensor
save_exr_tensor(tensor: torch.Tensor, file_path: str | Path, half: bool = True, primaries: Primaries = Primaries.REC709, color_space: str = "sRGB") -> None
encode_video(video: torch.Tensor | Iterator[torch.Tensor], fps: int, audio: Audio | None, output_path: str, video_chunks_number: int, frame_converter: FrameConverter = yuv420p_bt709_converter_, crf: int = 19, preset: str = "veryfast", thread_count: int = 0, *, color_space: HDRColorSpace | None = None) -> Path | None
encode_audio(audio: Audio, output_path: str) -> None
align_resolution(width: int, height: int, resize_mode: ResizeMode, divisor: int = 64) -> tuple[int, int, int, int]
to_vae_range(x: torch.Tensor) -> torch.Tensor
from_vae_range(z: torch.Tensor) -> torch.Tensor
resolve_hdr_color_space(images: Iterable[object] = (), video_paths: Iterable[str | Path] = (), hdr: HDRColorSpace | None = None) -> HDRColorSpace | None
vae_dtype_for_hdr(hdr: HDRColorSpace | None, default: torch.dtype) -> torch.dtype
HDRTransfer.to_working_space(video: Tensor, *, source_primaries: Primaries = Primaries.REC709) -> Tensor
HDRTransfer.to_linear(working: Tensor, *, out_primaries: Primaries = Primaries.REC709) -> Tensor
to_acescct_working_space(video: Tensor, source_primaries: Primaries = Primaries.REC709) -> Tensor
to_hdr_linear(working: Tensor, transfer: HDRTransfer = HDRTransfer.LOGC3, out_primaries: Primaries = Primaries.REC709) -> Tensor
```

`read_exr`/`save_exr_tensor` require OpenImageIO in the environment. `to_vae_range` validates that values are in `[0, 1]` and raises if callers forgot to compress or clamp.
