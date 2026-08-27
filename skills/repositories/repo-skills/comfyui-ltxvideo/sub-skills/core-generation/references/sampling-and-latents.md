# Sampling and Latent Utilities

This reference explains the core sampler and latent utility behavior that future agents need for ComfyUI-LTXVideo graph planning and debugging.

## Guider and conditioning contract

Core sampler nodes consume a ComfyUI `GUIDER`, then extract positive and negative conditioning from it. The safe mental model is:

- The graph must have positive and negative conditioning before the sampler.
- The guider must preserve both sides as raw conditionings or original conditionings.
- A guider built from only one conditioning side can fail with errors about missing negative conds or missing raw conds.
- `LTXVTiledSampler` is stricter and raises an explicit error asking for an STG-style advanced guider when `raw_conds` are unavailable.

When the user's issue is prompt text, Gemma, saved conditioning, API credentials, multimodal guider parameters, or prompt enhancement, route to [prompt-conditioning](../../prompt-conditioning/SKILL.md). When the user wants STG/APG expert tuning, route to [advanced-control](../../advanced-control/SKILL.md).

## LTXVBaseSampler

Use `LTXVBaseSampler` for ordinary T2V/I2V single-pass denoising.

Required inputs:

- `model`, `vae`, `width`, `height`, `num_frames`.
- `guider`, `sampler`, `sigmas`, and `noise` from the standard ComfyUI sampling stack.

Optional image inputs:

- `optional_cond_images`: one or more images used for I2V/keyframe conditioning.
- `optional_cond_indices`: comma-separated frame indices matching the image batch length.
- `strength`: conditioning strength; the node writes a noise mask of `1 - strength` for encoded first-frame regions.
- `crop`, `crf`, and `blur`: preprocessing controls for conditioning images.

Behavior:

1. If no initialization latent is provided, the sampler creates an empty LTX video latent of the requested size and frame count.
2. If an optional conditioning image is assigned to index `0`, it is encoded through the VAE and placed into the first latent frames with a noise mask.
3. Other conditioning images become guide/keyframe conditionings.
4. The sampler can split sigmas into unguided, guided, and low-sigma phases when hidden start/end step controls are used.
5. It returns denoised latents plus updated positive/negative conditioning with guide crops removed.

Use this sampler when the user asks for a one-shot clip. Do not use it for long chunked generation unless the sequence fits memory and does not need continuation.

## LTXVInContextSampler

Use `LTXVInContextSampler` when guiding latents already exist and should condition the generated result from the start.

Key constraints:

- `guiding_latents` define the default latent dimensions and length unless `num_frames` is explicitly set.
- Optional image conditioning indices must match the number of supplied images.
- If keyframe images and guiding latents are both used, avoid conditioning image indices congruent to `1 mod 8`; the sampler raises a `multiple of 8 + 1` error for those positions.
- Optional negative-index latents can provide context before the generated latent range.

Typical use: video/reference-latent guided generation, detailer starts, or in-context variants of core video workflows. For IC-LoRA-specific semantics, route to specialized-workflows.

## LTXVExtendSampler

Use `LTXVExtendSampler` to append frames to an existing latent sequence.

Important inputs:

- `latents`: existing sequence to extend.
- `num_new_frames`: pixel frames to add; `-1` means infer from optional guiding latents.
- `frame_overlap`: pixel-frame overlap from the end of the previous sequence, minimum 16 and step 8 in the node UI.
- `strength`: how strongly the overlap latent conditions the new tile.
- Optional guiding latents, keyframes, reference latents, and negative-index latents.

Behavior:

1. Converts `frame_overlap` to latent frames through `vae.downscale_index_formula`.
2. Selects the tail overlap from existing latents.
3. Creates a new latent with overlap plus requested new frames.
4. Adds the tail overlap as a latent guide at index `0`.
5. Optionally adds guiding latents after the overlap and keyframe images.
6. Denoises, crops guide conditioning, drops the reinterpretation frame, and fuses the old and new latents with `LinearOverlapLatentTransition`.

