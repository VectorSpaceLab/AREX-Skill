# Paired Inference CLI and API Reference

This reference distills the paired Pix2Pix-Turbo inference behavior from the public quickstart, `src/inference_paired.py`, `src/pix2pix_turbo.py`, `src/image_prep.py`, and the paired Gradio scripts. It is self-contained so future agents can build commands without reopening those source files.

## Pretrained paired model selectors

Exactly one model selector should be used for normal inference planning:

| Selector | Meaning | Source behavior |
| --- | --- | --- |
| `--model_name edge_to_image` | Canny edge control image to RGB image | Loads `Pix2Pix_Turbo(pretrained_name="edge_to_image")`; if the paired LoRA file is absent under `checkpoints/`, the constructor downloads `edge_to_image_loras.pkl`. |
| `--model_name sketch_to_image_stochastic` | Binary sketch to RGB image with stochastic variation | Loads `Pix2Pix_Turbo(pretrained_name="sketch_to_image_stochastic")`; if absent under `checkpoints/`, the constructor downloads `sketch_to_image_stochastic_lora.pkl`; the model uses a `TwinConv` input blend for stochastic guidance. |
| `--model_path PATH` | Custom Pix2Pix-Turbo checkpoint | Loads `Pix2Pix_Turbo(pretrained_path=PATH)` and uses the generic deterministic paired branch in `src/inference_paired.py`. |

The source script contains a comment saying only one of `model_name` and `model_path` should be provided. Treat that as the operating contract and enforce it before calling the source script. The bundled command builder does this with an argparse mutual-exclusion group.

## Source CLI flags

Source command shape:

```bash
python src/inference_paired.py \
  --input_image INPUT_IMAGE \
  --prompt PROMPT \
  --model_name edge_to_image \
  --output_dir output
```

Flags accepted by the source paired CLI:

| Flag | Required | Default | Used by | Notes |
| --- | --- | --- | --- | --- |
| `--input_image PATH` | yes | none | all modes | Opened with PIL and converted to RGB. The source resizes it down to the nearest width/height divisible by 8 before making tensors. |
| `--prompt TEXT` | yes | none | all modes | Required text prompt; the model forward path asserts that exactly one of `prompt` or `prompt_tokens` is supplied. |
| `--model_name NAME` | selector | empty string | pretrained modes | Use only `edge_to_image` or `sketch_to_image_stochastic` for paired pretrained inference. |
| `--model_path PATH` | selector | empty string | custom checkpoint | Use instead of `--model_name` for a paired checkpoint saved with `Pix2Pix_Turbo.save_model`. |
| `--output_dir DIR` | no | `output` | all modes | Created if absent. Final image is saved as `output_dir` plus the input basename. |
| `--low_threshold INT` | no | `100` | edge-to-image | Canny low threshold passed to OpenCV Canny. |
| `--high_threshold INT` | no | `200` | edge-to-image | Canny high threshold passed to OpenCV Canny. Use a value greater than the low threshold. |
| `--gamma FLOAT` | no | `0.4` | sketch-to-image only | Passed to model forward as stochastic guidance `r`. Gradio exposes the same concept as a 0 to 1 sketch-guidance slider. |
| `--seed INT` | no | `42` | sketch-to-image only | Used with `torch.manual_seed` before creating the latent noise map. |
| `--use_fp16` | no | false | all modes | Calls `model.half()` and casts control/noise tensors to half precision. Requires compatible CUDA execution. |

Use [`../scripts/build_paired_inference_command.py`](../scripts/build_paired_inference_command.py) to validate selector combinations, thresholds, gamma, seed, and image-size warnings before running the source script.

## Output behavior

All paired modes write the final generated image as:

```text
OUTPUT_DIR/<input basename>
```

For `edge_to_image`, the source script also saves an inverted Canny visualization before generation:

```text
OUTPUT_DIR/<input basename with .png replaced by _canny.png>
```

Because that suffix is produced with a literal `.replace('.png', '_canny.png')`, `.png` input names are safest. For a non-`.png` input basename, the preview path is not changed by that replacement and may collide with the final output name.

The paired README examples use these source fixture names:

- `assets/examples/bird.png` -> Canny preview `assets/examples/bird_canny.png` -> output `assets/examples/bird_canny_blue.png`.
- `assets/examples/sketch_input.png` -> output `assets/examples/sketch_output.png`.

Those images are source examples, not bundled runtime dependencies.

## Edge-to-image runtime path

When `--model_name edge_to_image` is selected, the source script:

1. Opens the input as RGB.
2. Resizes width and height down to multiples of 8.
3. Calls `canny_from_pil(input_image, low_threshold, high_threshold)`.
4. Saves an inverted Canny visualization in the output directory.
5. Converts the Canny control image to a tensor with shape `[1, 3, H, W]`, moves it to CUDA, optionally casts to FP16, and calls:

```python
output_image = model(c_t, prompt)
```

`canny_from_pil` converts the PIL image to a NumPy array, runs `cv2.Canny`, expands the single-channel Canny map to three identical channels, and returns a PIL image.

## Sketch-to-image stochastic runtime path

When `--model_name sketch_to_image_stochastic` is selected, the source script:

1. Opens the sketch as RGB.
2. Resizes width and height down to multiples of 8.
3. Converts it to a binary tensor with `F.to_tensor(input_image) < 0.5`.
4. Moves the tensor to CUDA and casts to float.
5. Sets the PyTorch seed from `--seed`.
6. Creates `noise = torch.randn((1, 4, H // 8, W // 8), device=c_t.device)`.
7. Calls:

```python
output_image = model(c_t, prompt, deterministic=False, r=gamma, noise_map=noise)
```

The stochastic `gamma`/`r` value controls interpolation between encoded control and latent noise in the non-deterministic forward path. Source Gradio uses a 0 to 1 slider with default `0.4` for this value.

## Custom checkpoint runtime path

When a custom paired checkpoint path is selected, the source script enters the generic branch:

```python
c_t = F.to_tensor(input_image).unsqueeze(0).cuda()
output_image = model(c_t, prompt)
```

That branch does not use Canny thresholds, stochastic `gamma`, `seed`, or `noise_map`. Use it for deterministic Pix2Pix-Turbo checkpoints produced by the paired training flow, then provide the prompt expected by that checkpoint.

## `Pix2Pix_Turbo` API facts

Constructor signature:

```python
Pix2Pix_Turbo(
    pretrained_name=None,
    pretrained_path=None,
    ckpt_folder="checkpoints",
    lora_rank_unet=8,
    lora_rank_vae=4,
)
```

Forward signature:

```python
forward(
    c_t,
    prompt=None,
    prompt_tokens=None,
    deterministic=True,
    r=1.0,
    noise_map=None,
)
```

Important behavior:

- The constructor loads tokenizer, text encoder, VAE, and UNet components from `stabilityai/sd-turbo`; the text encoder, VAE skip convolutions, UNet, VAE, and timesteps are moved to CUDA in source code.
- `set_eval()` sets UNet and VAE to eval mode and disables their gradients.
- `set_train()` enables LoRA and paired skip/conv training parameters; use the `training` sub-skill for training, not this inference sub-skill.
- `forward` asserts exactly one of `prompt` and `prompt_tokens` is provided.
- Deterministic forward encodes `c_t`, predicts one denoising step at timestep 999, decodes through the VAE, and clamps output to `[-1, 1]`.
- Non-deterministic forward sets LoRA adapter weights from `r`, blends encoded control with `noise_map`, sets `TwinConv.r`, and decodes with VAE decoder `gamma = r`.
- The source CLI converts the first output tensor to a PIL image with `output_image[0].cpu() * 0.5 + 0.5` before saving.

## Custom checkpoint schema notes

`Pix2Pix_Turbo.save_model(outf)` writes a `torch.save` dictionary with these keys:

```text
unet_lora_target_modules
vae_lora_target_modules
rank_unet
rank_vae
state_dict_unet
state_dict_vae
```

The `state_dict_unet` value contains UNet keys whose names include `lora` or `conv_in`; `state_dict_vae` contains VAE keys whose names include `lora` or `skip`. The load path recreates LoRA configs from `rank_*` and `*_target_modules`, adds adapters, then patches the UNet and VAE state dicts with the saved values. A custom checkpoint missing those keys will fail before inference.
