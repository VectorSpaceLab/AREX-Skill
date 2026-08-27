# SANA-Video, LTX-2 Refiner, and LongSANA

This reference distills the video-generation evidence into self-contained command-planning guidance. Use it for text-to-video (T2V), image-to-video (I2V), high-resolution LTX-2 refinement, and LongSANA long-context generation.

## Workflow selection

| User intent | Use | Main inputs | Typical output | Notes |
| --- | --- | --- | --- | --- |
| 5 second prompt-only clip | SANA-Video T2V | prompt text | MP4 | 480p or 720p; 81 frames at 16 fps is the common short-video setting. |
| Animate a starting image | SANA-Video I2V / TI2V | prompt plus first image | MP4 | Native script expects prompt lines containing `<image>` followed by an image path. |
| High-fidelity video texture | SANA-Video + LTX-2 refiner | prompt, 720p SANA-Video model, LTX-2 | MP4 | Stage 1 generates SANA latents, then LTX-2 refines spatial detail. |
| Minute-scale text video | LongSANA | prompt file and long frame count | MP4 set | Uses the LongLive checkpoint/config and `cfg_scale=1.0`. |

Route image-only generation elsewhere. Route training/data prep and evaluation/conversion elsewhere.

## SANA-Video model/config choices

| Choice | Resolution | Native config | Native checkpoint | Diffusers model id | Default dimensions |
| --- | --- | --- | --- | --- | --- |
| 480p | 480p | `configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp.yaml` | `hf://Efficient-Large-Model/SANA-Video_2B_480p/checkpoints/SANA_Video_2B_480p.pth` | `Efficient-Large-Model/SANA-Video_2B_480p_diffusers` | `height=480`, `width=832`, `frames=81` |
| 720p | 720p | `configs/sana_video_config/Sana_2000M_720px_ltx2vae_AdamW_fsdp.yaml` | `hf://Efficient-Large-Model/SANA-Video_2B_720p/checkpoints/SANA_Video_2B_720p.pth` | `Efficient-Large-Model/SANA-Video_2B_720p_diffusers` | `height=704`, `width=1280`, `frames=81` |
| LongSANA | 480p long-context | `configs/sana_video_config/Sana_2000M_480px_adamW_fsdp_longsana.yaml` | `hf://Efficient-Large-Model/SANA-Video_2B_480p_LongLive/checkpoints/SANA_Video_2B_480p_LongLive.pth` | `Efficient-Large-Model/Sana-Video_2B_480p_LongLive_diffusers` | `height=480`, `width=832`, user-chosen long frames |

Key differences:

- 480p SANA-Video uses WanVAE with 16 latent channels and temporal/spatial stride `[4, 8, 8]`.
- 720p SANA-Video uses the LTX-2 VAE with 128 latent channels and stride `[8, 32, 32]`; expect higher VRAM pressure.
- LongSANA uses causal/cached attention and a LongLive sampler/checkpoint for long-context generation.

## Native SANA-Video planning

Use the bundled planner to create commands safely:

```bash
python sub-skills/video-world-streaming/scripts/plan_sana_video_command.py \
  --mode sana-video \
  --resolution 480p \
  --video-task t2v \
  --txt-file prompts.txt \
  --work-dir output/sana_t2v_video_results
```

Canonical native short T2V command shape:

```bash
bash inference_video_scripts/inference_sana_video.sh \
  --np 1 \
  --config configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp.yaml \
  --model_path hf://Efficient-Large-Model/SANA-Video_2B_480p/checkpoints/SANA_Video_2B_480p.pth \
  --txt_file=asset/samples/video_prompts_samples.txt \
  --cfg_scale 6 \
  --motion_score 30 \
  --flow_shift 8 \
  --work_dir output/sana_t2v_video_results
```

Canonical native I2V/TI2V shape:

```bash
bash inference_video_scripts/inference_sana_video.sh \
  --np 1 \
  --config configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp.yaml \
  --model_path hf://Efficient-Large-Model/SANA-Video_2B_480p/checkpoints/SANA_Video_2B_480p.pth \
  --txt_file=asset/samples/sample_i2v.txt \
  --task=ltx \
  --cfg_scale 6 \
  --motion_score 30 \
  --flow_shift 8 \
  --work_dir output/sana_ti2v_video_results
```

Native command notes:

- `--motion_score` is appended to each prompt as `motion score: N.` when positive.
- `--cfg_scale` is commonly `6` for standard short SANA-Video.
- `--flow_shift` is typically `8` for the documented 480p/720p examples, even though the config may contain slightly different internal defaults.
- `--np` controls `accelerate launch --num_processes`; keep it `1` for single-GPU planning unless the user explicitly has a distributed inference setup.
- Native outputs are placed under `work_dir/vis/...` with a generated directory name encoding scale, steps, size, frames, sampler, seed, and motion score.

## Diffusers SANA-Video planning

Use Diffusers when the user specifically asks for pipeline code or wants a minimal Python snippet around `SanaVideoPipeline` / `SanaImageToVideoPipeline`.

T2V concepts:

