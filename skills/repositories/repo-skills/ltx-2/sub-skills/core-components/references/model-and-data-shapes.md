# Model and Data Shapes

This reference records model/component concepts and tensor layouts that matter when writing custom LTX-2 code. It does not replace complete inference recipes; route full pipeline execution to `inference-pipelines`.

## Component concepts

| Concept | What it is | Typical APIs |
|---|---|---|
| Transformer | Dual-stream diffusion transformer for audio-video, video-only, or audio-only generation. Video stream is wider than audio stream; both use prompt context and diffusion timesteps. | `LTXModelConfigurator`, `LTXVideoOnlyModelConfigurator`, `LTXAudioOnlyModelConfigurator`, `LTXModel`, `Modality`. |
| Video VAE | Encodes/decodes `[B, 3, F, H, W]` pixels to/from latent grids. The default conv decoder is one pass; DiffVAE is a diffusion decoder selected from checkpoint metadata. | `VideoEncoderConfigurator`, `VideoDecoderConfigurator`, `VideoLatentShape`, `SpatioTemporalScaleFactors`. |
| Audio VAE and vocoder | Encodes audio mel-spectrograms to compact audio latents; decoder returns mel spectrogram; vocoder emits audio waveform. | `AudioEncoderConfigurator`, `AudioDecoderConfigurator`, `VocoderConfigurator`, `AudioLatentShape`, `Audio`. |
| Gemma text encoder | Tokenizer + Gemma backbone + feature extractor + modality-specific connectors. Video and audio receive different prompt embeddings. | `LTXGemmaTextEncoder`, `EmbeddingsProcessor`, `GemmaTextEncoderConfigurator`. |
| Schedulers/guiders/noisers | Sigma schedules, guidance deltas, and latent noising for diffusion loops. | `LTX2Scheduler`, `LinearQuadraticScheduler`, `BetaScheduler`, `MultiModalGuiderParams`, `GaussianNoiser`. |
| Patchifiers | Convert latent grids into transformer token sequences and back. Also provide RoPE patch coordinate bounds. | `VideoLatentPatchifier`, `AudioPatchifier`, `get_pixel_coords`. |
| Conditioning items | Modify `LatentState` by injecting clean latents, masks, reference tokens, keyframes, or generated keyframe slots. | `VideoConditionByLatentIndex`, `VideoConditionByKeyframeIndex`, `VideoConditionByReferenceLatent`, `VideoConditionByMask`, `AudioConditionByReferenceLatent`, `VideoGeneratedKeyframeSlots`. |
| Generated keyframe slots | Extra empty video tokens inserted at interior pixel-frame indices so the model can generate keyframes and condition around them. Requires checkpoint support. | `VideoGeneratedKeyframeSlots`, `GeneratedKeyframeLayout`, `LatentState.generated_keyframes`. |
| Block streaming | Model builder/wrapper that streams transformer block weights through small GPU buffers. | `StreamingModelBuilder`, `BlockStreamingWrapper`. |
| LoRA and quantization hooks | Loader policies that remap state dicts, fuse LoRAs, transform modules, or load FP8/NVFP4 weight layouts. | `SDOps`, `LoraPathStrengthAndSDOps`, `QuantizationPolicy`, FP8 `build_policy` functions. |

## Pixel, latent, and token layouts

### Video pixels

`VideoPixelShape(batch, frames, height, width, fps)` describes decoded video in pixel space. The source code notes BGR in the shape docstring, while most pipeline media helpers expose RGB frame tensors; when writing custom code, treat the type as geometric metadata and follow the specific decode/encode helper's channel convention.

Common pixel tensor shapes:

- Raw/decoded video for VAE: `[B, 3, F, H, W]`.
- Media helper frame chunks for encode: `[F, H, W, C]` float in `[0, 1]`.
- SDR conditioning after preprocessing: `[1, C, F, height, width]` in VAE range `[-1, 1]`.
- EXR read: `[H, W, 3]` float32 RGB, scene-linear, values may exceed `1.0`.

### Video latent grid

`VideoLatentShape(batch, channels, frames, height, width)` describes a 5-D tensor `[B, C, F, H, W]` in latent space. Defaults:

- Latent channels: `128`.
- Default VAE scale factors: `SpatioTemporalScaleFactors(time=8, height=32, width=32)`.
- `VideoLatentShape.from_pixel_shape(VideoPixelShape(...))` computes:
  - latent frames: `(pixel_frames - 1) // time + 1`;
  - latent height: `pixel_height // height`;
  - latent width: `pixel_width // width`.
- `VideoLatentShape.upscale()` computes pixel-space shape with:
  - pixel frames: `(latent_frames - 1) * time + 1`;
  - pixel height: `latent_height * height`;
  - pixel width: `latent_width * width`.

The frame formula implies the usual LTX causal video frame alignment: pixel frame count should be `8k + 1` for the default VAE. For example, `33` pixel frames map to `5` latent frames and decode back to `33` pixel frames.

### Audio latent grid

`AudioLatentShape(batch, channels, frames, mel_bins)` describes `[B, C, T, mel_bins]` audio latents. Defaults:

- Channels: `8`.
- Latent mel bins: `16`.
- Input sample rate used by shape helpers: `16000`.
- Hop length: `160`.
- Audio latent downsample factor: `4`.
- `AudioLatentShape.from_duration(...)` computes `frames = round(duration * sample_rate / hop_length / audio_latent_downsample_factor)`, i.e. about `25` latent frames per second with defaults.
- `AudioLatentShape.from_video_pixel_shape(...)` derives duration from `pixel_frames / fps`.

The audio VAE README summary says encoder shape is `[B, mel_bins, T] -> [B, 8, T/4, 16]` and decoder is `[B, 8, T, 16] -> [B, mel_bins, T*4]`; the vocoder converts mel spectrograms to a 24 kHz waveform.

## Patchification and positions

### Video patchifier

`VideoLatentPatchifier(patch_size)` sets `_patch_size = (1, patch_size, patch_size)`. Its core transform is:

```text
[B, C, F, H, W] -> [B, F * (H / patch_size) * (W / patch_size), C * patch_size * patch_size]
```

With `patch_size=1`, token count is `F * H * W` and token width is `C`. `unpatchify(...)` expects a `VideoLatentShape` and reverses the layout.

`get_patch_grid_bounds(output_shape, device)` returns `[B, 3, num_patches, 2]`, where axis `1` is `(time/frame, height, width)` and the last dimension stores inclusive-start/exclusive-end bounds for each patch. `get_pixel_coords(latent_coords, scale_factors, causal_fix)` multiplies these latent bounds by the VAE scale factors. With `causal_fix=True`, the first video frame's temporal span is shifted/clamped so the causal first latent frame corresponds to a single pixel frame rather than a full eight-frame span.

### Audio patchifier

`AudioPatchifier(patch_size=1, sample_rate=16000, hop_length=160, audio_latent_downsample_factor=4, is_causal=True, shift=0)` transforms:

```text
[B, C, T, mel_bins] -> [B, T, C * mel_bins]
```

For audio, token count is `T`. `get_patch_grid_bounds(...)` returns `[B, 1, T, 2]` timestamp bounds in seconds, computed from latent indices, sample rate, hop length, downsample factor, causal mode, and optional shift.

## LatentState layout

`LatentState` is the common object passed through noising, conditioning, patchification, and denoising:

| Field | Expected shape after patchification | Meaning |
|---|---|---|
| `latent` | `[B, T, D]` | Current noisy tokens. |
| `clean_latent` | `[B, T, D]` | Clean/source tokens used by conditioning and noiser interpolation. |
| `denoise_mask` | `[B, T, 1]` | `1` = full denoising/noising; `0` = keep clean. Conditioning strength often writes `1 - strength`. |
| `positions` | video `[B, 3, T, 2]`; audio `[B, 1, T, 2]` | RoPE coordinate bounds, converted to pixel/time units for video or seconds for audio. |
| `attention_mask` | optional `[B, T, T]` | Self-attention weights, `1` full attention and `0` no attention. |
| `keyframes_mask` | optional `[B, T, 1]` | Marks single-pixel-frame video tokens that receive learned keyframe absolute-position embeddings. |
| `generated_keyframe_layout` | `GeneratedKeyframeLayout` or `None` | Records where generated slot tokens were appended. |
| `generated_keyframes` | optional `[B, C, K, H, W]` latent | Extracted generated slots after clearing conditioning. |
| `frozen` | bool | Holds a stream fixed; pipeline code forces sigma to zero for frozen modalities. |

