# Paired Inference Troubleshooting

Use this page to recover from common paired Pix2Pix-Turbo inference and Gradio failures without reopening source files.

## Selector and argument failures

### Both `--model_name` and `--model_path` are supplied

Symptom: ambiguous command such as:

```bash
python src/inference_paired.py --model_name edge_to_image --model_path checkpoints/custom.pkl ...
```

Recovery:

1. Choose exactly one selector.
2. Use `--model_name edge_to_image` for the pretrained Canny pipeline.
3. Use `--model_name sketch_to_image_stochastic` for the pretrained stochastic sketch pipeline.
4. Use `--model_path PATH` for a custom paired Pix2Pix-Turbo checkpoint.
5. Rebuild the command with [`../scripts/build_paired_inference_command.py`](../scripts/build_paired_inference_command.py), which rejects both selectors before any model code runs.

### Unknown or empty pretrained name

Symptom: a source run with an unsupported `--model_name` falls out of the named branches and can fail while trying to load a checkpoint path. Recovery: use only `edge_to_image` or `sketch_to_image_stochastic` as pretrained paired names, or switch to `--model_path` for a custom checkpoint.

### Custom checkpoint has the wrong schema

Symptom: load-time key errors around ranks, target modules, LoRA weights, VAE skip weights, or state dict patching.

Recovery: verify that the checkpoint is a Pix2Pix-Turbo paired checkpoint with these saved keys:

```text
unet_lora_target_modules
vae_lora_target_modules
rank_unet
rank_vae
state_dict_unet
state_dict_vae
```

A generic Stable Diffusion, ControlNet, CycleGAN-Turbo, or training framework checkpoint is not sufficient for `Pix2Pix_Turbo(pretrained_path=...)`.

## Prompt failures

### Missing or empty prompt

The source CLI marks `--prompt` as required. The model forward path also asserts that exactly one of `prompt` and `prompt_tokens` is provided. Recovery: pass a concrete text prompt for every paired mode, including custom checkpoint inference.

### Sketch style prompt becomes unexpectedly long

The sketch Gradio demo wraps the user text with a selected style template. If results are off-topic, inspect the template text in the UI and simplify either the style or the prompt. CLI sketch inference does not apply those Gradio style templates automatically; pass the full desired prompt text yourself.

## CUDA and precision failures

### `Torch not compiled with CUDA enabled`, `CUDA unavailable`, or CUDA allocation errors

Source paired inference is CUDA-oriented. `Pix2Pix_Turbo` moves the text encoder, VAE skip convolutions, UNet, VAE, and timesteps to CUDA, and the paired CLI moves control tensors and stochastic noise tensors to CUDA.

Recovery:

1. Use an environment with CUDA-capable PyTorch and an NVIDIA GPU.
2. Check CUDA availability before full inference:

   ```bash
   python - <<'PY'
   import torch
   print('cuda_available=', torch.cuda.is_available())
   if torch.cuda.is_available():
       print('device=', torch.cuda.get_device_name(0))
   PY
   ```

3. If memory is tight, try source flag `--use_fp16`, but only in a CUDA environment that supports half precision.
4. Reduce input resolution before inference; the source only rounds dimensions down to multiples of 8 and does not otherwise cap image size.
5. Do not assume a CPU fallback exists for full model inference.

### FP16 output errors

Symptom: half-precision dtype errors or poor results after `--use_fp16`.

Recovery: rerun without `--use_fp16` first. If full precision works, the failure is precision/backend specific rather than a command construction issue.

## xformers and dependency failures

The paired Pix2Pix-Turbo source keeps `unet.enable_xformers_memory_efficient_attention()` commented out, but the repository environment may still include xformers-related dependency constraints. If installation fails on xformers, use a wheel compatible with the installed PyTorch/CUDA pair or install the rest of the required inference stack without assuming xformers enables CPU inference. For paired model execution, CUDA is still required by source code.

If imports fail for `diffusers`, `transformers`, `peft`, `torchvision`, `PIL`, `cv2`, or `gradio`, install the repository requirements in the active source-checkout environment before running source commands. The safe command builders can run without importing the heavy model stack; `preview_canny.py` imports OpenCV only when writing a preview.

## Checkpoint and model download failures

### First run stalls or fails while downloading

Pretrained paired constructors download paired LoRA checkpoints into `checkpoints/` when missing:

