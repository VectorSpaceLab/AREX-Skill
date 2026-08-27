# CLI reference

All pipeline CLIs are Python modules under `ltx_pipelines`. Use `python -m <module> --help` to inspect installed flags without generation. The bundled `../scripts/inspect_pipeline_cli.py` helper limits this to known modules and defaults to safe help printing.

## Module catalog

| Module | Pipeline class | Required special flags | Notable optional flags |
|---|---|---|---|
| `ltx_pipelines.distilled` | `DistilledPipeline` | model layout flags, `--prompt`, `--output-path`, `--spatial-upsampler-path` | `--image`, `--num-generated-keyframes`, `--offload`, `--quantization`, `--compile`, `--hdr`, `--auto-duration` |
| `ltx_pipelines.ti2vid_two_stages` | `TI2VidTwoStagesPipeline` | model layout flags, `--prompt`, `--output-path`, `--distilled-lora`, `--spatial-upsampler-path` | CFG/STG guidance flags, `--image`, `--num-generated-keyframes`, `--hdr` |
| `ltx_pipelines.ti2vid_two_stages_hq` | `TI2VidTwoStagesHQPipeline` | same as `ti2vid_two_stages` | `--distilled-lora-strength-stage-1`, `--distilled-lora-strength-stage-2`, `--num-generated-keyframes` |
| `ltx_pipelines.ti2vid_one_stage` | `TI2VidOneStagePipeline` | model layout flags, `--prompt`, `--output-path` | guidance flags, `--image`, `--num-generated-keyframes`, no spatial upsampler |
| `ltx_pipelines.ic_lora` | `ICLoraPipeline` | distilled model layout flags, `--prompt`, `--output-path`, `--spatial-upsampler-path`, `--video-conditioning PATH STRENGTH`, `--lora` IC-LoRA | `--conditioning-attention-mask MASK_PATH STRENGTH`, `--skip-stage-2`, `--image`, `--hdr` |
| `ltx_pipelines.keyframe_interpolation` | `KeyframeInterpolationPipeline` | model layout flags, `--prompt`, `--output-path`, multiple `--image PATH FRAME STRENGTH`, `--distilled-lora`, `--spatial-upsampler-path` | guidance flags, `--hdr` |
| `ltx_pipelines.a2vid_two_stage` | `A2VidPipelineTwoStage` | model layout flags, `--prompt`, `--output-path`, `--distilled-lora`, `--spatial-upsampler-path`, `--audio-path` | `--audio-start-time`, `--audio-max-duration`, `--image`, guidance flags, `--hdr` |
| `ltx_pipelines.retake` | `RetakePipeline` | distilled model layout flags, `--prompt`, `--output-path`, `--video-path`, `--start-time`, `--end-time` | `--frame-rate` for EXR folders only, `--hdr`, `--offload`, `--quantization` |
| `ltx_pipelines.hdr_ic_lora` | `HDRICLoraPipeline` | `--input`, `--output-dir`, `--hdr-lora`, `--text-embeddings`, `--distilled-checkpoint-path`, `--spatial-upsampler-path` | `--video-vae-path`, `--num-frames`, `--spatial-tile`, `--skip-mp4`, `--high-quality`, `--offload` |
| `ltx_pipelines.dubit` | `DubItPipeline` | distilled model layout flags, `--prompt`, `--output-path`, `--spatial-upsampler-path`, `--reference-video`, exactly one Dub-It `--lora` | `--reference-strength`, `--image`; no `--num-frames`, no `--frame-rate`, no `--hdr` |
| `ltx_pipelines.t2a_one_stage` | `T2AOneStagePipeline` | model layout flags, `--prompt`, `--output-path` | audio guidance flags, `--num-frames`, `--auto-duration`, `--frame-rate`; no video/image flags |
| `ltx_pipelines.dfr_pipeline` | `DFRPipeline` | model layout flags, `--prompt`, `--output-path`, `--distilled-lora`, `--spatial-upsampler-path` | `--detailing-lora`, `--temporal-upsampler-path`, `--temporal-upsample-rounds {0,1,2}`, `--image`; no `--num-generated-keyframes` |