```python
from diffusers import SanaVideoPipeline
from diffusers.utils import export_to_video

pipe = SanaVideoPipeline.from_pretrained(
    "Efficient-Large-Model/SANA-Video_2B_480p_diffusers",
    torch_dtype=torch.bfloat16,
)
pipe.vae.to(torch.float32)
pipe.text_encoder.to(torch.bfloat16)
pipe.to("cuda")

video = pipe(
    prompt=prompt + " motion score: 30.",
    negative_prompt=negative_prompt,
    height=480,
    width=832,
    frames=81,
    guidance_scale=6,
    num_inference_steps=50,
).frames[0]
export_to_video(video, "sana_video.mp4", fps=16)
```

I2V uses `SanaImageToVideoPipeline`, passes `image=...`, and otherwise uses the same short-video dimensions and guidance parameters.

Diffusers requirements and caveats:

- Use a recent Diffusers build that includes the Sana video pipelines.
- Set VAE/text encoder dtypes deliberately: VAE float32 for the documented 480p Diffusers path; transformer/text encoder bf16 where supported.
- 720p Diffusers uses `Efficient-Large-Model/SANA-Video_2B_720p_diffusers`, `height=704`, `width=1280`, `frames=81`.

## SANA-Video + LTX-2 refiner

Use this when the user wants improved spatial texture or mentions the two-stage refiner.

Bundled planner:

```bash
python sub-skills/video-world-streaming/scripts/plan_sana_video_command.py \
  --mode sana-video-refiner \
  --prompt "A cat and a dog baking a cake together in a kitchen." \
  --output-name sana_ltx2_refined.mp4
```

Canonical command shape:

```bash
python app/sana_video_refiner_pipeline_diffusers.py \
  --sana_model_id Efficient-Large-Model/SANA-Video_2B_720p_diffusers \
  --ltx2_model_id Lightricks/LTX-2 \
  --prompt "A cat and a dog baking a cake together in a kitchen." \
  --sana_height 704 \
  --sana_width 1280 \
  --sana_frames 81 \
  --output_path sana_ltx2_refined.mp4
```

Important behavior:

- Stage 1 generates SANA-Video latents with `SanaVideoPipeline` using `motion_score`, `guidance_scale`, and `num_inference_steps`.
- Stage 1.5 may upsample latents.
- Stage 2 loads `Lightricks/LTX-2`, applies the stage-2 distilled LoRA, creates a zero-style audio latent, and runs a 3-step LTX-2 refinement schedule.
- This path is memory-heavy because it touches SANA-Video, LTX-2 VAE, LTX-2 transformer, audio VAE pieces, and optional latent upsampler.

Validation after planning:

- Confirm the final MP4 exists and is readable.
- Check that frame count equals the requested SANA frame count after any latent/temporal mapping.
- If saving the base SANA output too, compare base and refined paths rather than overwriting one file.

## LongSANA planning

LongSANA is the long-context SANA-Video variant. It is for long text-to-video, not for training in this sub-skill.

Frame rule:

```text
num_frames = seconds * fps + 1
```

Examples:

- 10 seconds at 16 fps -> `161` frames.
- 20 seconds at 16 fps -> `321` frames.
- 60 seconds at 16 fps -> `961` frames.

Native command shape:

```bash
accelerate launch --mixed_precision=bf16 \
  inference_video_scripts/inference_sana_video.py \
  --config=configs/sana_video_config/Sana_2000M_480px_adamW_fsdp_longsana.yaml \
  --model_path=hf://Efficient-Large-Model/SANA-Video_2B_480p_LongLive/checkpoints/SANA_Video_2B_480p_LongLive.pth \
  --work_dir=output/inference/longsana_480p \
  --txt_file=asset/samples/video_prompts_samples.txt \
  --dataset=samples \
  --cfg_scale=1.0 \
  --num_frames 321
```

LongSANA constraints:

- `cfg_scale=1.0` is required for the `longlive_flow_euler` path; the native script asserts this.
- The native code asserts long generation uses the LongLive sampler when `num_frames` exceeds the base model frames.
- Use the 480p LongLive checkpoint/config for public LongSANA planning.
- Long outputs still require enough GPU memory for the model and VAE, even though the attention state is constant-memory.

Diffusers LongSANA notes:

- Public docs show `LongSanaVideoPipeline` with `base_chunk_frames=10`, `num_cached_blocks=-1`, and a short distilled timestep list such as `[1000, 960, 889, 727, 0]`.
- Treat this as development Diffusers support: verify the installed Diffusers build before promising it.

## Validation checklist

For any SANA-Video or LongSANA plan:

1. Confirm prompt source exists and uses the correct format.
2. Confirm `height`, `width`, and `frames` match the chosen checkpoint/config.
3. Confirm motion score is deliberately set or deliberately disabled.
4. Confirm guidance scale matches the family: usually `6` for standard SANA-Video, `1.0` for LongSANA.
5. Confirm output directory or output path is not going to overwrite a valuable file.
6. Confirm the MP4 can be decoded and has the expected number of frames after generation.

## Source-script decisions

- `inference_video_scripts/inference_sana_video.py`: reference-only for generation because it performs model loading and GPU inference; argument surface is distilled here and in the bundled planner.
- `inference_video_scripts/inference_sana_video.sh`: reference-only for production execution; the bundled planner safely reconstructs command shapes instead of launching `accelerate`.
- `app/sana_video_refiner_pipeline_diffusers.py`: reference-only for GPU refiner execution; the planner prints the safer command and warns about memory.
- SANA-Video training scripts and LongSANA training scripts: excluded from this sub-skill; route to `training-data-configs`.
