# Image Generation Workflows

## Purpose

Use these recipes to convert a text prompt into one or more Janus-family images.

## Dry-run workflow

The bundled script can validate the prompt and generation parameters without downloading weights:

```bash
python sub-skills/image-generation/scripts/janus_text_to_image.py \
  --family janus-pro \
  --model-id deepseek-ai/Janus-Pro-1B \
  --prompt "A close-up high-contrast photo of a dog under blue light." \
  --output-dir ./generated_samples
```

Expected validation:

- The prompt is wrapped in the family-specific SFT template.
- The generation parameters are printed.
- No model download or image generation occurs until `--run-model` is added.

## Janus / Janus-Pro generation

1. Load the processor and tokenizer.
2. Build a single-turn conversation.
3. Apply the SFT template.
4. Append `image_start_tag`.
5. Encode the prompt to token ids.
6. Construct the conditional and unconditional token batches.
7. Run the generation loop with classifier-free guidance.
8. Decode the token grid to images and save them.

### Key generation details

- `cfg_weight` controls the guidance strength.
- `parallel_size` determines how many candidate images are sampled.
- `image_token_num_per_image` is 576 in the published examples.
- `img_size` and `patch_size` must stay consistent with the decoder shape.
- Use a fixed seed when you need reproducible output samples.

## Practical choices

- Use a smaller `parallel_size` first when VRAM is limited.
- Keep the family-specific role tokens consistent with the selected checkpoint.
- Choose a writable `output_dir` before the run starts.
- Check the tokenizer/model family if output quality degrades after a code change.

## When generation fails

If the token loop crashes, inspect the following first:

- prompt/template construction,
- `pad_id` handling,
- `past_key_values` initialization,
- output shape passed to `decode_code`,
- CUDA availability and dtype.

Then retry with the dry-run helper and a smaller sample count before a full run.
