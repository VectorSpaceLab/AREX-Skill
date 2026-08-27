# CycleGAN-Turbo unpaired inference CLI and API

This reference distills the unpaired inference behavior into a self-contained operating guide. It is based on the repository's README unpaired examples, the CycleGAN-Turbo inference entry point, the CycleGAN-Turbo model implementation, the shared model utilities, the image-transform builder, and the documented example input names.

## Source-checkout CLI

The source-checkout entry point is:

```bash
python src/inference_unpaired.py \
  --input_image INPUT_IMAGE \
  (--model_name PRETRAINED_NAME | --model_path CUSTOM_CHECKPOINT) \
  [--output_dir OUTPUT_DIR] \
  [--image_prep IMAGE_PREP] \
  [--prompt PROMPT_FOR_CUSTOM] \
  [--direction a2b|b2a] \
  [--use_fp16]
```

Use exactly one of `--model_name` or `--model_path`. The bundled helper at [../scripts/build_unpaired_inference_command.py](../scripts/build_unpaired_inference_command.py) enforces this rule, catches assertion-prone prompt/direction combinations, and prints the command instead of running model inference.

### CLI flags

| Flag | Required | Default | Valid values | Meaning |
| --- | --- | --- | --- | --- |
| `--input_image` | yes | none | image path | Image to translate. The source script opens it with PIL and converts it to RGB. |
| `--model_name` | exactly one model selector | `None` | `day_to_night`, `night_to_day`, `clear_to_rainy`, `rainy_to_clear` | Selects a built-in pretrained CycleGAN-Turbo checkpoint and built-in caption/direction. |
| `--model_path` | exactly one model selector | `None` | local checkpoint path | Loads a custom CycleGAN-Turbo state dict with `torch.load`. Requires `--prompt` and `--direction`. |
| `--output_dir` | no | `output` | directory path | Created if missing. Output is saved as `OUTPUT_DIR/<input basename>`. README examples use `outputs`. |
| `--image_prep` | no | `resize_512x512` | see image-prep table | Prepares the input image before tensor conversion and normalization. |
| `--prompt` | custom only | `None` | text prompt | Required with `--model_path`; forbidden with `--model_name`. Passed to model forward as `caption`. |
| `--direction` | custom only | `None` | `a2b` or `b2a` | Required with `--model_path`; forbidden with `--model_name`. Built-in pretrained models set it internally. |
| `--use_fp16` | no | false | flag | Calls `model.half()` and converts the input tensor to half precision. |

## Pretrained names, captions, directions, and examples

For pretrained names, the constructor downloads or reuses a checkpoint under the default checkpoint folder, sets `timesteps = [999]` on CUDA, and stores both caption and direction in the model object. Do not provide `--prompt` or `--direction` in this mode.

| `--model_name` | Input domain | Output domain | Checkpoint filename | Built-in caption | Built-in direction | Example input name |
| --- | --- | --- | --- | --- | --- | --- |
| `day_to_night` | day driving image | night driving image | `day2night.pkl` | `driving in the night` | `a2b` | `assets/examples/day2night_input.png` |
| `night_to_day` | night driving image | day driving image | `night2day.pkl` | `driving in the day` | `b2a` | `assets/examples/night2day_input.png` |
| `clear_to_rainy` | clear driving image | rainy driving image | `clear2rainy.pkl` | `driving in heavy rain` | `a2b` | `assets/examples/clear2rainy_input.png` |
| `rainy_to_clear` | rainy driving image | clear driving image | `rainy2clear.pkl` | `driving in the day` | `b2a` | `assets/examples/rainy2clear_input.png` |

Other documented unpaired example names include `assets/examples/my_horse2zebra_input.jpg` and `assets/examples/my_horse2zebra_output.jpg` for a custom-style horse-to-zebra workflow. Those are example names, not a built-in pretrained model selector.

## Custom checkpoint prompt and direction rules

Use `--model_path` when you have a custom CycleGAN-Turbo checkpoint created by unpaired training or an equivalent checkpoint export. In custom mode:

- Always pass `--prompt`; the model stores `caption = None` for custom checkpoints, and the forward pass asserts if neither `caption` nor `caption_emb` is provided.
- Always pass `--direction a2b` or `--direction b2a`; the model stores `direction = None` for custom checkpoints, and the VAE wrappers assert that direction is one of `a2b` or `b2a`.
- Match the prompt to the target domain for the direction. If training used domain A as horse images and domain B as zebra images, `a2b` should use the target-domain B prompt, while `b2a` should use the target-domain A prompt.
- Use the same domain semantics as training data layout: A-to-B maps `train_A`/source-domain images to `train_B`/target-domain images; B-to-A reverses the learned mapping.

The custom checkpoint state dict is expected to contain LoRA ranks, UNet target-module lists, UNet adapter weights, VAE LoRA target modules, and VAE encoder/decoder weights. The model loader reads keys including `rank_unet`, `l_target_modules_encoder`, `l_target_modules_decoder`, `l_modules_others`, `sd_encoder`, `sd_decoder`, `sd_other`, `rank_vae`, `vae_lora_target_modules`, `sd_vae_enc`, and `sd_vae_dec`.

## Python constructor and forward API

The main model class has this constructor shape:

```python
CycleGAN_Turbo(
    pretrained_name=None,
    pretrained_path=None,
    ckpt_folder="checkpoints",
    lora_rank_unet=8,
    lora_rank_vae=4,
)
```

Important constructor behavior:

- It loads SD-Turbo tokenizer, text encoder, VAE, and UNet components.
- It patches VAE encoder/decoder forward functions and creates skip-connection convolutions.
- It calls CUDA methods on the text encoder, VAE skip convolutions, VAE wrappers, and UNet, so source inference has no CPU-only path.
- If `pretrained_name` is one of the four built-in names, it downloads or reuses the corresponding checkpoint and assigns the built-in caption/direction.
- If `pretrained_path` is provided, it loads the local state dict and leaves caption/direction unset for the caller.

The forward signature is:

```python
model.forward(x_t, direction=None, caption=None, caption_emb=None)
```

Forward behavior:

- `x_t` is expected to be a CUDA tensor normalized to approximately `[-1, 1]`, as produced by `ToTensor()` followed by `Normalize([0.5], [0.5])` and `unsqueeze(0).cuda()` in the source inference script.
- If `direction` is omitted, the model uses the built-in pretrained direction and asserts if no built-in direction is available.
- If both `caption` and `caption_emb` are omitted, the model uses the built-in pretrained caption and asserts if no built-in caption is available.
- If `caption_emb` is provided, it bypasses tokenizer/text-encoder caption processing.
- The internal one-step scheduler uses timestep `999`; the decoded output is clamped to `[-1, 1]` before the source script maps it back to PIL image range.

The lower-level static method shape is:

```python
CycleGAN_Turbo.forward_with_networks(
    x, direction, vae_enc, unet, vae_dec, sched, timesteps, text_emb
)
```

Use the CLI unless you need to integrate CycleGAN-Turbo into a larger Python pipeline that already handles device placement, prompts, and tensor normalization.

## Image preprocessing options

The source inference script calls `build_transform(image_prep)` before tensor conversion. Valid values are:

| `image_prep` | Transform behavior | Inference notes |
| --- | --- | --- |
| `resize_512x512` | Resize to `(512, 512)` with LANCZOS interpolation | Source default; safest pretrained starting point. |
| `resize_512` | Same resize branch as `resize_512x512` | Alias accepted by the transform builder. |
| `resized_crop_512` | Resize with scalar size `512`, then center-crop `512` | Useful when you want a square crop while preserving aspect before crop. |
| `resize_256x256` | Resize to `(256, 256)` | Smaller spatial size; may reduce memory and detail. |
| `resize_256` | Same resize branch as `resize_256x256` | Alias accepted by the transform builder. |
| `resize_286_randomcrop_256x256_hflip` | Resize to `(286, 286)`, random-crop `(256, 256)`, random horizontal flip | Training-style stochastic transform; avoid for deterministic single-image inference unless randomness is intentional. |
| `no_resize` | Identity transform | Keeps original size before tensor conversion. Use only when dimensions are compatible with the model path and available memory. |

After model inference, the source script converts the output tensor to a PIL image and resizes it back to the original input image width and height with LANCZOS interpolation. This means the saved file has the original dimensions even when model inference ran at a resized square resolution.
