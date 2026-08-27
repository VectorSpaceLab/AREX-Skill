# Inference workflows

This page shows the DreamOmni2 command-line flows for image editing and image generation.

## Editing workflow

The editing workflow keeps the source image first and the reference image second.

```bash
python sub-skills/inference/scripts/inference_edit.py \
  --input_img_path /path/to/source.jpg /path/to/reference.jpg \
  --input_instruction "Make the woman from the second image stand on the road in the first image." \
  --output_path /tmp/dreamomni2_edit.png
```

What the wrapper does:

1. Loads the VLM checkpoint from `--vlm-path`.
2. Loads the editing LoRA from `--edit-lora-path`.
3. Builds the VLM prompt by appending the editing prefix.
4. Resizes the two images to the nearest Kontext bucket.
5. Runs the FLUX.1-Kontext pipeline and saves one edited image.

## Generation workflow

The generation workflow also uses two images, but it loads the generation LoRA and lets you choose the output size.

```bash
python sub-skills/inference/scripts/inference_gen.py \
  --input_img_path /path/to/reference1.jpg /path/to/reference2.jpg \
  --input_instruction "Compose the two characters into a spaceship interior scene." \
  --height 1024 \
  --width 1024 \
  --output_path /tmp/dreamomni2_gen.png
```

What the wrapper does:

1. Loads the VLM checkpoint from `--vlm-path`.
2. Loads the generation LoRA from `--gen-lora-path`.
3. Builds the VLM prompt by appending the generation prefix.
4. Uses the requested `height` and `width`, defaulting to `1024 x 1024`.
5. Runs the FLUX.1-Kontext pipeline and saves one generated image.

## Default model-path assumptions

The bundled wrappers assume these local paths unless you override them:

- `models/vlm-model`
- `models/edit_lora`
- `models/gen_lora`
- `black-forest-labs/FLUX.1-Kontext-dev` for the base model

See `../../references/model-setup.md` before launching if those paths are not already available.

## Prompt-stage notes

- The instruction text is suffixed with a task-specific prefix before it is sent to the VLM.
- The VLM output is then normalized and passed as the final diffusion prompt.
- If the prompt looks wrong, inspect the raw VLM text before changing the diffusion model itself.

## Validation checks

- Run `sub-skills/inference/scripts/inference_edit.py --help` and `sub-skills/inference/scripts/inference_gen.py --help` to confirm argument parsing.
- Run `scripts/check_models.py` to confirm the local paths before any real inference.
