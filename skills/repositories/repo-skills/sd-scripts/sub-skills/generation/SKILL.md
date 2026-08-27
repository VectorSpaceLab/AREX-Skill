---
name: generation
description: "Run and troubleshoot sd-scripts image generation and minimal
  inference CLIs, including txt2img, img2img, inpainting, prompt files, SDXL
  conditioning, LoRA/network application, ControlNet/LLLite, and model-family
  inference scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# sd-scripts Generation

Use this sub-skill when the user wants to generate images, validate prompt files, apply trained LoRA weights during inference, or diagnose generation failures. For LoRA training route to `../training`; for model merging/conversion route to `../model-utilities`; for dataset TOML route to `../data-preparation`.

## Choose the Entry Point

- Use `gen_img.py` for SD 1.x, SD 2.x, SDXL, txt2img, img2img, inpainting-by-mask, prompt files, highres fix, LoRA networks, ControlNet, and ControlNet-LLLite.
- Use `sdxl_gen_img.py` when you want the SDXL-focused script surface and the same prompt-file conventions.
- Use `gen_img_diffusers.py` when the model is a Diffusers pipeline/folder and the user wants Diffusers-style loading.
- Use `inpainting_minimal_inference.py` for a small inpainting script with `--ckpt_path`, `--image`, `--mask`, and `--sdxl` rather than the broader `gen_img.py` interface.
- Use family minimal inference scripts for newer architectures: `sdxl_minimal_inference.py`, `sd3_minimal_inference.py`, `flux_minimal_inference.py`, `lumina_minimal_inference.py`, `hunyuan_image_minimal_inference.py`, `anima_minimal_inference.py`, and `anima_minimal_inference_control_net_lllite.py`.

## Fast Start Commands

Keep commands model-path agnostic and replace placeholders with the user’s files:

```bash
python gen_img.py --ckpt <model.ckpt-or-safetensors-or-diffusers-id> --outdir outputs \
  --fp16 --xformers --W 512 --H 768 --steps 30 --sampler k_euler_a \
  --prompt "masterpiece, detailed illustration --n low quality, blurry"
```

```bash
python gen_img.py --ckpt <model> --outdir outputs --bf16 --sdpa --no_preview \
  --from_file prompts.txt --images_per_prompt 4 --batch_size 2 --seed 1234
```

```bash
python gen_img.py --ckpt <sdxl-model> --sdxl --outdir outputs --bf16 --sdpa \
  --original_width 1024 --original_height 1024 --target_width 1024 --target_height 1024 \
  --prompt "cinematic studio portrait --n distorted face"
```

Before running a batch, validate prompt-file syntax without loading models:

```bash
python skills/sd-scripts/sub-skills/generation/scripts/validate_prompt_file.py prompts.txt --family gen-img
```

## Required References

- `references/commands.md`: command templates for txt2img, img2img, inpainting, SDXL, LoRA, ControlNet, LLLite, and minimal inference scripts.
- `references/prompt-formats.md`: prompt-file syntax, negative prompts, prompt weights, dynamic prompts, per-line options, and model-family differences.
- `references/troubleshooting.md`: diagnosis for model-family flags, path errors, headless preview, precision artifacts, xformers/SDPA, OOM, LoRA count mismatch, ControlNet mismatches, and offline tokenizer cache.

## Practical Workflow

1. Identify the model family first: SD1/SD2/SDXL uses `gen_img.py`; SD3/Flux/Lumina/Hunyuan/Anima use family minimal inference scripts.
2. Confirm required model components exist: checkpoint or DiT plus text encoders plus VAE/AE as required by the selected script.
3. Select precision and memory flags conservatively: start with `--fp16` or `--bf16`, reduce `--batch_size`, reduce resolution, then add VAE slicing/offload flags if needed.
4. Validate prompt files with the bundled script; it catches malformed per-line options, missing values, invalid numeric fields, and likely LoRA multiplier count mistakes.
5. If applying LoRA at inference, match each `--network_module` with a `--network_weights` entry for `gen_img.py`, or use the family script’s `--lora_weights`/`--lora_weight` convention.
6. For ControlNet/LLLite, verify image, mask, and control dimensions and ensure ControlNet and LLLite are not mixed in one `gen_img.py` command.

## Common Decisions

- Prefer `--no_preview` on servers, containers, CI, SSH sessions, and any headless environment.
- Prefer `--sdpa` on modern PyTorch when xformers is unavailable; use `--xformers` only when the package is installed and compatible.
- For SD2 v-parameterized checkpoints, include both `--v2` and `--v_parameterization`; missing `--v_parameterization` can produce brown images.
- For black images or NaNs, retry with `--bf16`, `--no_half_vae`, lower resolution, or fp32 depending on hardware support.
- For prompt weighting, use WebUI-like `(term:1.2)`, `(term)`, and `[term]`; keep generation options separated with spaces, such as `prompt text --n bad anatomy --w 768`.