## Checkpoint-layout flag rules

### LTX-2.5 split layout

Split mode is selected by any pack-identifying flag: `--transformer-path`, `--text-encoder-path`, `--audio-vae-path`, or `--duration-head-path`. In split mode:

- Use `--transformer-path` for the DiT/transformer `.safetensors`.
- Use `--text-encoder-path` for the single-file LTX Gemma + projection checkpoint. Do **not** add `--gemma-root`.
- Use `--video-vae-path` for the video VAE. Pipelines that encode/decode video need it.
- Use `--audio-vae-path` for audio generation/decoding. Video pipelines in this package commonly decode audio too, so include it for normal audio-video output.
- Use `--duration-head-path` only when using auto-duration from LTX-2.5 duration head; otherwise pass explicit `--num-frames`.
- Add `--spatial-upsampler-path` for every two-stage/upscaling pipeline.
- Add `--temporal-upsampler-path` only for DFR when `--temporal-upsample-rounds` is greater than 0.

### LTX-2.3 or legacy monolith layout

Monolith mode uses:

```bash
--checkpoint-path path/to/full-or-dev.safetensors --gemma-root path/to/gemma-dir
```

or for distilled-only CLIs:

```bash
--distilled-checkpoint-path path/to/distilled.safetensors --gemma-root path/to/gemma-dir
```

Rules:

- Do not pass split pack flags with `--checkpoint-path`, `--distilled-checkpoint-path`, or `--gemma-root`.
- `--video-vae-path` is a shared override: it can be used in monolith mode to override the VAE bundled in the fat checkpoint.
- LTX-2.3 LoRAs and upsamplers are not interchangeable with LTX-2.5 component files.

## Common flags

| Flag | Meaning | Practical guidance |
|---|---|---|
| `--prompt TEXT` | Positive prompt | Use one chronological, literal cinematography-style paragraph. Keep it concise and concrete. |
| `--negative-prompt TEXT` | Negative prompt for guided pipelines | Distilled-only modules generally do not expose/need CFG negative prompts. |
| `--output-path PATH` | Output file path | Standard video modules write MP4; `t2a_one_stage` writes audio; HDR standard mode also writes an EXR folder beside the output stem. |
| `--seed INT` | Reproducibility | Keep fixed while debugging flags. |
| `--height`, `--width` | Output size | Two-stage pipelines require multiples of 64; one-stage and retake source dimensions require multiples of 32. |
| `--num-frames INT` | Output frame count | Must satisfy `num_frames = 8*k + 1` for video/audio duration. Examples: 1, 9, 17, 25, 97, 121, 161, 193. |
| `--auto-duration MIN MAX` | Let DurationHead choose duration | Requires a model/component with duration head; explicit `--num-frames` wins. |
| `--frame-rate FPS` | Playback fps / duration basis | For retake, set only for EXR folders; video files use container fps. |
| `--image PATH FRAME_IDX STRENGTH [CRF]` | Image conditioning | Repeatable. Use still image files, not folders. `.exr` stills require `--hdr`. |
| `--video-conditioning PATH STRENGTH` | IC-LoRA reference video or EXR folder | `ic_lora` only. Repeatable in parser/action, subject to LoRA compatibility. |
| `--conditioning-attention-mask MASK STRENGTH` | Spatial/temporal IC-LoRA attention mask | `ic_lora` only; mask video should be grayscale values in `[0,1]`. |
| `--audio-path PATH` | Input audio for A2V | `a2vid_two_stage` only; combine with optional start/max duration. |
| `--reference-video PATH` | Dub-It reference container | Must be SDR video file with audio; no EXR folder. |
| `--lora PATH [STRENGTH]` | Apply LoRA | Repeatable except Dub-It expects exactly one Dub-It IC-LoRA. Default strength is 1.0. |
| `--distilled-lora PATH [STRENGTH]` | Stage-2 distilled refinement LoRA | Required by guided two-stage, keyframe interpolation, A2V, and DFR. |
| `--offload {none,cpu,disk}` | Weight streaming/offload | Memory relief; route detailed backend choice to `performance-backends`. CLI help may print enum spellings; user values are lower-case strings. |
| `--quantization {fp8-cast,fp8-scaled-mm,nvfp4-cast,nvfp4-prequant}` | Transformer quantization | `fp8-cast` is common for bf16 checkpoints. NVFP4 paths need specific hardware/backends; route details to `performance-backends`. |
| `--compile [KEY=VALUE ...]` | Enable `torch.compile` | Good for repeated runs after warmup; not a fix for bad flags. |
| `--diffvae-optimization MODE` | Diffusion VAE decode mode | Optional backend/performance surface. Missing backend fallback belongs to `performance-backends`. |
| `--hdr {SRGB_LINEAR,ACESCG,ACESCCT}` | Native HDR/EXR mode | Required for any EXR input on standard pipelines; writes EXR frames plus HLG master. |
| `--num-generated-keyframes N` | Extra generated interior keyframe slots | Supported by Distilled/TI2V/one-stage/HQ. Requires keyframe-capable transformer. Not used by DFR. |

