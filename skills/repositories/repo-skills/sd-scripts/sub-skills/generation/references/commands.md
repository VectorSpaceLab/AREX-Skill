# Generation Command Templates

These templates are self-contained command patterns for sd-scripts generation. Replace placeholders such as `<model>`, `<image.png>`, and `<lora.safetensors>` with user-provided files. Generation requires model weights and usually a GPU or large CPU runtime; these commands are reference patterns, not safe lightweight tests.

## Main `gen_img.py` Surface

### SD 1.x txt2img

```bash
python gen_img.py --ckpt <sd15-model.safetensors> --outdir outputs/txt2img \
  --fp16 --xformers --W 512 --H 768 --steps 30 --scale 7.5 \
  --sampler k_euler_a --images_per_prompt 2 \
  --prompt "best quality, a small robot reading a book --n low quality, blurry"
```

### SD 2.x and v-parameterization

```bash
python gen_img.py --ckpt <sd2-model.safetensors> --v2 --outdir outputs/sd2 \
  --fp16 --sdpa --W 768 --H 768 --steps 30 --scale 7.0 \
  --prompt "landscape photograph, mountain lake --n low contrast"
```

For v-parameterized SD2 checkpoints, add `--v_parameterization`:

```bash
python gen_img.py --ckpt <sd2-v-model.safetensors> --v2 --v_parameterization \
  --outdir outputs/sd2-v --bf16 --sdpa --W 768 --H 768 \
  --prompt "clean architectural render --n brown tint, artifacts"
```

### SDXL txt2img with conditioning

```bash
python gen_img.py --ckpt <sdxl-model.safetensors> --sdxl --outdir outputs/sdxl \
  --bf16 --sdpa --W 1024 --H 1024 --steps 30 --scale 6.5 \
  --original_width 1024 --original_height 1024 --target_width 1024 --target_height 1024 \
  --crop_top 0 --crop_left 0 \
  --prompt "cinematic portrait, rim lighting --n deformed hands, text"
```

Per-line SDXL prompt options can override conditioning: `--ow`, `--oh`, `--nw`, `--nh`, `--ct`, and `--cl`.

### Prompt file batch

```bash
python gen_img.py --ckpt <model> --outdir outputs/from-file --fp16 --xformers \
  --W 512 --H 768 --steps 28 --scale 7.5 --sampler k_euler_a \
  --from_file prompts.txt --images_per_prompt 4 --batch_size 2 --seed 1234
```

Use `--n_iter` to repeat the full file, `--iter_same_seed` to reuse the same generated seeds across iterations when prompt lines do not specify seeds, and `--shuffle_prompts` to randomize prompt-line order per iteration.

### Interactive mode on a local desktop

```bash
python gen_img.py --ckpt <model> --outdir outputs/interactive --fp16 --xformers --interactive
```

On headless servers, add `--no_preview` or use `--prompt`/`--from_file` instead of interactive preview workflows.

### img2img

```bash
python gen_img.py --ckpt <model> --outdir outputs/img2img --fp16 --xformers \
  --image_path input.png --strength 0.65 --W 768 --H 768 \
  --prompt "watercolor repaint, gentle texture --n jpeg artifacts, blurry" \
  --batch_size 1 --images_per_prompt 4
```

If `--image_path` is a folder, files are consumed in string-sorted filename order. Use zero-padded names such as `0001.png` to avoid `1, 10, 2` ordering surprises.

### Inpainting with `gen_img.py`

```bash
python gen_img.py --ckpt <model> --outdir outputs/inpaint --fp16 --xformers \
  --image_path source.png --mask_image mask.png --strength 0.85 \
  --prompt "replace masked area with red flowers --n seams, blurry"
```

The `gen_img.py` mask workflow performs img2img on the mask area. White mask regions are regenerated; soft mask edges usually blend better.

### Dedicated inpainting minimal script

```bash
python inpainting_minimal_inference.py --ckpt_path <inpaint-model.safetensors> \
  --image source.png --mask mask.png --prompt "repair the empty wall" \
  --negative_prompt "text, watermark" --width 512 --height 512 \
  --steps 30 --guidance_scale 7.5 --seed 42 --output_dir outputs/inpaint
```

Add `--sdxl` for an SDXL inpainting model.

## LoRA and Additional Networks During Generation

### Single LoRA

```bash
python gen_img.py --ckpt <base-model> --outdir outputs/lora --fp16 --xformers \
  --network_module networks.lora --network_weights <lora.safetensors> --network_mul 0.8 \
  --prompt "subject in the trained style --n low quality"
```

### Multiple LoRAs

```bash
python gen_img.py --ckpt <base-model> --outdir outputs/multi-lora --fp16 --xformers \
  --network_module networks.lora networks.lora \
  --network_weights <style-lora.safetensors> <character-lora.safetensors> \
  --network_mul 0.5 0.8 \
  --prompt "style trigger, character trigger --n bad anatomy"
```

The counts for `--network_module`, `--network_weights`, and `--network_mul` must align. Per-prompt `--am 0.4,0.8` can override multipliers for a line. `--network_merge` can speed up generation but disables per-prompt `--am` and Regional LoRA behavior; use merge/conversion guidance from `../model-utilities` for durable merged checkpoints.

