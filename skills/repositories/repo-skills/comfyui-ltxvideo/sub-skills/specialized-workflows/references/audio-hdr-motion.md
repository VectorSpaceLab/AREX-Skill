# Audio, HDR, and motion-track utilities

This reference covers the specialized utility nodes that wrap IC-LoRA workflows: audio-only text-to-audio, Dub-It speaker reference tokens, HDR LogC3 decode/EXR export, and sparse motion tracks.

## Text-to-audio (T2A) with `LTXVAudioOnlyModel`

LTX-2 is a joint audio/video transformer, so even an audio-only graph still has to satisfy the model's positional split of the latent into `[video, audio]`. The audio-only nodes make that safe and cheap.

Recipe:

1. Load the normal LTX audio/video model and audio VAE assets as the core graph expects.
2. Patch the model with `LTXVAudioOnlyModel` before sampling. The patch turns off the transformer's video stream and audio/video cross-attention flags, so audio denoising no longer depends on video tokens.
3. Create the audio latent with the normal LTX audio latent node for the requested duration/audio shape.
4. Add `LTXVAudioOnlyEmptyVideoLatent` as the required dummy video latent. It has no user parameters and always creates a minimal single-frame 64x64 placeholder latent.
5. Join dummy video latent + audio latent with the AV latent concat node, with the video latent in index 0 and audio latent in index 1.
6. Sample using the audio-only patched model.
7. Decode audio with the LTX audio VAE decode node and save/preview with a standard ComfyUI audio output node.

Important constraints:

- Do not tune the dummy video latent dimensions. It is fixed so future users do not accidentally make T2A slower or condition the audio on video.
- Remove or bypass `LTXVAudioOnlyModel` when returning to joint audio+video generation; otherwise the video stream and audio/video cross-attention remain disabled.
- Prompt text, negative prompts, and Gemma/API conditioning are owned by [prompt-conditioning](../../prompt-conditioning/SKILL.md).
- Sampler choice, duration/frame sizing, and low-VRAM sequencing are owned by [core-generation](../../core-generation/SKILL.md).

## Dub-It and audio reference tokens

Dub-It workflows use a source video/audio reference plus target dialogue prompt to regenerate lip movement and audio while preserving speaker identity.

`LTXVSetAudioRefTokens` is the key specialized node:

- Input: positive conditioning, negative conditioning, and an encoded audio latent.
- It patchifies the audio latent from `(batch, channels, time, frequency)` into reference audio tokens.
- It attaches those tokens to both positive and negative conditioning under `ref_audio`.
- The model treats them as context by prepending them at negative temporal positions, not as generated output frames.
- It returns `frozen_audio`, a copy of the input audio latent with `noise_mask=0`, for direct use when a later stage should preserve the audio instead of regenerating it.

Common two-stage Dub-It pattern:

1. Stage 1: condition on the target dialogue prompt, source video guide, and reference audio tokens. Generate base video+audio.
2. Stage 2: upsample/refine the video while reusing `frozen_audio` through the AV latent concat path so the audio remains fixed.
3. Keep target dialogue prompt and translation/rephrasing instructions in the prompt-conditioning path; keep two-stage upsampling and sampler details in core-generation.

Troubleshooting hints:

- If speaker identity drifts, check that `LTXVSetAudioRefTokens` updated both positive and negative conditioning and that downstream nodes use those returned conditioning outputs.
- If stage 2 changes audio unexpectedly, check that the `frozen_audio` output, not a newly noised audio latent, feeds the stage-2 AV concat.
- If the graph errors on latent type/shape, check video-only versus AV latent placement: IC-LoRA guides happen before AV concat; samplers consume the final latent shape expected by the core graph.

## HDR IC-LoRA decode and EXR export

HDR IC-LoRA workflows produce video frames in ARRI LogC3-compressed space. After VAE decode, use `LTXVHDRDecodePostprocess` to recover linear HDR values and produce an SDR preview.

Placement:

1. Load the HDR IC-LoRA and build the IC-LoRA guide as described in [IC-LoRA recipes](ic-lora-recipes.md).
2. Sample and VAE-decode normally. Tiled VAE decode is acceptable if the core graph needs it.
3. Place `LTXVHDRDecodePostprocess` immediately after VAE decode.
4. Use `tonemapped` for an SDR preview/output and `hdr_linear` for downstream HDR processing.

Node behavior:

- Input `image` is the VAE-decoded image tensor in standard ComfyUI `[0, 1]` range.
- The node reverses ComfyUI's decode scaling to `[-1, 1]`, applies LogC3 decompression, clamps linear HDR to a finite range, applies exposure in stops, then uses Reinhard tonemapping + sRGB conversion for the preview.
- Optional `save_exr` writes a frame sequence through OpenCV only when enabled. If `save_exr` is false, OpenCV is not needed for normal tonemapped/HDR tensor outputs.
- `half_precision=true` writes float16 EXR; false writes float32 EXR. This affects file size and downstream grading precision, not the in-graph `hdr_linear` tensor.

EXR preflight:

- `OPENCV_IO_ENABLE_OPENEXR=1` must be present before ComfyUI starts and before `cv2` imports. Setting it inside an already-running ComfyUI session is too late.
- Optional `opencv-python` must be installed for EXR writing.
- Run `../scripts/hdr_exr_preflight.py` from this sub-skill to check the environment without writing files.

Do not interpret a flat/washed SDR preview as proof that HDR failed. The `tonemapped` output is only a preview controlled by exposure; use `hdr_linear` or saved EXR frames for grading-aware downstream work.

## Sparse motion tracks

Motion-track workflows use drawn tracks as a visual control guide for the motion-track IC-LoRA.

### `LTXVSparseTrackEditor`

The editor is an interactive output node that overlays a spline editor on a reference image and writes JSON into hidden widgets.

Inputs:

- `image`: reference image used as the canvas background.
- `points_store`: JSON array of spline control points managed by the UI.
- `coordinates`: JSON array of interpolated coordinates, also managed by the UI.
- `points_to_sample`: number of points sampled along each spline; default evidence value is 121.

Interpolation rules:

- Empty spline -> no output points.
- One control point -> static repeated point for every sampled frame.
- Two control points -> linear interpolation.
- Three or more control points -> Catmull-Rom interpolation with duplicated endpoint padding.
- Coordinates are rounded to integer image-space pixels before being written to the `coordinates` JSON.

Editor UI behavior:

- The editor hides `points_store` and `coordinates` widgets and shows a canvas instead.
- Right click exposes actions such as add point, subdivide nearest segment, create new spline, create static spline, delete spline, and delete point.
- Coordinates are clamped to the reference image canvas while dragging.

### `LTXVDrawTracks`

`LTXVDrawTracks` converts track JSON into an image sequence for IC-LoRA conditioning.

Inputs:

- `tracks`: JSON string, usually emitted by `LTXVSparseTrackEditor`.
- `width`, `height`: output guide image dimensions. Match these to the guide/control resolution expected by the workflow.

Behavior:

- The node accepts nested/wrapped JSON structures and extracts lists of `{x, y}` point dictionaries.
- If no tracks parse, it returns a blank image sequence rather than raising.
- It renders colored circles with a trail history and downscales from a higher reference resolution for smoother tracks.
- It chooses CUDA when available and CPU otherwise; native ComfyUI execution is still deferred because the full motion-track workflow needs model assets.
- The rendered color channel order is intentionally swapped to match the motion-track IC-LoRA training data convention.

Static validation:

Use `../scripts/validate_sparse_tracks.py` to validate track JSON before loading it into ComfyUI, especially if the JSON was hand-edited or generated outside the UI.

Example validation command shape:

```bash
python ../scripts/validate_sparse_tracks.py --input tracks.json --width 512 --height 512 --require-same-length
```

This script reads only the supplied JSON and writes no files.