Troubleshooting cue: if appended video jumps at the boundary, increase overlap and/or overlap conditioning strength before changing prompts.

## Latent frame math

LTX video latents use a temporal downscale factor provided by the VAE. Core code consistently uses this formula:

```text
pixel_frames = 1 + (latent_frames - 1) * time_scale_factor
latent_frames = (pixel_frames - 1) / time_scale_factor + 1  when divisible
```

For common LTX video VAEs this often means frame counts of `1 + 8*k`, but do not hard-code `8` when inspecting a live graph; read it from the VAE behavior if available.

Spatially, latent height and width map to pixel height and width through the VAE spatial scale factors. Tiled and guide nodes frequently compute pixel dimensions as latent dimensions multiplied by those scale factors.

## Guide and keyframe nodes

### LTXVAddGuideAdvanced

Use this for image/video keyframes at a target frame index.

- Resizes the image/video to latent-derived pixel dimensions.
- Applies LTX preprocessing with `crf` and optional blur.
- Uses `interpolation` and `crop` to control resizing.
- `frame_idx` supports negative values from the end. For guide videos longer than eight frames, choose a frame index divisible by eight; otherwise the underlying guide behavior rounds down or raises when the sequence would exceed latent length.
- Higher `strength` makes the keyframe more exact but can reduce motion freedom.

### LTXVAddGuideAdvancedAttention

This is the same keyframe guide pattern with `attention_strength` and optional `attention_mask`. Use only for basic per-guide strength/mask placement here; route deeper attention-control tuning to [advanced-control](../../advanced-control/SKILL.md) or IC-LoRA guide behavior to [specialized-workflows](../../specialized-workflows/SKILL.md).

### LTXVImgToVideoConditionOnly

Use this when an existing latent should be first-frame conditioned before sampling.

- Encodes the input image to VAE latents at the target latent size.
- Writes encoded frames into the beginning of the latent.
- Creates a `noise_mask` with `1 - strength` for the conditioned frames.
- `bypass=True` returns the latent unchanged; check this when I2V appears to do nothing.

## Latent selection, concatenation, and transition

### LTXVSelectLatents

- Selects an inclusive frame interval from a video latent.
- Supports negative indices.
- Clamps out-of-range indices to valid bounds.
- Preserves `noise_mask` when present.

Use it for tail overlaps, extracting guide latents, inspecting a chunk, or isolating a problematic frame range.

### LTXVAddLatents

- Concatenates latents along the frame dimension.
- Requires matching batch, channel, height, and width for video latents.
- Merges noise masks if present; fills absent mask regions with zeros.

If it fails, compare shapes except frame dimension first.

### LinearOverlapLatentTransition

- Blends the last `overlap` frames of one latent with the first `overlap` frames of another using linear coefficients.
- `axis=2` is the frame axis for video latents.
- Used by `LTXVExtendSampler` to avoid a hard temporal cut.

## Video latent noise masks

`LTXVSetVideoLatentNoiseMasks` applies masks to latent frames.

Accepted mask inputs:

- 2D: one mask `[H, W]`.
- 3D: multiple masks `[M, H, W]`.
- 4D: multiple masks with channel dimension `[M, C, H, W]`.

Behavior:

- Masks are resized to latent height/width.
- If fewer masks than frames are supplied, the last mask is reused for remaining frames.
- If an existing noise mask has the wrong frame count, it is reinitialized to the latent frame count.

Use this for core latent noise control only. Semantic mask preprocessing, inpaint, outpaint, and specialized mask workflows belong to specialized-workflows.

## Practical planning checklist

Before answering a core sampling question, identify:

1. Pixel width, height, and frame count.
2. Whether the user has prompt-only, first-image, multiple keyframes, existing video, or existing latents.
3. Whether model files include only a checkpoint or also latent upsamplers/LoRAs.
4. Whether the guider exposes positive and negative conditionings.
5. Whether frame indices are pixel-frame indices or latent-frame indices for the node in question.
6. Whether memory pressure occurs during loading, denoising, or decode; each uses a different fix.
