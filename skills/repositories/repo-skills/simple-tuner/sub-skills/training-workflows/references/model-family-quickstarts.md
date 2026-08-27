# Model family quickstarts

Use this reference to choose a SimpleTuner model family, flavour, and starting config. Keep it at decision level. Dataloader schemas, adapter target details, adapter extraction/conversion, and distillation internals belong to other sub-skills.

## Selection workflow

1. Identify the output modality and base checkpoint: image, video, audio, image-editing, image-to-video, audio-video, or staged model.
2. Pick `model_family` and, when needed, `model_flavour` from the installed registry metadata. The source snapshot includes 41 registry entries and packaged examples for most families.
3. Start from a packaged example when possible, then copy it into a writable config environment before editing. The example configs are runnable starting points but may download models, small datasets, or validation assets.
4. Check platform and memory guidance before selecting precision, attention backend, DeepSpeed, FSDP2, context parallelism, or offload.
5. If the task is primarily about PEFT/LyCORIS targets, `lora_format`, adapter export to ComfyUI/Diffusers, checkpoint merge, extraction scripts, ControlNet adapter mechanics, CaptionFlow, Prompt2Effect, or distillation methods, route to `sub-skills/model-and-adapter-tooling/`.

## High-value starting points

| Request shape | Prefer | Starting evidence and caveats |
| --- | --- | --- |
| Flux.1 LoRA, Krea/dev/schnell, or Kontext image editing | `model_family=flux`; set `model_flavour` to `krea`, `dev`, `schnell`, or `kontext` | Examples include `flux.peft-lora`, `flux.peft-lora+TREAD`, `flux.peft-controlnet-lora`, and `kontext.peft-lora`. Flux is memory-heavy and documented as not currently working for Apple training. Schnell quickstart defaults handle the fast schedule. Kontext/reference data details route to `sub-skills/data-and-config/`. |
| Flux.2 LoRA | `model_family=flux2`; default smaller Klein variants unless user explicitly needs `dev` | `klein-4b`/`klein-9b` are more accessible; `dev` combines a large transformer and a 24B text encoder and usually requires multi-GPU FSDP2 or DeepSpeed. Examples include `flux2.peft-lora`, `flux2.peft-lora+TREAD`, and `flux2-klein-9b-i2i.lycoris-lokr`. |
| SDXL/SD3/PixArt/Sana/Auraflow-style image tuning | `sdxl`, `sd3`, `pixart`/`pixart_sigma`, `sana`, `auraflow`, `lumina2`, `chroma`, `qwen_image`, `z_image`, or related family | Use the quickstart matching the architecture. Some families prefer LyCORIS or have ControlNet support differences; consult model/adapters when adapter format or target modules matter. |
| Video LoRA on Wan or LTX Video | `model_family=wan`, `wan_s2v`, `ltxvideo`, or `ltxvideo2` | Video runs are usually memory-bound. Wan examples split 1.3B/14B, T2V/I2V/stage presets, and 8xH100 context-parallel FlashAttention profiles. LTX Video 2 is a 19B-class family; single-GPU configs usually need group offload, while multi-GPU jobs may need FSDP2 or context parallelism. |
| Hunyuan/Cosmos/LongCat/Kandinsky video or image-to-video | `hunyuanvideo`, `cosmos3`, `longcat_video`, `longcat_image`, `kandinsky5_video`, `kandinsky5_image` | Expect model-flavour and conditioning details. Keep training launch planning here; route paired conditioning/data schemas to data-and-config. |
| MiniMax H3 video/audio | `model_family=minimaxh3`, usually `model_flavour=convrot-int8` for examples | 33B flow-matching video/audio family. Start from the VRAM-matched H3 example and run a short smoke test. H3 sparse attention is experimental, CUDA/FlexAttention-dependent, and has context-parallel restrictions. H3 drift distillation details route to model/adapters. |
| Audio/music generation | `ace_step`, `heartmula`, or `minimaxmusic` | Examples distinguish ACE-Step generations and MiniMax Music VRAM presets. Audio data and lyrics schemas route to data-and-config. |
| Legacy or smaller image baselines | `sd1x`, `deepfloyd`, `kolors`, `stable_cascade`, `omnigen`, `boogu_image`, `ernie`, `ideogram`, `krea2`, `mageflow`, `zlab_i1` | Use model-specific quickstart/examples when present. Confirm license/access and adapter support before launching. |

## Quickstart/config handoff pattern

When a user names a model family and asks for a run command:

1. Choose the closest packaged example by model family, model flavour, modality, adapter type, VRAM tier, and distributed profile.
2. Instruct the user to copy the example into a config environment before editing; do not edit package examples in place.
3. Keep topology stable when resuming: do not change model family/flavour/type, distributed backend, world size, batch sizing, gradient accumulation, dataset repeats, or dataloader semantics without starting a new run or explicitly accepting resume risk.
4. Build the command with `simpletuner train --env <env>` for copied environments, or with `CONFIG_BACKEND=json CONFIG_PATH=<path> simpletuner-train` when a specific JSON config path is already selected.
5. Mark actual model downloads, dataset downloads, and training as manual/expensive.

Example command patterns:

```bash
simpletuner train --env flux-lora max_train_steps=100 report_to=none
simpletuner train example=kontext.peft-lora
CONFIG_BACKEND=json CONFIG_PATH=config/ltxvideo2-cp/config.json simpletuner-train --resume_from_checkpoint=latest
```

## Model-family caveats to surface early

- **Flux.1**: needs high system RAM during quantization; Apple training is documented as not currently working; `gradient_checkpointing` is effectively mandatory for low VRAM.
- **Flux.2-dev**: multi-GPU FSDP2 or DeepSpeed is usually required. Klein variants are recommended for most users.
- **Wan 14B and LTX Video 2**: start with single-GPU offload examples or 8xH100 context-parallel examples; validate frame counts, resolution, and attention backend before long runs.
- **MiniMax H3**: keep distilled validation settings and H3 drift defaults unless the task is explicitly a distillation/ablation task; experimental sparse attention requires CUDA FlexAttention and careful context-parallel planning.
- **SLA attention**: a model fine-tuned with SLA should keep SLA enabled for validation/resume/inference and must retain `sla_attention.pt` with checkpoints.
- **Validation adapters**: `validation_adapter_path` and `validation_adapter_config` are decision-level training options here; complex adapter stack design routes to model/adapters.
