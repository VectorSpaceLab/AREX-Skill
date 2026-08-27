# Inference troubleshooting

Start with the error message and the pipeline selected in `pipeline-selection.md`. Most recoveries are flag/path fixes and do not require reading source code.

## Symptoms, causes, recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Path not found` while parsing CLI | A model/media/LoRA path does not exist; the parser resolves many paths before running. | Check every path. Use absolute or current-directory-relative local paths. The bundled command builder can validate split distilled assets without running generation. |
| 401/403 or gated-model access during asset acquisition | Model terms not accepted or HF token lacks read/gated scope. | Accept model terms on the provider site and use a read token with gated-repo permission. Do not let runtime commands implicitly download models; prepare local assets first. |
| Parser says split flags cannot combine with checkpoint/gemma flags | Mixed LTX-2.5 split layout with monolith layout. | Use either split (`--transformer-path`, `--text-encoder-path`, `--video-vae-path`, `--audio-vae-path`) or monolith (`--checkpoint-path`/`--distilled-checkpoint-path` plus `--gemma-root`). Remove `--gemma-root` in split mode. |
| Missing `ModelPaths.* is required but missing` in Python | `ModelPaths.from_split` omitted a component the chosen pipeline loads. | Add the needed component path: usually text encoder, video VAE, audio VAE, transformer, and for auto-duration the duration head. |
| Text encoder version mismatch / bad Gemma generation | Used stock Gemma or a prompt-enhancer root instead of the LTX text encoder, or omitted prompt enhancer root when needed. | For LTX-2.5 split, use the single-file `gemma4-12b-with-proj-ltx-2.5-...safetensors` via `--text-encoder-path`; do not use `--gemma-root`. Only add `--prompt-enhancer-gemma-root` for prompt enhancement. |
| Video/audio VAE path missing in split layout | Split command included transformer/text encoder but forgot VAE paths. | Add `--video-vae-path` for video encode/decode and `--audio-vae-path` for normal audio-video output. Retake and A2V need both. T2A needs audio VAE. |
| LoRA appears ignored or fails to load | Wrong model family, wrong LoRA type, conflicting IC-LoRA metadata, or omitted required distilled LoRA. | Match LoRA to LTX-2.5 vs LTX-2.3 assets. Use `--distilled-lora` for guided two-stage/keyframe/A2V/DFR refinement. Use task-specific `--lora` for IC-LoRA/Dub-It. Do not combine IC-LoRAs with conflicting reference scale metadata. |
| `num_frames` invalid or source frame count invalid | Frame count not on `8k+1` grid. | Choose `num_frames = 8*k + 1` such as 97, 121, 161, or trim/source-convert retake videos to that frame count. Dub-It snaps reference frames internally; retake rejects invalid source counts. |
| Resolution divisibility error | Dimensions not multiples of required divisor. | Use multiples of 64 for two-stage/upscaling pipelines; multiples of 32 for one-stage and retake source media. HDRICLora input dimensions must also be divisible by 32. |
| CUDA out of memory during model load or denoise | 22B model, high resolution/frame count, HDR float decode, generated keyframes, DFR temporal rounds, or no memory-saving flags. | Lower `--height`, `--width`, or `--num-frames`; remove generated keyframes/DFR temporal rounds; try `--quantization fp8-cast`; try `--offload cpu` then `disk`; reduce HDRICLora `--spatial-tile`; route backend-specific tuning to `performance-backends`. |
| OOM or long stall during VAE decode | Diffusion VAE decode is heavy; HDR uses float32; tile size too large. | Use conv VAE if acceptable, lower resolution/frame count, lower HDRICLora `--spatial-tile`, or tune `--diffvae-optimization`. Optional NATTEN/DiffVAE backend setup routes to `performance-backends`. |
| NATTEN/FlashAttention/DiffVAE optional backend import/build fails | Optional accelerator package missing or incompatible hardware/toolkit. | Do not treat as a CLI selection failure unless the user required that backend. Use fallback modes or route install/build diagnosis to `performance-backends`. |
| `--quantization ... requires --checkpoint-path ... or --transformer-path` | Quantization policy needs a transformer/checkpoint path to inspect. | Ensure the command includes monolith checkpoint or split `--transformer-path` before/with quantization. |
| NVFP4 quantization fails | NVFP4 requires Blackwell-specific kernels/checkpoints. | Use `fp8-cast` for general bf16 checkpoints, or route NVFP4 setup to `performance-backends`. |
| `--compile` errors on KEY=VALUE | Invalid `CompilationConfig` key or malformed JSON. | Use only documented keys: `mode`, `backend`, `fullgraph`, `dynamic`, `inductor_config`, `dynamo_config`, `seq_dim_dynamic`, `recompile_perturbed_block`, `capture`. For JSON config, pass a JSON object or path. |
| EXR input rejected because `--hdr` missing | Any EXR still/folder requires explicit color-space declaration. | Add `--hdr SRGB_LINEAR`, `ACESCG`, or `ACESCCT` matching the source. |
| EXR/SDR mix rejected | The parser forbids mixing EXR and non-EXR conditioning media in one run. | Convert all conditioning media to the same domain or run separate passes. `--conditioning-attention-mask` is SDR and not part of the EXR/SDR check. |
| Single `.exr` passed to video-conditioning or retake video path | Sequence/video flags require a video file or a directory of `*.exr` frames. | Use `.exr` stills only with `--image`; for video-conditioning/retake, provide an EXR folder. |
| Retake EXR folder complains about frame rate | EXR folders have no container fps. | Add `--frame-rate FPS`. For normal video files, remove `--frame-rate`. |
| Retake segment does not align or changes too much | Window boundaries do not match intended frames; prompt describes whole video; invalid source grid. | Verify source fps and `8k+1` frame count, compute start/end on frame boundaries where possible, and write the prompt for only the replacement interval while preserving context. |
| Retake `start_time must be less than end_time` | Reversed or zero-length time window. | Set a positive interval in seconds. |
| HDR output lacks EXR folder | `--hdr` was omitted or dedicated HDR IC-LoRA path used differently. | For standard pipelines, add `--hdr` to write EXR frames plus HLG master. For HDRICLora CLI, check `--output-dir` and `--skip-mp4`; Python returns tensor unless you save it. |
| OpenImageIO/OpenEXR import or encode error | EXR/HDR dependency missing or incompatible. | Install/repair HDR I/O dependencies in the environment; route package/backend setup to `performance-backends`. |
| HDRICLora output OOMs at 4K | Tile size/frame count too high for available VRAM. | Reduce `--num-frames`, lower `--spatial-tile` (for example 768), avoid `--high-quality`, or use larger GPU/offload. |
| Dub-It rejects reference video | Reference is EXR, a directory, lacks audio, or wrong media type. | Provide an SDR video container with an audio stream. Do not use `--hdr`, `--num-frames`, or `--frame-rate` with Dub-It. |
| Dub-It LoRA error | Missing or multiple/incorrect LoRA. | Pass exactly one Dub-It IC-LoRA with `--lora PATH [STRENGTH]`, matched to the checkpoint family. |
| A2V audio decode fails | Bad path, unsupported audio, or requested start/max duration outside file. | Verify local audio file, shorten/adjust `--audio-start-time` and `--audio-max-duration`, and match video duration (`num_frames / frame_rate`). |
| T2A unexpectedly asks for video VAE or image flags | Wrong module selected. | Use `ltx_pipelines.t2a_one_stage`; do not pass video dimensions/image flags. Provide audio VAE in split mode. |
| Generated keyframes fail | Checkpoint does not support keyframe absolute position embeddings or too many keyframes caused OOM. | Use LTX-2.5 or another generated-keyframe-capable transformer; lower `--num-generated-keyframes` or switch to DFR if detail-fidelity is the goal. |
| DFR rejects temporal rounds or fails later | `--temporal-upsample-rounds > 0` without temporal upsampler path; checkpoint lacks generated-keyframe slots; token/VRAM budget too high. | Add `--temporal-upsampler-path`, use LTX-2.5+ keyframe-capable full/dev transformer, reduce rounds/resolution/frames, or run DFR with `--temporal-upsample-rounds 0`. |
| DFR user asks for `--num-generated-keyframes` | DFR does not expose this flag. | Remove it. DFR derives generated keyframe slot positions internally from its segment grid. |

## Preflight checklist

Before running generation:

1. Pipeline matches the user's source and target: retake segment, whole video conditioning, audio-to-video, audio-only, HDR, Dub-It, or DFR.
2. Exactly one checkpoint layout is used.
3. Every local model/media/LoRA path exists.
4. Frame count is `8k+1`; dimensions satisfy required multiples.
5. HDR/EXR inputs are all EXR and include `--hdr`; SDR inputs omit it.
6. Required task assets are present: spatial upsampler for two-stage, distilled LoRA for guided refinement/DFR/A2V/keyframe, temporal upsampler for DFR temporal rounds, Dub-It LoRA/reference video, HDR embeddings/HDR LoRA.
7. Memory plan is realistic. Add `--quantization fp8-cast` or `--offload cpu` when needed, but route backend installation/tuning to `performance-backends`.
