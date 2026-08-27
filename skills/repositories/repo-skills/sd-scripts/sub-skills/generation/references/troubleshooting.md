# Generation Troubleshooting

## Model Family and Precision

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Load error immediately after checkpoint selection | Wrong `--v2` or `--sdxl` family flag | Match the checkpoint family: SD1 default, SD2 `--v2`, SDXL `--sdxl` |
| Brown SD2 images | Missing or incorrect `--v_parameterization` | Add `--v2 --v_parameterization` for v-parameterized SD2 checkpoints |
| Black images or NaNs | fp16 instability, VAE half precision, unsupported bf16, or too aggressive memory settings | Try `--bf16` on supported GPUs, `--no_half_vae`, lower resolution, smaller batch, or fp32 |
| Washed-out or artifact-heavy images | VAE mismatch or precision artifacts | Pass the intended `--vae`, use `--no_half_vae`, and test a known-good prompt |
| Tokenizer download failure offline | Tokenizer cache unavailable | Pre-populate cache and pass `--tokenizer_cache_dir <cache-dir>` where supported |

## Missing Paths and Component Mismatches

- `gen_img.py` requires `--ckpt`; it can be a checkpoint file, Diffusers folder, or model ID depending on environment support.
- SD3 and Flux minimal scripts require multiple text encoder/autoencoder components. Missing `--clip_l`, `--clip_g`, `--t5xxl`, or `--ae` paths produce early load failures.
- Hunyuan and Anima minimal scripts require DiT/model, VAE, and Qwen-family text encoder paths; Hunyuan may also use ByT5.
- Keep model paths and output paths outside prompt files; prompt files should only describe prompts and per-prompt generation options.

## Preview and Headless Environments

If interactive mode fails while trying to show an image, the environment may have headless OpenCV or no display server. Use one of these fixes:

```bash
python gen_img.py --ckpt <model> --outdir outputs --interactive --no_preview
```

or avoid interactive preview entirely:

```bash
python gen_img.py --ckpt <model> --outdir outputs --from_file prompts.txt --no_preview
```

Installing a GUI-enabled OpenCV can help on desktop machines, but `--no_preview` is safer for servers and agent-run workflows.

## xformers, SDPA, and Memory

- If `--xformers` fails to import or complains about CUDA/PyTorch versions, remove it and try `--sdpa` on PyTorch 2.
- If OOM occurs during denoising, reduce `--batch_size`, `--images_per_prompt`, `--W`, `--H`, or steps.
- If OOM occurs near the end of generation, reduce `--vae_batch_size`, add `--vae_slices 16` or `--vae_slices 32`, or add `--no_half_vae` if artifacts are also present.
- For minimal scripts, use `--offload`, `--blocks_to_swap`, `--text_encoder_cpu`, smaller dimensions, or fewer steps when available.
- Avoid combining high resolution, large batch size, multiple LoRAs, ControlNet, and highres fix until a small single-image run succeeds.

## Prompt File Problems

Common mistakes:

- Missing spaces around prompt options: write `text --n bad`, not `text--n bad`.
- Missing option values: `--w`, `--h`, `--s`, `--d`, `--l`, `--am`, and SDXL conditioning options need values.
- Seed list length mismatch: if `--images_per_prompt 4`, `--d 1,2` only provides two explicit seeds.
- LoRA multiplier mismatch: `--am 0.8,0.5` expects two loaded networks or LLLite contexts that understand the value.
- Shell-style quotes inside prompt files are usually literal text, not shell parsing. Prefer unquoted prompt text unless the script’s prompt parser explicitly supports quotes.

Run:

```bash
python skills/sd-scripts/sub-skills/generation/scripts/validate_prompt_file.py prompts.txt --family gen-img --images-per-prompt 4 --expected-networks 2
```

## LoRA and Network Issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Argument/parser error for networks | Count mismatch among `--network_module`, `--network_weights`, and `--network_mul` | Repeat `networks.lora` once per LoRA and provide matching weights/multipliers |
| LoRA has no visible effect | Wrong trigger words, too-low multiplier, wrong base model family, or wrong network module | Confirm trigger text, increase `--network_mul`, match SD1/SDXL/Flux/etc., and use the correct LoRA option for the selected script |
| Regional LoRA error or wrong regions | `AND` region count, mask channels, and LoRA weight count do not align | Match LoRA count to regions and verify the RGB mask channel content |
| `--am` ignored | `--network_merge` was used or script does not support per-prompt multiplier override | Remove `--network_merge` for per-prompt overrides |

Training new LoRA weights belongs in `../training`; durable model merging/conversion belongs in `../model-utilities`.

## ControlNet, LLLite, and Masks

- Regular ControlNet and ControlNet-LLLite are separate paths; do not pass both families in the same `gen_img.py` command.
- For Canny ControlNet, use `--control_net_preps canny_63_191` or another threshold pair. For other control types, preprocess the guide image and use `none` if needed.
- Ensure `--guide_image_path`, `--control_image`, `--mask_image`, or per-prompt `--cn`/`--mk` files exist before running generation.
- If the result ignores structure, increase ControlNet weight/multiplier or ratio; if the result is overconstrained, reduce it.
- If masks behave inverted, remember that inpainting masks use white for regions to regenerate.
- For folder-based image/mask inputs, ensure sorted filenames line up with prompt lines and each other.

## Diagnosing Black or Brown Images Quickly

1. Re-run a single 512px or 768px prompt with no LoRA, no ControlNet, batch size 1.
2. Verify model family flags: SD1 default, SD2 `--v2`, SD2-v `--v2 --v_parameterization`, SDXL `--sdxl`.
3. Switch precision: try `--bf16` on supported GPUs, otherwise try fp32 or `--no_half_vae`.
4. Confirm VAE compatibility or omit custom `--vae` to test the checkpoint’s bundled VAE.
5. Add LoRA and ControlNet back one component at a time.
