# Tiling, Looping, and Low-VRAM Operation

Use this reference when the user wants high-resolution output, long video, tiled VAE decode, or lower peak memory during model loading/generation.

## Distinguish the memory bottleneck

| Bottleneck | Symptom | Preferred core fix |
| --- | --- | --- |
| Model load peak | OOM before sampling starts, often while loading checkpoint/audio VAE/upscaler | Chain `LowVRAM*` loaders with `dependencies`. |
| Denoising large frames | OOM inside sampler/model forward | Reduce dimensions/frame count, use `LTXVTiledSampler`, or use `LTXVLoopingSampler` with spatial tiles. |
| Denoising long clips | OOM or timeout with many frames | Use `LTXVLoopingSampler` temporal chunks. |
| VAE decode | Sampling finishes but decode OOMs | Use `LTXVTiledVAEDecode` or `LTXVSpatioTemporalTiledVAEDecode`, optionally decode on CPU. |
| Visible seams | Output has spatial/temporal tile boundaries | Increase overlap, use normalization, and decode with matching tiled strategy. |

## LTXVTiledSampler

Use `LTXVTiledSampler` for one clip whose spatial size is too large to denoise as a single latent.

Key inputs:

- `horizontal_tiles`, `vertical_tiles`: number of spatial divisions, each 1 to 6.
- `overlap`: latent-pixel overlap between tiles, 1 to 8.
- `latents_cond_strength`: strength for latent self-guidance when `boost_latent_similarity` is enabled.
- `boost_latent_similarity`: when image conditioning is present, guides middle and last latent frames to improve consistency.
- `optional_cond_images`, `optional_cond_indices`, `images_cond_strengths`: per-keyframe conditioning for tiles.

Behavior:

1. Splits the latent height/width into overlapping tiles.
2. Scales conditioning images to the full target pixel size, then crops each tile's image region.
3. Runs the sampler on each spatial tile.
4. Blends tile outputs with linear overlap weights.
5. Returns both `output` and `denoised_output` latent dictionaries.

Parameter cues:

- Start with `1×1` tiles. Increase tile count only when memory or resolution requires it.
- Use overlap `1` to `2` latent pixels for moderate tiling; increase overlap for seam reduction.
- More tiles reduce per-tile memory but increase runtime and can increase seam risk.
- If keyframes are used, make sure the number of indices and strengths matches the number of images; missing strengths repeat the last value.

## LTXVLoopingSampler

Use `LTXVLoopingSampler` for long video, high resolution, evolving prompts per temporal tile, or V2V/detailer workflows that should process chunks.

Required concepts:

- `latents` define the target latent dimensions and total timeline. They may be empty latents, partial denoise latents, or prepared V2V latents.
- `temporal_tile_size` is in pixel frames in the UI. Internally it is divided by the VAE temporal scale.
- `temporal_overlap` is in pixel frames in the UI. It conditions a new chunk on the end of the previous chunk.
- `horizontal_tiles`, `vertical_tiles`, and `spatial_overlap` enable spatial tiling inside the looping workflow.
- `optional_positive_conditionings` can provide one positive conditioning per temporal tile, often from `MultiPromptProvider`; prompt details route to prompt-conditioning.

Typical starting points:

| Goal | Initial settings |
| --- | --- |
| Standard long clip | `temporal_tile_size` 80, `temporal_overlap` 24, `horizontal_tiles=1`, `vertical_tiles=1`. |
| Smoother temporal boundaries | Set overlap around 25-33% of tile size and increase `temporal_overlap_cond_strength`. |
| High-res long clip | Add spatial tiling, for example `2×1` or `2×2`, with `spatial_overlap` 1-3 latent pixels. |
| Reduce long-run color drift | Use `adain_factor` around 0.1-0.3 and/or provide `optional_normalizing_latents`. |
| Narrative progression | Use per-tile positive conditionings; if fewer prompts than chunks are provided, repeat the last prompt. |

Important constraints and caveats:

