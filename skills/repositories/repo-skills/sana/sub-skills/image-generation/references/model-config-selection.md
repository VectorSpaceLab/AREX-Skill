# Model and Config Selection for Sana Image Generation

Use this reference to choose model IDs, native `.pth` checkpoint names, config
families, precision, resolution, and workflow surface before generating images.

## Selection Rules

- Use **Diffusers** model IDs ending in `_diffusers` with Diffusers pipelines.
- Use **native `.pth`** checkpoint URIs with native config YAMLs and native app
  pipeline classes or batch inference scripts.
- Do not mix a Diffusers model ID with a native YAML+`.pth` workflow, and do not
  pass a native `hf://.../checkpoints/*.pth` URI into Diffusers
  `from_pretrained`.
- Match the native config's model family, resolution, precision, scheduler, and
  ControlNet/Sprint architecture to the checkpoint.
- For `fp16` Diffusers models, set `variant="fp16"` and `torch_dtype=torch.float16`.
  For `bf16` Diffusers models, set `variant="bf16"` and
  `torch_dtype=torch.bfloat16` when a variant exists.
- The Diffusers transformer dtype is not enough: keep the Sana VAE and text
  encoder in `torch.bfloat16` or `torch.float32` unless using a documented
  quantized component path. Plain `torch.float16` text encoder/VAE loading is a
  common source of bad outputs or runtime errors.

## Common Diffusers Image Models

| Need | Diffusers model id | Pipeline | Recommended dtype | Notes |
| --- | --- | --- | --- | --- |
| Sana-1.5 1.6B at 1024px | `Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers` | `SanaPipeline` or `SanaPAGPipeline` | `torch.bfloat16` | Best default for Sana-1.5 image generation. |
| Sana-1.5 4.8B at 1024px | `Efficient-Large-Model/SANA1.5_4.8B_1024px_diffusers` | `SanaPipeline` or `SanaPAGPipeline` | `torch.bfloat16` | Larger model; plan more VRAM. |
| Sana 1.6B bf16 at 1024px | `Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers` | `SanaPipeline` or `SanaPAGPipeline` | `torch.bfloat16`, `variant="bf16"` | Good multilingual 1K bf16 baseline. |
| Sana 1.6B fp16 at 1024px | `Efficient-Large-Model/Sana_1600M_1024px_diffusers` | `SanaPipeline` | `torch.float16`, `variant="fp16"` | Keep VAE/text encoder bf16 or fp32. |
| Sana 1.6B multilingual 1024px | `Efficient-Large-Model/Sana_1600M_1024px_MultiLing_diffusers` | `SanaPipeline` | `torch.float16`, `variant="fp16"` | Multilingual prompt support. |
| Sana 0.6B at 1024px | `Efficient-Large-Model/Sana_600M_1024px_diffusers` | `SanaPipeline` | `torch.float16`, `variant="fp16"` | Lower VRAM; text rendering can be weaker. |
| Sana 1.6B at 512px | `Efficient-Large-Model/Sana_1600M_512px_diffusers` | `SanaPipeline` | `torch.float16`, `variant="fp16"` | Use 512 height/width. |
| Sana 0.6B at 512px | `Efficient-Large-Model/Sana_600M_512px_diffusers` | `SanaPipeline` | `torch.float16`, `variant="fp16"` | Lowest native model size. |
| Sana 1.6B 2K | `Efficient-Large-Model/Sana_1600M_2Kpx_BF16_diffusers` | `SanaPipeline` | `torch.bfloat16`, `variant="bf16"` | Plan high VRAM; use 2048 height/width. |
| Sana 1.6B 4K | `Efficient-Large-Model/Sana_1600M_4Kpx_BF16_diffusers` | `SanaPipeline` | `torch.bfloat16`, `variant="bf16"` | Enable VAE tiling; 16 GPUs are recommended in source guidance. |
| SANA-Sprint 1.6B | `Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers` | `SanaSprintPipeline` | `torch.bfloat16` | Usually two inference steps. |
| SANA-Sprint 0.6B | `Efficient-Large-Model/Sana_Sprint_0.6B_1024px_diffusers` | `SanaSprintPipeline` | `torch.bfloat16` | Lower model size; same Sprint scheduler family. |
| 4-bit SVDQuant Sana | transformer `mit-han-lab/svdq-int4-sana-1600m` plus base `Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers` | `SanaPipeline` | base bf16, int4 transformer | Requires Nunchaku/SVDQuant engine and CUDA. |

