# Core Generation Troubleshooting

Use this reference for workflow-specific failures after ComfyUI can see the ComfyUI-LTXVideo nodes. For install/import/backend problems, start with root [troubleshooting](../../../references/troubleshooting.md) and [model/backend requirements](../../../references/model-and-backend-requirements.md).

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Checkpoint/upscaler/LoRA not found | File missing or placed in wrong ComfyUI model folder | Check `models/checkpoints`, `models/latent_upscale_models`, `models/loras`, and `models/text_encoders` according to the recipe. |
| Two-stage graph cannot produce `LATENT_UPSCALE_MODEL` | Latent upscaler model absent or loaded by wrong loader | Put the required latent upscaler safetensors under `models/latent_upscale_models` and use the latent upscaler loader or low-VRAM variant. |
| Sampler says guider lacks negative conds/raw conds | Guider was built without both positive and negative conditionings or uses an incompatible guider object | Rebuild prompt conditioning with positive and negative sides; use a guider that exposes raw/original conds. Route prompt setup to prompt-conditioning. |
| `Number of optional cond images must match number of optional cond indices` | Image batch count and comma-separated indices differ | Provide exactly one index per conditioning image. |
| `multiple of 8 + 1` conditioning index error | Keyframe image index conflicts with guiding-latent alignment | Move the keyframe to another nearby frame, commonly a multiple of 8 or index 0 for first-frame I2V. |
| `Conditioning frames exceed the length of the latent sequence` | Guide video/keyframe starts too late for latent length | Shorten the guide, increase latent frame count, or move `frame_idx` earlier. |
| Latent add/concat fails with shape mismatch | Batch/channel/height/width differ between latents | Match all latent dimensions except frame count, or resize/re-encode before concatenating. |
| Looping sampler rejects AV latents | It expects video latents, not nested audio/video latents | Separate/select video latents for core looping; route audio-only/AV-special cases to specialized-workflows. |
| Looping sampler says guiding and target frame counts differ | `optional_guiding_latents` frame count differs from `latents` | Select, pad, extend, or regenerate guiding latents to the same latent frame count. |
| Tiled decode error: temporal tile length must be greater than temporal overlap + 1 | Invalid spatio-temporal decode chunk settings | Increase `temporal_tile_length` or lower `temporal_overlap`. |
| OOM during model loading | Multiple large assets load concurrently | Use `LowVRAM*` loaders and chain `dependencies`. |
| OOM during sampling | Clip is too large/long for model forward | Lower resolution/frame count, use spatial tiling, use temporal looping, or choose a smaller model/variant. |
| OOM during VAE decode | Denoise succeeded but decode is too large | Use `LTXVTiledVAEDecode` or `LTXVSpatioTemporalTiledVAEDecode`; consider `working_device=cpu`. |
| Visible spatial seams | Too little spatial overlap or too many tiny tiles | Increase overlap, reduce tile count if possible, and keep decode tiling separate from denoise tiling diagnosis. |
| Temporal jumps between chunks | Overlap too small or weakly conditioned | Increase temporal overlap and `temporal_overlap_cond_strength`; use `LinearOverlapLatentTransition`/extend behavior rather than hard concatenation. |
| Long output drifts or oversaturates | Accumulated latent statistics across chunks | Add light `adain_factor` or use normalizing/reference latents. |

## Missing model files

Core recipe folders:

- Main LTX checkpoint: `models/checkpoints`.
- Text encoder/Gemma assets: `models/text_encoders`; route details to prompt-conditioning.
- Latent upscalers for two-stage recipes: `models/latent_upscale_models`.
- Distilled LoRA or ordinary workflow LoRA: `models/loras`.

Recommended response pattern:

1. Ask which ComfyUI model folder contains the named file.
2. Confirm the exact filename selected in the loader node.
3. Confirm whether the graph is single-stage or two-stage; two-stage requires upscaler assets in addition to the checkpoint.
4. If low VRAM is involved, swap to low-VRAM loaders only after file placement is correct.

Do not advise downloading models automatically; the user must provide or authorize model acquisition.

## Wrong guider type or raw conditioning errors

Failure messages often appear when a graph connects a basic guider or a partially built prompt branch into a core sampler.

Fix sequence:

1. Confirm positive and negative conditioning exist. Even if the negative prompt is empty, the negative conditioning branch should still be present.
2. Use a guider compatible with the sampler. `LTXVBaseSampler`, `LTXVExtendSampler`, and `LTXVInContextSampler` can reconstruct raw conds from original positive/negative conds; `LTXVTiledSampler` expects `raw_conds` directly and suggests STG-style advanced guider usage when absent.
3. If the user is mixing multimodal guider parameters, Gemma API text encode, saved conditioning, or dynamic conditioning, route to prompt-conditioning for the upstream conditioning contract.
4. If the user intentionally uses STG/APG/PAG/FETA, route advanced parameter choices to advanced-control but keep core sampler placement here.

## Latent frame-count and index errors

Remember the two index domains:

- Pixel-frame indices: most image/keyframe UI fields and `num_frames` fields.
- Latent-frame indices: latent tensor dimension 2, `LTXVSelectLatents`, tiled decode temporal chunk lengths, and internal overlap calculations after dividing by the VAE time scale.

Common fixes:

- Prefer frame counts of the form `1 + time_scale*k` for video generation.
- For first-frame I2V, use index `0`.
- For guide videos longer than eight frames, align `frame_idx` to multiples of eight.
- When guiding latents are present, avoid image-conditioning indices that are `1 mod 8`.
- Use `LTXVSelectLatents` to trim or align guide/reference latents before concatenation/extension.
- If adding latents, match batch, channels, height, and width; only frame count may differ.

## Tiling seams and decode artifacts

Spatial seams:

- Increase `overlap`/`spatial_overlap` by one or two latent pixels.
- Reduce tile count if memory allows; very small tiles have less context.
- Ensure conditioning images are resized/cropped consistently with the tiled sampler's `crop` setting.

Temporal seams:

- Increase `temporal_overlap` and `temporal_overlap_cond_strength`.
- For continuation, prefer `LTXVExtendSampler` or `LTXVLoopingSampler` over manual latent concatenation.
- Use `adain_factor` or normalizing latents if chunks shift color or contrast.

Decode artifacts:

- Use `last_frame_fix` if only the tail frames show VAE boundary behavior.
- Use spatio-temporal tiled decode for long outputs; keep `temporal_tile_length > temporal_overlap + 1`.
- Decode on CPU only when the user accepts slower processing.

## VRAM failures

Ask where the OOM occurs:

1. **Load-time OOM:** use `LowVRAMCheckpointLoader`, `LowVRAMLatentUpscaleModelLoader`, or `LowVRAMAudioVAELoader` and connect `dependencies` from earlier loaders to later loaders.
2. **Sampling OOM:** reduce width/height/frames, switch from one-pass base sampling to tiled or looping sampling, or use smaller model variants.
3. **Decode OOM:** use tiled VAE decode or spatio-temporal tiled VAE decode; consider CPU decode and/or float16.
4. **Two-stage OOM:** lower stage-one resolution, reduce stage-two target, or verify the upscaler is latent upscaling rather than adding a pixel upscaler after an already-too-large latent.

Low-VRAM loaders only control loading order. They do not make a denoise step fit if the active model, latent, and attention workload exceed available memory.
