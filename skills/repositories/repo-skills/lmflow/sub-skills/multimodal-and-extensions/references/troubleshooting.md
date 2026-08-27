# Multimodal Troubleshooting

## Missing Pillow / Multimodal Support

**Symptom**: the dataset backend or image helpers fail to import.

**Likely cause**: Pillow is missing from the environment.

**Recovery**: install the multimodal/Pillow dependency and re-run the import smoke check.

## Missing Gradio

**Symptom**: the browser UI import fails.

**Likely cause**: the optional `gradio` extra is not installed.

**Recovery**: install the UI extra or use the CLI recipe instead.

## Bad Image Paths

**Symptom**: the loader cannot open an image file.

**Likely cause**: `image_folder` is wrong or the training JSON points at a missing file.

**Recovery**: run the dataset validator and fix the relative filenames.

## Prompt / Separator Mismatch

**Symptom**: tokenization warnings, malformed prompts, or empty responses.

**Likely cause**: the dataset `sep_style` does not match the prompt family.

**Recovery**: use `plain` for two-turn image-caption data and `v1` for LLaVA-style alternation.

## Missing Projector Checkpoint

**Symptom**: stage 2 cannot reuse the stage 1 result.

**Likely cause**: the projector file was not saved or the path is stale.

**Recovery**: make sure stage 1 ran with `save_language_projection=True` and point stage 2 to the saved file.

## Legacy Loader Gap

**Symptom**: the current checkout has the multimodal helpers but not the exact end-to-end loader you expected.

**Likely cause**: the archived multimodal recipe differs from the current core model loader.

**Recovery**: report the gap explicitly and treat the recipe as compatibility guidance rather than a guaranteed route.
