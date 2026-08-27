# Conditioning, HDR, and input constraints

Use this reference before building CLI/Python inference calls. Most user-visible failures come from mixing checkpoint layouts, invalid frame grids, incompatible media, or choosing the wrong HDR path.

## Prompt rules

- LTX-2 prompts work best as one literal chronological paragraph, similar to a cinematographer's shot description.
- Include action, subject appearance, environment, camera movement, lighting, and important audio/speech cues in order.
- Avoid vague lists of style tags as the only prompt. Keep prompts under roughly 200 words unless the user has a reason for a longer script.
- `--enhance-prompt` invokes prompt enhancement and may require `--prompt-enhancer-gemma-root` when the encoding text encoder is not suitable for generation. Do not silently add prompt enhancement when the user asked for a no-download/local-only command.

## Frame count and resolution

- Video/audio duration uses the causal VAE grid: `num_frames = 8*k + 1` for integer `k >= 0`.
- Common valid counts: `1`, `9`, `17`, `25`, `49`, `97`, `121`, `161`, `193`, `241`.
- Two-stage pipelines require output `height` and `width` divisible by 64 because stage 1 runs at half resolution and stage 2 upsamples.
- One-stage generation and retake source videos require dimensions divisible by 32.
- DFR temporal rounds return `(num_frames - 1) * 2**rounds + 1` frames and multiply playback fps by `2**rounds`.
- Higher frame counts, generated keyframes, HDR, and large resolutions increase token/VRAM cost. Use offload/quantization or lower frame/resolution if memory is constrained.

## Image conditioning

CLI syntax:

```bash
--image PATH FRAME_IDX STRENGTH [CRF]
```

Rules:

- `PATH` must be a still image file. PNG/JPEG are SDR; `.exr` is HDR and requires `--hdr`.
- `FRAME_IDX` selects the pixel frame to condition. Use `0` for first-frame I2V.
- `STRENGTH` controls conditioning influence. `1.0` is full/default strong conditioning.
- Optional `CRF` controls SDR H.264 recompression for conditioning. Omit it to let the pipeline choose the checkpoint-matched value; `0` means lossless.
- Multiple `--image` flags can be used for keyframes or multiple constraints.

Pipeline behavior:

- Standard TI2V and Distilled use replacing-latent image conditioning for strong frame control.
- `KeyframeInterpolationPipeline` uses guiding-latent conditioning for smoother transitions between keyframes.
- DFR accepts images but internally owns generated keyframe slot placement.

## Video conditioning and IC-LoRA

CLI syntax for `ltx_pipelines.ic_lora`:

```bash
--video-conditioning PATH STRENGTH
--conditioning-attention-mask MASK_PATH STRENGTH   # optional
```

Rules:

- Use `ICLoraPipeline` for whole-clip video-to-video/reference-video control.
- Provide an IC-LoRA with `--lora`; the pipeline reads LoRA metadata for reference downscale and temporal scale. Do not combine LoRAs that declare conflicting reference scales.
- `PATH` can be a video file or, in native HDR mode, a directory of EXR frames.
- Attention masks should be grayscale videos with values in `[0,1]`; the scalar strength multiplies the mask.
- `--skip-stage-2` decodes the half-resolution stage-1 result and skips spatial upsample/refinement.

Use `RetakePipeline`, not IC-LoRA, when the user wants only a time segment regenerated while preserving the rest.

## Generated keyframe slots

Generated keyframes are extra single-frame token slots the model creates inside the timeline. They reduce effective temporal compression at selected positions but cost additional attention tokens.

- CLI flag: `--num-generated-keyframes N`.
- Supported by `DistilledPipeline`, `TI2VidOneStagePipeline`, `TI2VidTwoStagesPipeline`, `TI2VidTwoStagesHQPipeline`, and their matching generated-keyframe-capable checkpoints.
- LTX-2.5 checkpoints support this. Older checkpoints without `use_keyframes_abs_pos_embedding` raise rather than silently ignore it.
- Slots are first-stage only for the standard pipelines; the effect is carried into stage 2.
- `DFRPipeline` does not expose `--num-generated-keyframes`; it derives slot positions from its own segment grid and re-attaches/seeds slots during temporal refinement.

## Audio inputs and outputs

### Audio-to-video

`A2VidPipelineTwoStage` uses:

```bash
--audio-path PATH [--audio-start-time SECONDS] [--audio-max-duration SECONDS]
```

