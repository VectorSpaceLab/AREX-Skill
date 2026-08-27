# Reference and Mask Preparation

## When to read

Read this when the task involves IC-LoRA reference data, inpainting masks, or audio/video conditioning inputs that are prepared before preprocessing.

## Reference data

For IC-LoRA-style training, the dataset must already include paired targets and references:

- `reference_video` for video IC-LoRA
- `reference_audio` for audio IC-LoRA
- both together for AV2AV IC-LoRA

The reference stream should describe the same content family as the target stream. It can be downscaled or temporally subsampled when the user needs a lighter conditioning signal, but the scale factors must match the preprocessing plan.

## Mask data

For inpainting tasks:

- `video_mask` points to the media used to create `video_masks/`
- `audio_mask` points to the media used to create `audio_masks/`

Mask tensors are thresholded at 0.5:

- values above 0.5 are conditioning tokens
- values at or below 0.5 are generated tokens

## Output layout

`inspect_precomputed_latents.py` expects a `.precomputed/` root that may contain:

- `latents/`
- `conditions/`
- `audio_latents/`
- `reference_latents/`
- `reference_audio_latents/`
- `video_masks/`
- `audio_masks/`

## Safe checks

Use `inspect_precomputed_latents.py` to compare a manifest against cached outputs without decoding media. It can summarize the expected directories and catch missing or mismatched samples.

## Common mistakes

- Running without the needed reference columns.
- Reusing a `.precomputed/` directory after changing the model family, trigger token, or scale factors.
- Expecting a downscaled reference to work with multiple resolution buckets and a non-1 training batch size.
- Forgetting that audio-only or mask-heavy modes still need the matching latents directory.

## Next step

If the reference/mask layout is correct, move to `captioning-and-preprocessing.md` and draft the preprocessing command with the bundled helper.
