# Unpaired inference troubleshooting

Use this guide when CycleGAN-Turbo unpaired inference fails before a translated image is saved. Start by rebuilding the command with the bundled helper so argument errors are caught before model import, CUDA allocation, or checkpoint download.

## Quick triage

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Helper says exactly one model selector is required | Neither or both of `--model_name` and `--model_path` were supplied | Choose pretrained mode or custom mode, not both. |
| Helper rejects `--prompt` with `--model_name` | Pretrained models already embed their caption | Remove `--prompt`; for `day_to_night`, the built-in caption is `driving in the night`. |
| Helper rejects `--direction` with `--model_name` | Pretrained models already embed their direction | Remove `--direction`; use direction only with custom checkpoints. |
| Helper rejects custom mode without prompt/direction | Custom checkpoints leave caption and direction unset | Add the target-domain `--prompt` and `--direction a2b` or `--direction b2a`. |
| Source run fails with CUDA errors | The model and scheduler call CUDA paths directly | Use a CUDA-capable environment/GPU; do not treat CPU import as proof of inference support. |
| Source run fails near xformers attention setup | `model.unet.enable_xformers_memory_efficient_attention()` could not enable xformers | Use torch/xformers versions compatible with the installed CUDA stack, or make a deliberate local source edit to guard the call. |
| Source run fails while downloading or loading checkpoints | Network/cache issue, partial checkpoint file, or incompatible checkpoint | Retry after network is available; delete any corrupt partial `.pkl` before retrying; verify custom checkpoint schema. |
| Output exists but has unexpected filename | Source saves with the input basename | Look for `OUTPUT_DIR/<input basename>`, not a name based on model or direction. |

## CUDA and xformers

CycleGAN-Turbo source inference is CUDA-bound:

- The constructor moves the CLIP text encoder, VAE skip convolutions, VAE wrappers, and UNet to CUDA.
- The one-step scheduler sets timesteps and cumulative alphas on CUDA.
- The inference entry point converts the preprocessed input tensor with `.cuda()`.
- The inference entry point always calls `model.unet.enable_xformers_memory_efficient_attention()`.

Recovery steps:

1. Confirm the active runtime can import torch and see a CUDA device before running full inference.
2. If CUDA is available but memory is tight, try `--use_fp16` and a smaller deterministic image prep such as `resize_256x256`. This does not change the need for CUDA.
3. If xformers fails due to missing wheels or version mismatch, align torch, CUDA, and xformers versions. Do not silently remove xformers guidance from the command; if you patch the source call, record that it is a local runtime workaround.
4. If full model downloads are not approved, stop after command construction; do not claim inference was run.

## Prompt and direction assertions

The most common argument mistakes are pretrained commands with extra custom arguments and custom commands missing required custom arguments.

### Pretrained command with unnecessary prompt

Bad:

```bash
python src/inference_unpaired.py \
  --model_name day_to_night \
  --input_image assets/examples/day2night_input.png \
  --prompt "driving in the night" \
  --output_dir outputs
```

Why it fails: pretrained `day_to_night` already sets caption `driving in the night`, and the inference entry point asserts that `--prompt` is not required when loading a pretrained model.

Good:

```bash
python src/inference_unpaired.py \
  --model_name day_to_night \
  --input_image assets/examples/day2night_input.png \
  --output_dir outputs
```

### Custom checkpoint without prompt or direction

Bad:

```bash
python src/inference_unpaired.py \
  --model_path checkpoints/custom_cyclegan_turbo.pkl \
  --input_image path/to/domain_a_image.png \
  --output_dir outputs_custom
```

Why it fails: custom checkpoint loading sets both caption and direction to `None`. The CLI requires a prompt for custom paths, and model forward/VAE wrappers require a concrete direction.

Good:

```bash
python src/inference_unpaired.py \
  --model_path checkpoints/custom_cyclegan_turbo.pkl \
  --input_image path/to/domain_a_image.png \
  --prompt "<target-domain-B prompt>" \
  --direction a2b \
  --output_dir outputs_custom
```

### Invalid or swapped direction

Only `a2b` and `b2a` are valid directions. `a2b` means source-domain A to target-domain B; `b2a` reverses the mapping. If output semantics look reversed but the command succeeds, check the training domain naming and the prompt before changing model files.

## Image prep and resize behavior

Valid `--image_prep` values are `resize_512x512`, `resize_512`, `resized_crop_512`, `resize_256x256`, `resize_256`, `resize_286_randomcrop_256x256_hflip`, and `no_resize`.

Failure and recovery notes:

- Invalid image-prep strings are unsafe because the transform builder only assigns a transform for known values. Use the helper to validate choices before running the source script.
- `resize_512x512` is the source default and safest first attempt for pretrained checkpoints.
- `resize_286_randomcrop_256x256_hflip` includes random crop and random horizontal flip. Avoid it for deterministic single-image comparisons unless stochastic preprocessing is desired.
- `no_resize` keeps original dimensions before model inference. Use it only when image dimensions and memory are compatible with the VAE/UNet path; if a shape error appears, retry with `resize_512x512` or dimensions compatible with the model's downsampling behavior.
- The saved image is resized back to the original input width and height. Do not use saved dimensions alone to infer the internal inference resolution.

## Checkpoint downloads and custom checkpoint loading

Pretrained runs download or reuse checkpoint filenames `day2night.pkl`, `night2day.pkl`, `clear2rainy.pkl`, or `rainy2clear.pkl` in the default `checkpoints` folder. The model also loads SD-Turbo tokenizer, text encoder, scheduler, VAE, and UNet components through the installed model libraries, which may use their own caches.

Recovery steps:

1. If the first run fails while downloading, retry after network/proxy/cache access is fixed.
2. If a partial checkpoint file exists, the downloader may skip it on the next run because the filename already exists. Delete the suspect `.pkl` file and retry.
3. If `torch.load` fails for a custom checkpoint, verify it is a CycleGAN-Turbo checkpoint with the expected LoRA and VAE keys, not a Pix2Pix-Turbo checkpoint or a full training directory.
4. Keep pretrained names exact. An unknown `--model_name` is not a custom path; use the helper's known-name validation.

## Output naming and overwrite behavior

The source script uses:

- `os.path.basename(input_image)` as the output filename;
- `os.makedirs(output_dir, exist_ok=True)` before saving;
- `output_pil.save(os.path.join(output_dir, basename))`.

Consequences:

- `--output_dir outputs --input_image a/b/day.png` saves `outputs/day.png`.
- Running different models on files with the same basename in the same output directory can overwrite earlier results.
- If you need side-by-side comparisons, use separate output directories such as `outputs_day_to_night`, `outputs_night_to_day`, and `outputs_custom_a2b`.