### Regional LoRA and attention regions

```bash
python gen_img.py --ckpt <base-model> --outdir outputs/regional --fp16 --xformers \
  --network_module networks.lora networks.lora \
  --network_weights <left-region.safetensors> <right-region.safetensors> \
  --mask_path region-mask.png \
  --prompt "left subject AND right subject --n bad composition"
```

For Regional LoRA, the number of LoRAs should match the `AND` prompt regions. RGB channels in the mask map to the first prompt regions; all-zero channels apply that region globally.

## ControlNet and LLLite

### ControlNet with Canny preprocessing

```bash
python gen_img.py --ckpt <model> --outdir outputs/controlnet --bf16 --xformers \
  --control_net_models <controlnet-canny.safetensors> \
  --control_net_preps canny_63_191 --control_net_weights 1.0 \
  --control_net_ratios 1.0 --guide_image_path guide.png \
  --prompt "precise line-art guided character --n distorted lines"
```

For non-Canny ControlNet models, preprocess the guide image yourself and set the prep to `none`.

### ControlNet-LLLite with `gen_img.py`

```bash
python gen_img.py --ckpt <model> --outdir outputs/lllite --bf16 --xformers \
  --control_net_lllite_models <lllite.safetensors> \
  --control_net_multipliers 0.8 --control_net_ratios 1.0 \
  --guide_image_path guide.png \
  --prompt "guided composition, clean edges --n noisy edges"
```

Do not combine regular ControlNet and ControlNet-LLLite in the same `gen_img.py` run.

### Anima LLLite minimal inference

```bash
python anima_minimal_inference_control_net_lllite.py --dit <dit-path> --vae <vae-path> \
  --text_encoder <text-encoder-path> --lllite_weights <lllite.safetensors> \
  --control_image guide.png --prompt "a cat on a chair" \
  --image_size 1024 1024 --infer_steps 50 --save_path outputs/anima-lllite
```

In `--from_file` mode, per-prompt `--cn <path>` overrides the control image and `--am <float>` overrides the LLLite multiplier.

## Minimal Inference Scripts by Family

### SDXL minimal inference

```bash
python sdxl_minimal_inference.py --ckpt_path <sdxl-model.safetensors> \
  --prompt "a cat in a garden" --negative_prompt "low quality" \
  --width 1024 --height 1024 --steps 30 --output_dir outputs/sdxl-min
```

### SD3 minimal inference

```bash
python sd3_minimal_inference.py --ckpt_path <sd3-mmdit.safetensors> \
  --clip_g <clip-g-path> --clip_l <clip-l-path> --t5xxl <t5xxl-path> \
  --prompt "modern product photo" --negative_prompt "blur" \
  --width 1024 --height 1024 --steps 40 --cfg_scale 5.0 --bf16 \
  --output_dir outputs/sd3
```

Use `--lora_weights <file...>` and `--merge_lora_weights` when applying SD3 LoRA weights.

### Flux or Chroma minimal inference

```bash
python flux_minimal_inference.py --ckpt_path <flux-or-chroma.safetensors> \
  --model_type flux --clip_l <clip-l-path> --t5xxl <t5xxl-path> --ae <ae-path> \
  --prompt "editorial photo of a glass sculpture" --negative_prompt "low detail" \
  --width 1024 --height 768 --steps 30 --guidance 3.5 --cfg_scale 1.0 \
  --dtype bfloat16 --offload --output_dir outputs/flux
```

Use `--lora_weights <file...>` for Flux LoRA weights and `--merge_lora_weights` when the script should merge them into the model for the run.

### Lumina minimal inference

```bash
python lumina_minimal_inference.py --ckpt_path <lumina-model> \
  --prompt "fantasy landscape at sunrise" --negative_prompt "flat lighting" \
  --image_width 1024 --image_height 1024 --steps 36 --guidance_scale 3.5 \
  --dtype bf16 --gemma2_dtype bf16 --ae_dtype bf16 --offload \
  --output_dir outputs/lumina
```

Lumina interactive mode accepts prompt-line options such as `--w`, `--h`, `--s`, `--d`, `--g`, `--n`, and LoRA multipliers.

### Hunyuan Image minimal inference

```bash
python hunyuan_image_minimal_inference.py --dit <dit-path> --vae <vae-path> \
  --text_encoder <qwen-vl-path> --byt5 <byt5-path> \
  --prompt "high detail poster design" --negative_prompt "text artifacts" \
  --image_size 2048 2048 --infer_steps 50 --save_path outputs/hunyuan \
  --text_encoder_cpu --blocks_to_swap 8
```

Use `--lora_weight <file...>` and `--lora_multiplier <float...>` for Hunyuan LoRA application.

### Anima minimal inference

```bash
python anima_minimal_inference.py --dit <dit-path> --vae <vae-path> \
  --text_encoder <qwen3-path> --prompt "anime key visual" \
  --negative_prompt "bad anatomy" --image_size 1024 1024 \
  --infer_steps 50 --save_path outputs/anima
```

Use `--from_file` or `--interactive` for repeated prompts. Use `--latent_path` to decode precomputed latents without running full inference.