## Command recipes

These commands show shape and flag compatibility. Replace all placeholder paths with existing local files. They do not imply model downloads.

### Fastest LTX-2.5 split I2V with FP8/offload

This is the common quick path for a local image-to-video run. It uses `DistilledPipeline`, split flags, image conditioning, spatial upsampler, FP8 cast, and CPU offload; it deliberately avoids `--gemma-root`.

```bash
python -m ltx_pipelines.distilled \
  --transformer-path models/ltx-2.5/diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors \
  --text-encoder-path models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
  --video-vae-path models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
  --audio-vae-path models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
  --spatial-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
  --prompt "A precise chronological description of the shot." \
  --image assets/start.png 0 1.0 \
  --num-frames 121 --height 1024 --width 1536 --frame-rate 24 \
  --seed 42 --quantization fp8-cast --offload cpu \
  --output-path outputs/i2v.mp4
```

Use `../scripts/build_distilled_command.py` to produce this safely from local paths.

### Guided two-stage LTX-2.5 split with generated keyframes

```bash
python -m ltx_pipelines.ti2vid_two_stages \
  --transformer-path models/ltx-2.5/diffusion_models/ltx-2.5-22b-dev-transformer-bf16.safetensors \
  --text-encoder-path models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
  --video-vae-path models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
  --audio-vae-path models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
  --spatial-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
  --distilled-lora models/ltx-2.5/loras/ltx-2.5-22b-distilled-lora-450-bf16.safetensors 0.8 \
  --prompt "A detailed shot description." \
  --negative-prompt "low quality, artifacts" \
  --num-frames 121 --num-generated-keyframes 4 \
  --video-cfg-guidance-scale 3.0 --audio-cfg-guidance-scale 7.0 \
  --output-path outputs/guided.mp4
```

### Video-to-video IC-LoRA

```bash
python -m ltx_pipelines.ic_lora \
  --transformer-path models/ltx-2.5/diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors \
  --text-encoder-path models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
  --video-vae-path models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
  --audio-vae-path models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
  --spatial-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
  --lora models/ic-lora/control.safetensors 1.0 \
  --video-conditioning assets/control.mp4 1.0 \
  --prompt "Transform the reference motion into a cinematic scene." \
  --num-frames 121 --height 1024 --width 1536 \
  --output-path outputs/ic_lora.mp4
```

### Keyframe interpolation