- `edge_to_image_loras.pkl` for `edge_to_image`.
- `sketch_to_image_stochastic_lora.pkl` for `sketch_to_image_stochastic`.

The same run may also need access to Stable Diffusion Turbo model components through the model-loading stack.

Recovery:

1. Confirm network access and permission to download model weights before launching full inference or Gradio.
2. Check that `checkpoints/` is writable from the source checkout.
3. If a partial `.pkl` file was created during an interrupted download, remove or replace that partial file before retrying.
4. If the model-loading stack is configured for offline mode, pre-populate the expected caches and checkpoint files before running.
5. Use the bundled command builders while downloads are unavailable; they validate commands without importing or downloading models.

## Image-size and tensor-shape failures

### Non-multiple-of-8 input dimensions

The source paired CLI and Gradio Canny path resize inputs down by subtracting the remainder modulo 8. Example: a 513x513 sketch becomes 512x512. In sketch mode, the latent noise map shape is then `(1, 4, 64, 64)` because it is created from `H // 8` and `W // 8`.

Recovery:

1. Pre-resize or pad images yourself if exact framing matters.
2. Use the command builder to warn about non-divisible dimensions when the input can be inspected.
3. Avoid images smaller than 8 pixels on either axis; rounding down could produce a zero dimension.

### Output name collision for edge preview

The edge branch saves an inverted Canny preview using a literal `.replace('.png', '_canny.png')`. With non-`.png` basenames, that replacement does not add a suffix and can collide with the final output path.

Recovery: use `.png` inputs for edge-to-image, or save to an empty output directory and rename/copy outputs immediately after inference.

## Canny threshold failures

### Invalid threshold range

OpenCV Canny expects numeric thresholds. The source defaults are low `100` and high `200`; Gradio Canny sliders use range 1 to 255. Bad ranges can produce empty or noisy control maps.

Recovery:

1. Keep thresholds within 0 to 255.
2. Keep low threshold lower than high threshold.
3. Preview the edge map before full inference:

   ```bash
   python sub-skills/paired-inference/scripts/preview_canny.py \
     --input_image path/to/input.png \
     --output_image outputs/canny_preview.png \
     --low_threshold 100 \
     --high_threshold 200 \
     --invert-preview
   ```

4. If the preview is too sparse, lower thresholds; if it is too noisy, raise thresholds.

## Sketch gamma and seed failures

### `gamma` outside useful range

The stochastic source path passes `--gamma` as `r` to the model forward path and uses it to scale adapter weights and blend encoded control with latent noise. The Gradio sketch slider constrains this value to 0 through 1 with default 0.4.

Recovery:

1. Use `0 <= gamma <= 1` for planned commands.
2. Increase gamma for stronger sketch/control adherence.
3. Decrease gamma for more stochastic variation.
4. Fix `--seed` when comparing prompts or gamma values.

### Sketch with gamma and 513x513 image

Expected behavior: the source resizes 513x513 down to 512x512, then creates stochastic noise at 64x64 latent resolution. If the user expected 513x513 output, pre-pad or resize deliberately before running.

## Gradio launch failures and server risks

### Gradio command starts downloads or fails before the page opens

Both paired Gradio scripts instantiate the model at import time. The UI may not appear until CUDA setup and checkpoint/model downloads finish. Recovery: validate the intended command with [`../scripts/build_gradio_command.py`](../scripts/build_gradio_command.py), then run only after CUDA and downloads are approved.

### Sketch demo exposes a shared link

The source sketch Gradio script launches with `share=True`; the Canny script launches with `share=False`. Recovery: before running the sketch demo on an untrusted network or with private inputs, edit the launch configuration or run in an isolated environment. The bundled Gradio helper only prints the command and warning; it does not launch a server.

### UI component/version errors

The source demos use Gradio APIs such as canvas/color-sketch image settings, queued Blocks, and custom JavaScript/CSS. If launch fails with component argument errors, use the repository-pinned Gradio version from its requirements rather than a much newer or older Gradio release.

### Port already in use or long-running process remains active

Recovery: stop the old Gradio process, choose a different port if using Gradio CLI options, or restart from a clean shell. Do not run multiple GPU-backed Gradio demos simultaneously unless the GPU has enough memory for multiple Pix2Pix-Turbo instances.