`VideoLatentTools.create_initial_state(...)` creates a zero or provided latent grid, patchifies it, converts positions, and marks the target's first latent frame in `keyframes_mask`. `LatentTools.clear_conditioning(...)` keeps the first target token count and removes appended conditioning tokens; if generated keyframe slots exist, their denoised content is extracted before dropping the extra tokens.

## Transformer Modality layout

`ltx_core.model.transformer.Modality` is the transformer input container:

| Field | Shape/role |
|---|---|
| `latent` | `[B, T, D]` patchified tokens. |
| `sigma` | `[B]` current sigma. |
| `timesteps` | `[B, T]` per-token timestep values. |
| `positions` | default `[B, n_pos_dims, T, 2]`; `n_pos_dims=3` for video and `1` for audio. Legacy `[B, n_pos_dims, T]` is accepted when `use_middle_indices_grid=False`. |
| `context` | text conditioning embeddings. |
| `context_mask` | optional text-token mask. |
| `attention_mask` | optional `[B, T, T]`. |
| `keyframes_mask` | optional `[B, T, 1]`; meaningful only for checkpoints with keyframe embedding support. |

`Modality.split(sizes)` splits tensor fields along batch and broadcasts `None`/bool fields.

## Text encoder output shapes

The Gemma text path produces separate embeddings for video and audio, even from the same prompt:

- Video context: `[B, seq_len, 4096]`.
- Audio context: `[B, seq_len, 2048]`.
- `EmbeddingsProcessorOutput(video_encoding, audio_encoding, attention_mask)` carries both modality contexts plus the attention mask.

This separation is important for audio-video prompts; do not reuse video context as audio context unless you are deliberately writing a video-only path.

## Conditioning item shape contracts

| Conditioning item | Input shape/contract | Effect |
|---|---|---|
| `VideoConditionByLatentIndex(latent, strength, latent_idx)` | `latent` unpatchified `[B, C, F_cond, H, W]`; batch/channels/H/W must match target. | Replaces clean tokens at latent frame index and writes denoise mask to `1 - strength`. |
| `VideoConditionByKeyframeIndex(keyframes, frame_idx, strength, num_pixel_frames=1)` | keyframes `[B, C, F, H, W]`; positions are offset by `frame_idx`. | Appends keyframe tokens as clean conditioning. If `num_pixel_frames == 1`, narrows temporal span to `[start, start+1)`. |
| `VideoConditionByReferenceLatent(latent, downscale_factor=1, temporal_scale_factor=1, strength=1.0)` | reference video latents `[B, C, F, H, W]`. | Appends reference tokens for IC-LoRA; position coordinates are spatially/temporally scaled to match training metadata. |
| `VideoConditionByMask(latent, mask, strength=1.0)` | `latent` `[B, C, F, H, W]`; `mask` `[B, F, H, W]` in unpatchified latent space. | Writes clean latents and denoise mask only where mask is `1`. |
| `AudioConditionByReferenceLatent(patchified, positions, strength=1.0)` | patchified `[B, T_ref, C]`; positions `[B, 1, T_ref, 2]`. | Appends reference audio tokens and updates attention mask. |
| `ConditioningItemAttentionStrengthWrapper(conditioning, attention_mask)` | Inner conditioning must append tokens; attention mask is scalar or `[B, M]`. | Adds/updates `[B, T, T]` self-attention mask for the appended tokens. |
| `VideoGeneratedKeyframeSlots(pixel_frame_indices, initial_keyframes=None)` | indices must be non-empty, non-negative, strictly increasing, and inside target pixel frames; optional initial latents `[B, C, K, H, W]`. | Appends fully denoised slot tokens and records a `GeneratedKeyframeLayout`. |

Reference and given-keyframe conditioning tokens are **not** marked in `keyframes_mask`. The target's first latent frame and generated keyframe slots are marked because they encode standalone pixel frames.