```bash
python -m ltx_pipelines.keyframe_interpolation \
  --checkpoint-path models/ltx-2.3/ltx-2.3-22b-dev.safetensors \
  --gemma-root models/gemma-3-12b-it-qat-q4_0-unquantized \
  --distilled-lora models/ltx-2.3/ltx-2.3-22b-distilled-lora-384-1.1.safetensors 0.8 \
  --spatial-upsampler-path models/ltx-2.3/ltx-2.3-spatial-upscaler-x2-1.1.safetensors \
  --image assets/key_000.png 0 1.0 \
  --image assets/key_120.png 120 1.0 \
  --prompt "A smooth transition between the two key poses." \
  --num-frames 121 --output-path outputs/interp.mp4
```

### Audio-to-video

```bash
python -m ltx_pipelines.a2vid_two_stage \
  --transformer-path models/ltx-2.5/diffusion_models/ltx-2.5-22b-dev-transformer-bf16.safetensors \
  --text-encoder-path models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
  --video-vae-path models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
  --audio-vae-path models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
  --spatial-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
  --distilled-lora models/ltx-2.5/loras/ltx-2.5-22b-distilled-lora-450-bf16.safetensors 0.8 \
  --audio-path assets/input.wav --audio-start-time 0 --audio-max-duration 5 \
  --prompt "A performer moves in sync with the audio." \
  --num-frames 121 --output-path outputs/a2v.mp4
```

### HDR retake segment from EXR frames

Retake from an EXR folder requires `--hdr` and `--frame-rate`; retake from a video file must not set `--frame-rate`.

```bash
python -m ltx_pipelines.retake \
  --transformer-path models/ltx-2.5/diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors \
  --text-encoder-path models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
  --video-vae-path models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
  --audio-vae-path models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
  --video-path assets/source_exr_frames/ --frame-rate 24 \
  --start-time 1.0 --end-time 3.5 \
  --prompt "Replace only this time window with a brighter performance." \
  --hdr SRGB_LINEAR --seed 7 \
  --output-path outputs/retake_hdr.mp4
```

### Dub-It

```bash
python -m ltx_pipelines.dubit \
  --distilled-checkpoint-path models/ltx-2.3/ltx-2.3-22b-distilled-1.1.safetensors \
  --gemma-root models/gemma-3-12b-it-qat-q4_0-unquantized \
  --spatial-upsampler-path models/ltx-2.3/ltx-2.3-spatial-upscaler-x2-1.1.safetensors \
  --lora models/ltx-2.3/ltx-2.3-22b-ic-lora-dubit-0.9.safetensors 1.0 \
  --reference-video assets/speaker_reference.mp4 \
  --prompt "The speaker says the new line naturally." \
  --output-path outputs/dubit.mp4
```

### Text-to-audio

```bash
python -m ltx_pipelines.t2a_one_stage \
  --transformer-path models/ltx-2.5/diffusion_models/ltx-2.5-22b-dev-transformer-bf16.safetensors \
  --text-encoder-path models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
  --audio-vae-path models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
  --prompt "A calm narrator says hello in a studio." \
  --num-frames 121 --frame-rate 24 \
  --output-path outputs/speech.wav
```

### DFR with optional temporal refine

```bash
python -m ltx_pipelines.dfr_pipeline \
  --transformer-path models/ltx-2.5/diffusion_models/ltx-2.5-22b-dev-transformer-bf16.safetensors \
  --text-encoder-path models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors \
  --video-vae-path models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors \
  --audio-vae-path models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors \
  --spatial-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors \
  --distilled-lora models/ltx-2.5/loras/ltx-2.5-22b-distilled-lora-450-bf16.safetensors 0.8 \
  --detailing-lora models/detailing/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors 1.0 \
  --temporal-upsampler-path models/ltx-2.5/latent_upscale_models/ltx-2.5-latent-temporal-upscaler-x2-bf16-1.0.safetensors \
  --temporal-upsample-rounds 1 \
  --prompt "A high-detail cinematic shot." \
  --num-frames 121 --output-path outputs/dfr.mp4
```