- The node currently rejects audio/video nested latents; use video latents only for this core route.
- If `optional_guiding_latents` are supplied, they must have the same latent frame count as `latents` before any dilation.
- Guiding latent height/width ratios to target latents must be integer ratios; the node dilates guiding latents to match.
- Keyframe indices are mapped to temporal tiles. Out-of-range keyframes are skipped. Negative keyframe indices count from the effective end of the video.
- When guiding latents and conditioning images are both used, avoid keyframe positions that trigger the `multiple of 8 + 1` restriction inside in-context/extend sampling.

## MultiPromptProvider

`MultiPromptProvider` takes pipe-separated prompts, encodes each prompt with the connected `CLIP`, and returns a list of conditionings for `LTXVLoopingSampler`.

Usage cues:

- Separate prompts with `|`, not newlines, for the runtime parser.
- One prompt is used per temporal tile.
- If there are fewer prompts than chunks, the last conditioning is reused.
- If there are too many prompts, extra prompts are ignored.

Prompt wording, Gemma token limits, and API/local encoder decisions belong to prompt-conditioning.

## Tiled VAE decode

### LTXVTiledVAEDecode

Use when sampling succeeds but VAE decode OOMs or when output frames are large.

Key inputs:

- `horizontal_tiles`, `vertical_tiles`: spatial tiles for decode.
- `overlap`: latent-pixel overlap; output overlap is scaled by the VAE spatial factor.
- `last_frame_fix`: repeats the final latent frame before decode, then discards the extra decoded tail. Use when the last decoded frames show a VAE boundary artifact.
- `working_device`: `auto` keeps decode on latent device; `cpu` lowers GPU memory but is slower.
- `working_dtype`: `auto`, `float16`, or `float32`; `float16` can reduce memory, `float32` can reduce precision artifacts.

### LTXVSpatioTemporalTiledVAEDecode

Use for long latent sequences where spatial-only decode is still too large.

Key inputs:

- `spatial_tiles`: same count for horizontal and vertical tiles.
- `spatial_overlap`: latent-pixel overlap between spatial tiles.
- `temporal_tile_length`: latent-frame chunk length, including overlap.
- `temporal_overlap`: latent-frame overlap between temporal decode chunks.
- `last_frame_fix`, `working_device`, and `working_dtype` behave like tiled decode.

Constraints:

- `temporal_tile_length` must be greater than `temporal_overlap + 1`.
- Later chunks drop their first decoded frame and blend the temporal overlap into the already-written output.
- Temporal decode overlap is in latent frames, not pixel frames; it is scaled by the VAE time factor for output blending.

## Low-VRAM loaders

This repo provides loader variants with a `dependencies` input. The dependency value can be any previous loader output; its purpose is to force ComfyUI execution order so models are loaded sequentially rather than all peaking simultaneously.

Loader families:

- `LowVRAMCheckpointLoader`: checkpoint loader with `dependencies`; returns model, CLIP, and VAE like the standard checkpoint loader.
- `LowVRAMAudioVAELoader`: loads an LTX audio VAE checkpoint and returns `audio_vae`; relevant when AV workflows are present.
- `LowVRAMLatentUpscaleModelLoader`: latent upscaler loader with `dependencies`; useful in two-stage workflows.

Sequencing pattern:

```text
LowVRAMCheckpointLoader -> downstream model/clip/vae consumers
   dependency output -> LowVRAMLatentUpscaleModelLoader -> stage-two upsampler
      dependency output -> LowVRAMAudioVAELoader if the workflow also needs audio VAE
```

The dependency chain does not reduce the model's active memory during the actual denoise step. If OOM occurs during sampling, reduce dimensions/frame count, tile/chunk the workload, or use smaller model variants.

## Seam reduction checklist

1. Identify whether seam is temporal, spatial denoise, or VAE decode.
2. Increase temporal overlap for chunk boundaries; increase spatial overlap for tile boundaries.
3. Use overlap around one-quarter to one-third of temporal tile size for long videos.
4. Add light `adain_factor` or normalizing latents if long videos drift in color/statistics.
5. Avoid excessive tile counts; too many small tiles can create more visible local inconsistency.
6. Match sampler tiling and decode tiling only when both stages need it; tiled decode alone cannot fix denoise seams.