## Common Native `.pth` Pairings

| Need | Native config label | Native model checkpoint label | Native entry label | Notes |
| --- | --- | --- | --- | --- |
| Sana 1.6B 1024px bf16 | `configs/sana_config/1024ms/Sana_1600M_img1024.yaml` | `hf://Efficient-Large-Model/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth` or bf16 checkpoint label | `scripts/inference.py`, `app.sana_pipeline.SanaPipeline` | Flow-DPM-Solver, PAG capable with linear attention. |
| Sana 0.6B 1024px | `configs/sana_config/1024ms/Sana_600M_img1024.yaml` | `hf://Efficient-Large-Model/Sana_600M_1024px/checkpoints/Sana_600M_1024px.pth` | `scripts/inference.py` | Lower VRAM, fp16 config family. |
| Sana 1.6B 512px | `configs/sana_config/512ms/Sana_1600M_img512.yaml` | `hf://Efficient-Large-Model/Sana_1600M_512px/checkpoints/Sana_1600M_512px.pth` | `scripts/inference.py` | Use 512 prompt aspect-ratio bin. |
| Sana 0.6B 512px | `configs/sana_config/512ms/Sana_600M_img512.yaml` | `hf://Efficient-Large-Model/Sana_600M_512px/checkpoints/Sana_600M_512px.pth` | `scripts/inference.py` | Smallest ordinary native image config. |
| Sana-1.5 1.6B 1024px | `configs/sana1-5_config/1024ms/Sana_1600M_1024px_allqknorm_bf16_lr2e5.yaml` | `hf://Efficient-Large-Model/SANA1.5_1.6B_1024px/checkpoints/SANA1.5_1.6B_1024px.pth` | `app.sana_pipeline.SanaPipeline` or adapted native batch command | Sana-1.5 config uses all-QK-norm bf16. |
| Sana-1.5 4.8B 1024px | `configs/sana1-5_config/1024ms/Sana_4800M_1024px_came8bit_grow_constant_allqknorm_bf16_lr2e5.yaml` | `hf://Efficient-Large-Model/Sana1-5_4800M_1024px/checkpoints/Sana1-5_4800M_1024px.pth` from the config, while the public model-zoo label is `SANA1.5_4.8B_1024px` | native pipeline or custom batch run | Larger bf16 config; verify checkpoint naming, availability, and VRAM first. |
| Sana 1.6B 2K | `configs/sana_config/2048ms/Sana_1600M_img2048_bf16.yaml` | `hf://Efficient-Large-Model/Sana_1600M_2Kpx_BF16/checkpoints/Sana_1600M_2Kpx_BF16.pth` | native pipeline or batch script shape | High VRAM; aspect-ratio tables include 2048. |
| Sana 1.6B 4K | `configs/sana_config/4096ms/Sana_1600M_img4096_bf16.yaml` | `hf://Efficient-Large-Model/Sana_1600M_4Kpx_BF16/checkpoints/Sana_1600M_4Kpx_BF16.pth` | native pipeline or batch script shape | High VRAM; Diffusers VAE tiling is the clearer 4K path. |
| SANA-Sprint 1.6B | `configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml` | `hf://Efficient-Large-Model/Sana_Sprint_1.6B_1024px/checkpoints/Sana_Sprint_1.6B_1024px.pth` | `scripts/inference_sana_sprint.py`, `app.sana_sprint_pipeline.SanaSprintPipeline` | SCM scheduler, usually two steps. |
| SANA-Sprint 0.6B | `configs/sana_sprint_config/1024ms/SanaSprint_600M_1024px_allqknorm_bf16_scm_ladd.yaml` | `hf://Efficient-Large-Model/Sana_Sprint_0.6B_1024px/checkpoints/Sana_Sprint_0.6B_1024px.pth` | Sprint native entry | Lower model size. |
| ControlNet HED 1.6B | `configs/sana_controlnet_config/Sana_1600M_1024px_controlnet_bf16.yaml` | `hf://Efficient-Large-Model/Sana_1600M_1024px_BF16_ControlNet_HED/checkpoints/Sana_1600M_1024px_BF16_ControlNet_HED.pth` | `tools/controlnet/inference_controlnet.py`, `app.sana_controlnet_pipeline.SanaControlNetPipeline` | Requires HED annotator checkpoint when deriving control maps from ref images. |
| ControlNet HED 0.6B | `configs/sana_controlnet_config/Sana_600M_img1024_controlnet.yaml` | `hf://Efficient-Large-Model/Sana_600M_1024px_ControlNet_HED/checkpoints/Sana_600M_1024px_ControlNet_HED.pth` | ControlNet native entry | Check model availability before committing to the run. |
| Gradio default 1.6B | `configs/sana_app_config/Sana_1600M_app.yaml` or image config | Sana 1.6B checkpoint label | `app/app_sana.py` | Interactive server, `DEMO_PORT` controls the port. |
| Gradio default 0.6B | `configs/sana_app_config/Sana_600M_app.yaml` | Sana 0.6B checkpoint label | `app/app_sana.py` | Smaller demo model. |

