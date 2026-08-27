# Pipeline selection

This guide chooses among the public `ltx_pipelines` inference entry points. Prefer the smallest pipeline that matches the conditioning source and output contract; do not pick a training or low-level core workflow for ordinary generation.

## Decision tree

```text
Is the output audio-only from a text prompt?
├─ YES → T2AOneStagePipeline / ltx_pipelines.t2a_one_stage
└─ NO

Do you need to regenerate only a segment of an existing video/EXR sequence?
├─ YES → RetakePipeline / ltx_pipelines.retake
│        Add --hdr for EXR folders; provide --start-time and --end-time.
└─ NO

Is Dub-It requested: rephrase/dub while preserving speaker identity and lip motion?
├─ YES → DubItPipeline / ltx_pipelines.dubit
│        Requires one Dub-It IC-LoRA and an SDR reference video with audio.
└─ NO

Do you need video-to-video or reference-video control through an IC-LoRA?
├─ YES → ICLoraPipeline / ltx_pipelines.ic_lora
│        Use a distilled transformer and at least one IC-LoRA.
└─ NO

Do you need dedicated HDR IC-LoRA linear float output for external tonemapping?
├─ YES → HDRICLoraPipeline / ltx_pipelines.hdr_ic_lora
│        Uses precomputed text embeddings and returns/exports linear HDR float/EXR material.
└─ NO

Do you have EXR stills or EXR-frame folders for a standard pipeline?
├─ YES → Use Distilled, TI2V, IC-LoRA, or Retake with --hdr {SRGB_LINEAR,ACESCG,ACESCCT}
│        This writes half EXR frames plus a BT.2020/HLG master.
└─ NO

Do you have an input audio file that should drive video?
├─ YES → A2VidPipelineTwoStage / ltx_pipelines.a2vid_two_stage
└─ NO

Do you have multiple keyframe still images that should be interpolated?
├─ YES → KeyframeInterpolationPipeline / ltx_pipelines.keyframe_interpolation
└─ NO

Do you need maximum detail fidelity or higher effective frame rate?
├─ YES → DFRPipeline / ltx_pipelines.dfr_pipeline
│        Requires generated-keyframe-capable model; optional temporal upsampler for 2x/4x fps.
└─ NO

Need fastest default text/image-to-video?
├─ YES → DistilledPipeline / ltx_pipelines.distilled
└─ Need guided/high-quality two-stage → TI2VidTwoStagesPipeline or TI2VidTwoStagesHQPipeline
```

## Feature matrix