The input audio is decoded and encoded as a frozen audio latent while video is denoised around it. The original waveform is passed through/returned to preserve fidelity. Ensure the requested `num_frames / frame_rate` duration matches the intended audio window.

### Text-to-audio

`T2AOneStagePipeline` is audio-only. It has no `--height`, `--width`, `--image`, or video output. Duration is still derived from `--num-frames / --frame-rate` or auto-duration.

### Dub-It

`DubItPipeline` requires `--reference-video` as an SDR video container with audio. It derives frame count and frame rate from the reference and snaps frame count to the nearest `8k+1`; the CLI intentionally has no `--num-frames` or `--frame-rate`.

## Retake windows

Retake regenerates only the `[start_time, end_time]` interval of an existing video/sequence.

Rules:

- `--start-time` must be less than `--end-time`.
- The source video frame count must satisfy `8k+1`.
- Source width and height must be multiples of 32.
- For video containers, do not pass `--frame-rate`; the container fps is used.
- For EXR-frame folders, pass `--frame-rate` because folders have no container fps.
- The prompt should describe only the replacement segment while respecting continuity at segment boundaries.

For an HDR retake, use the standard retake pipeline with `--hdr` and an EXR folder. Do not use the dedicated HDR IC-LoRA path unless the user requested HDR IC-LoRA video-to-video.

## Native HDR / EXR on standard pipelines

Standard pipelines that accept image/video conditioning can run native HDR/EXR with:

```bash
--hdr {SRGB_LINEAR,ACESCG,ACESCCT}
```

Color-space values:

| Value | Input meaning | Load behavior |
|---|---|---|
| `SRGB_LINEAR` | Scene-linear Rec.709/sRGB-tagged EXR | Compresses to ACEScct for the VAE. |
| `ACESCG` | Scene-linear ACEScg EXR | Compresses to ACEScct for the VAE. |
| `ACESCCT` | Already ACEScct log codes | Passes through without load-time transfer. |

Input rules:

- Any `.exr` still or EXR-frame folder requires `--hdr`.
- All image/video conditioning media in one run must be all EXR or all SDR. Do not mix EXR stills with PNG/JPEG stills or SDR videos.
- A single `.exr` file is valid for `--image`; video/sequence flags expect a video file or a directory of `*.exr` frames, not a single `.exr` file.
- Retake EXR folders require `--frame-rate`; retake video files forbid it.
- Dub-It has no native `--hdr` flag and rejects EXR reference inputs.

Output rules:

- With `--hdr`, standard pipelines write half-float EXR frames under an output-stem-derived EXR directory and a 10-bit BT.2020/HLG video master at `--output-path`.
- HDR VAE decode uses float32. Expect higher memory use than SDR.

## Dedicated HDR IC-LoRA

`HDRICLoraPipeline` / `ltx_pipelines.hdr_ic_lora` is separate from native `--hdr`.

Use it when the user has an HDR IC-LoRA workflow with precomputed text embeddings and wants linear HDR float output for EXR export/offline tonemapping.

CLI-specific constraints:

- `--input` is a single `.mp4` or a directory of `.mp4` videos.
- `--hdr-lora` and `--text-embeddings` are required.
- `--num-frames` must satisfy `(n - 1) % 8 == 0`.
- Width and height inferred from input must be divisible by 32.
- `--spatial-tile` controls tiled VAE decode; reduce it on lower-VRAM GPUs.
- `--high-quality` internally generates at 2x frame count and keeps every other frame; it is roughly 2x slower.
- This pipeline's Python return is a linear HDR float tensor; tonemapping and EXR saving are caller responsibilities unless using the CLI.

## Local asset checklist

For LTX-2.5 split DistilledPipeline, local paths usually include:

- Distilled transformer: `diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors`
- LTX text encoder: `text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors`
- Video VAE: `vae/ltx-2.5-video-vae-bf16.safetensors` or conv variant
- Audio VAE: `vae/ltx-2.5-audio-vae-bf16.safetensors`
- Spatial upsampler: `latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors`
- Optional duration head: `model_patches/ltx-2.5-duration-head-bf16.safetensors`

For guided two-stage/DFR, use the full/dev transformer and add the distilled LoRA. For temporal DFR, add the temporal upsampler. For IC-LoRA/Dub-It/HDRICLora, add the task-specific LoRA(s) and respect model-family compatibility.