## Generated keyframe slots

`VideoGeneratedKeyframeSlots` is different from ordinary image/keyframe conditioning:

- It supplies empty fully-denoised tokens, not clean reference content, unless optional `initial_keyframes` is provided.
- Each slot uses one latent frame's worth of spatial tokens at the target resolution.
- Each slot corresponds to exactly one pixel frame at an interior target frame index.
- The class stores `GeneratedKeyframeLayout(pixel_frame_indices, tokens_per_keyframe, first_token)` so generated slot content can be extracted later.
- `pixel_frame_indices` must be non-empty, non-negative, strictly increasing, and the last index must be less than the target pixel frame count.
- `initial_keyframes`, when provided, must have shape `[B, C, K, H, W]`, `K == len(pixel_frame_indices)`, batch matching the latent state, and spatial shape matching the target latent spatial size.
- The state may receive generated slots only once; applying another `VideoGeneratedKeyframeSlots` raises an error.

Checkpoint requirement: the transformer config must set `use_keyframes_abs_pos_embedding=True`. Older checkpoints lack the learned marker embedding; generated slots would be unmarked tokens and are rejected by pipelines rather than silently degrading. If a user hits this, route to generated-keyframe-capable/DFR checkpoints or `inference-pipelines` for asset selection.

## Frame and spatial alignment checklist

Before writing custom code, assert these conditions explicitly:

1. Pixel frames fit the VAE grid: with default scale factors, use `F = 8k + 1` for generated video.
2. Pixel height/width are multiples of the selected VAE spatial scale factor, normally `32`; two-stage/pipeline resolution alignment may impose stricter multiples such as `64`.
3. Video latent tensors use `[B, C, F, H, W]`, not `[B, F, H, W, C]`.
4. Audio latent tensors use `[B, C, T, mel_bins]`, not waveform shape.
5. Patchified token tensors use `[B, T, D]` and masks use `[B, T, 1]` unless a helper explicitly documents another shape.
6. Video `positions` for the default transformer path are `[B, 3, T, 2]`; audio positions are `[B, 1, T, 2]`.
7. `attention_mask`, if present, is `[B, T, T]`, where `T` includes appended conditioning tokens.
8. `keyframes_mask`, if present, extends whenever tokens are appended. Conditioning items in `ltx_core.conditioning` do this for the built-in cases.
9. `clear_conditioning(...)` assumes appended extra tokens live after the target's token range. Custom conditioning that inserts tokens in the middle will break the invariant.

## Tiny CPU shape example

This example constructs shapes and patchifies zeros. It does not require checkpoints.

```python
import torch
from ltx_core.components.patchifiers import VideoLatentPatchifier, AudioPatchifier
from ltx_core.tools import VideoLatentTools, AudioLatentTools
from ltx_core.types import VideoPixelShape, VideoLatentShape, AudioLatentShape

pixel = VideoPixelShape(batch=1, frames=33, height=512, width=768, fps=24.0)
video_shape = VideoLatentShape.from_pixel_shape(pixel)
assert video_shape.to_torch_shape() == torch.Size([1, 128, 5, 16, 24])

video_tools = VideoLatentTools(VideoLatentPatchifier(1), video_shape, fps=pixel.fps)
state = video_tools.create_initial_state(device="cpu", dtype=torch.float32)
assert state.latent.shape == (1, video_shape.token_count(), 128)
assert state.positions.shape == (1, 3, video_shape.token_count(), 2)
assert state.keyframes_mask.shape == (1, video_shape.token_count(), 1)

audio_shape = AudioLatentShape.from_duration(batch=1, duration=pixel.frames / pixel.fps)
audio_tools = AudioLatentTools(AudioPatchifier(1), audio_shape)
audio_state = audio_tools.create_initial_state(device="cpu", dtype=torch.float32)
assert audio_state.latent.shape[:2] == (1, audio_shape.frames)
assert audio_state.positions.shape == (1, 1, audio_shape.frames, 2)
```

You can run an equivalent check with:

```bash
python sub-skills/core-components/scripts/inspect_core_api.py --tiny-shapes
```