## Config Facts That Affect Generation

- Standard image configs use `AutoencoderDC` with downsample rate 32, Gemma
  `gemma-2-2b-it` text encoder, model max length 300, and Flow-DPM-Solver.
- Sana 1.6B 1024 bf16 and Sana-1.5 1024 bf16 configs use
  `SanaMS_1600M_P1_D20`, `mixed_precision=bf16`, `flow_shift=3.0`, and linear
  attention.
- Sana 0.6B 1024 configs use `SanaMS_600M_P1_D28`, typically fp16, and
  `flow_shift=4.0`.
- 4K native config uses image size 4096 and `flow_shift=6.0`.
- Sprint configs use `SanaMSCM_*`, `vis_sampler=scm`, `sigma_data=0.5`,
  `cfg_embed=True`, and usually two steps.
- ControlNet configs use `SanaMSControlNet_*` and add a `controlnet` section;
  do not substitute a plain image config.

## Hardware and Precision Planning

| Plan | Minimum expectation from source guidance | Practical notes |
| --- | --- | --- |
| Sana 0.6B image inference | around 9 GB VRAM | CUDA is still required for native and recommended for Diffusers. |
| Sana 1.6B image inference | around 12 GB VRAM | bf16 requires GPU support; otherwise choose fp16 model or smaller resolution. |
| 4-bit image inference | less than 8 GB VRAM in source guidance | Requires Nunchaku/SVDQuant engine; not a generic PyTorch quantization flag. |
| ControlNet HED | similar to 1K image inference plus HED preprocessing | HED detector creates CUDA modules and may download `ControlNetHED.pth`. |
| 2K/4K bf16 | substantially more than 1K; 4K source guidance recommends many GPUs | Enable VAE tiling for 4K and reduce batch/images/steps before changing models. |

## Pre-run Sanity Checks

- Confirm CUDA availability before native generation; CPU is not a credible
  substitute for end-to-end Sana image generation.
- Confirm model/cache/Hugging Face access for base model, Gemma text encoder,
  DC-AE VAE, optional ShieldGemma safety checker, Sprint weights, ControlNet
  weights, and optional HED checkpoint.
- Confirm the command uses either `--txt_file` or `--json_file` for batch image
  scripts. A direct prompt string is not a native batch-script input unless you
  first write it to a prompt file.
- Confirm `height` and `width` are multiples of 32 for Diffusers requests; the
  native pipeline bins to supported aspect-ratio tables when resolution binning
  is enabled.
- For 2K/4K, estimate output storage and decide the output directory before the
  run.