| Pipeline class | CLI module | Primary use | Stages | Conditioning | Key assets beyond base model | Output contract | Notes |
|---|---|---:|---:|---|---|---|---|
| `DistilledPipeline` | `ltx_pipelines.distilled` | Fast default T2V/I2V | 2 | Prompt, optional images, optional generated keyframe slots | Distilled transformer, video VAE, audio VAE, text encoder, spatial upsampler | MP4; with `--hdr`, HLG MP4 plus EXR folder | Recommended fastest path; fixed distilled sigmas; no CFG flags. |
| `TI2VidTwoStagesPipeline` | `ltx_pipelines.ti2vid_two_stages` | Production guided T2V/I2V | 2 | Prompt, negative prompt, image conditioning, multimodal guidance, generated keyframes | Full/dev transformer, text encoder, video/audio VAE, spatial upsampler, distilled LoRA | MP4; HDR/EXR with `--hdr` | Highest quality default; slower than distilled. |
| `TI2VidTwoStagesHQPipeline` | `ltx_pipelines.ti2vid_two_stages_hq` | Production T2V/I2V with res_2s sampler | 2 | Same as two-stage TI2V | Same as two-stage TI2V; stage-specific distilled LoRA strengths | MP4; HDR/EXR with `--hdr` | Uses res_2s sampler; default step count is lower than standard TI2V. |
| `TI2VidOneStagePipeline` | `ltx_pipelines.ti2vid_one_stage` | Educational/prototype T2V/I2V | 1 | Prompt, negative prompt, image conditioning, guidance, generated keyframes | Full/dev transformer, text encoder, video/audio VAE | MP4; HDR/EXR with `--hdr` | Lower resolution/quality; useful for understanding or quick parser-level prototypes. |
| `ICLoraPipeline` | `ltx_pipelines.ic_lora` | Video-to-video or image/video controlled transforms | 2 | Prompt, images, `--video-conditioning`, optional attention mask | Distilled transformer, text encoder, video/audio VAE, spatial upsampler, IC-LoRA(s) | MP4; HDR/EXR with `--hdr` for EXR conditioning | IC-LoRA path expects distilled model. Stage 2 can be skipped for half-res output. |
| `KeyframeInterpolationPipeline` | `ltx_pipelines.keyframe_interpolation` | Smooth interpolation between keyframe images | 2 | Multiple image keyframes, prompt, guidance | Full/dev transformer, text encoder, video/audio VAE, spatial upsampler, distilled LoRA | MP4; HDR/EXR with `--hdr` | Uses guiding-latent conditioning, not replacement, for smoother transitions. |
| `A2VidPipelineTwoStage` | `ltx_pipelines.a2vid_two_stage` | Audio-driven video | 2 | Input audio, prompt, optional images, video guidance | Full/dev transformer, text encoder, video/audio VAE, spatial upsampler, distilled LoRA | MP4 with original/conditioned audio | Input audio latent drives generation; audio waveform is preserved/passed through. |
| `RetakePipeline` | `ltx_pipelines.retake` | Regenerate a time window of a source video | 1 | Source video or EXR folder, prompt, start/end window | Distilled transformer or monolith, text encoder, video/audio VAE | MP4; HDR/EXR with `--hdr` | Source frames must be `8k+1`; dimensions multiples of 32. |
| `HDRICLoraPipeline` | `ltx_pipelines.hdr_ic_lora` | Dedicated HDR IC-LoRA video-to-video | 2 | SDR video input(s), HDR IC-LoRA, precomputed text embeddings | Distilled monolith or compatible paths, video VAE, spatial upsampler, HDR LoRA, embeddings | Linear HDR float tensor; CLI writes EXR frames and optional video preview | Separate from standard `--hdr`; no audio generation. |
| `DubItPipeline` | `ltx_pipelines.dubit` | Dubbing/rephrasing with lip/speaker reference | 2 | Reference video with audio, prompt, optional images | Distilled transformer, text encoder, video/audio VAE, spatial upsampler, exactly one Dub-It IC-LoRA | MP4 with dubbed audio/video | Frame count/fps come from reference video and are snapped to `8k+1`; no `--num-frames` or `--frame-rate`. |
| `T2AOneStagePipeline` | `ltx_pipelines.t2a_one_stage` | Text-to-audio | 1 | Prompt, negative prompt, audio guidance | Full/dev transformer with audio-only loading, text encoder, audio VAE | Audio file from `--output-path` | No video dimensions or image flags. |
| `DFRPipeline` | `ltx_pipelines.dfr_pipeline` | Detail-fidelity rendering and optional 2x/4x temporal refine | 2 plus optional temporal rounds | Prompt, images, generated keyframe slots internally | Full/dev transformer supporting keyframe slots, text encoder, video/audio VAE, spatial upsampler, distilled LoRA; optional detailing LoRA and temporal upsampler | MP4; audio from stage 1; fps multiplied by temporal rounds | Does not accept `--num-generated-keyframes`; derives its own slot positions. |

## Model family compatibility

- **LTX-2.5 split layout** is the recommended current layout. It uses separate component files: transformer, single-file Gemma/text-projection encoder, video VAE, audio VAE, optional duration head, spatial upsampler, temporal upsampler, and LoRAs.
- **LTX-2.3/legacy monolith layout** uses a fat checkpoint plus a Hugging Face Gemma directory. The monolith bundles transformer, VAEs, and text projection; Gemma text encoder files are separate. LTX-2.3 LoRAs must stay with LTX-2.3 checkpoints.
- Do not mix model families or component layouts in one run. A stock Gemma release is not a substitute for the LTX-2.5 single-file text encoder.
- Pipelines that run distilled models (`DistilledPipeline`, `ICLoraPipeline`, `DubItPipeline`, and distilled retake) require a distilled transformer/monolith. Guided two-stage, keyframe interpolation, A2V, DFR, T2A generally use the full/dev transformer plus a distilled LoRA where stage-2 refinement is present.

## Selection heuristics

- If the user asks for "fastest", "default", "quick start", or "I2V with one image", choose `DistilledPipeline` unless they explicitly need guidance, reference video control, retake, or DFR.
- If they ask for "HQ", "best quality", "CFG/STG", or detailed prompt adherence, choose `TI2VidTwoStagesPipeline` or `TI2VidTwoStagesHQPipeline`.
- If they ask for "change this clip", "use this pose/depth/control video", or "video-to-video", choose `ICLoraPipeline` when the whole clip is conditioned and `RetakePipeline` when only a time segment changes.
- If they ask for "HDR plates", "EXR input", or "HLG master", stay on the standard chosen pipeline and add `--hdr`. Use `HDRICLoraPipeline` only for the dedicated HDR IC-LoRA / LogC3 inverse-decode workflow.
- If they ask for "higher fps", "more detail", or "generated keyframes", prefer `DFRPipeline` for finished detail-fidelity output, or `--num-generated-keyframes` on Distilled/TI2V only when they want extra interior keyframe slots without DFR.
