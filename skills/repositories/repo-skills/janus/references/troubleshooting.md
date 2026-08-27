# Troubleshooting

## Purpose

Read this when the package imports but the workflow still fails. These are the most likely Janus-family issues to diagnose before retrying with the generated skill.

## Common failures

### `ModuleNotFoundError: No module named 'torchvision'`

**Where it shows up**: importing `janus.models.image_processing_vlm` or any workflow that uses `load_pil_images` and the processor.

**Likely cause**: the package metadata does not declare `torchvision`, but the source image processor imports it.

**Recovery**:

1. Install `torchvision` compatible with your torch wheel.
2. Re-run the import check from `scripts/check_janus_environment.py`.
3. Retry the understanding workflow.

### `ModuleNotFoundError: No module named 'diffusers'`

**Where it shows up**: importing `janus.janusflow.models` or running JanusFlow generation.

**Likely cause**: JanusFlow needs diffusers even though the base package does not.

**Recovery**:

1. Install a compatible `diffusers` build.
2. If the newest release breaks with your torch wheel, choose an older compatible release.
3. Re-run the JanusFlow import check before attempting generation.

### `AttributeError: module 'torch' has no attribute 'xpu'`

**Where it shows up**: some newer diffusers releases import `torch.xpu` helpers before the model loads.

**Likely cause**: the chosen diffusers release expects a newer torch stack than the one installed for Janus.

**Recovery**:

1. Downgrade to a diffusers version that is compatible with the torch wheel in use.
2. Re-run the JanusFlow import check.
3. Keep the compatibility choice documented in the workflow notes.

### `torch.cuda.is_available() == False`

**Where it shows up**: the repo's example scripts and demos call `.cuda()` directly.

**Likely cause**: the environment has no GPU-visible torch runtime, an incompatible wheel, or missing device passthrough.

**Recovery**:

1. Check the installed torch wheel and GPU visibility.
2. Use the CPU dry-run mode of the generated scripts if you only need prompt validation.
3. For real model generation, switch to a CUDA-capable environment.

### Placeholder / image-count mismatch

**Where it shows up**: `VLChatProcessor` input preparation.

**Likely cause**: the prompt contains image placeholders that do not match the number of images, or the images are not RGB.

**Recovery**:

1. Load images with `load_pil_images`.
2. Make sure every image placeholder in the prompt has a corresponding image.
3. Convert non-RGB images before batching.

### Wrong roles or template format

**Where it shows up**: `apply_sft_template_for_multi_turn_prompts` and generation setup.

**Likely cause**: Janus and Janus-Pro snippets use different role tokens in the README examples.

**Recovery**:

1. Match the conversation roles to the model family.
2. For dry-run validation, print the formatted prompt before generating.
3. If the answer looks echoed or truncated, inspect the chosen template first.

### Generation output is empty, noisy, or just echoes the prompt

**Where it shows up**: understanding workflows after decoding.

**Likely cause**: bad prompt formatting, wrong `pad_id`, missing `trust_remote_code`, or an incompatible checkpoint.

**Recovery**:

1. Inspect the formatted prompt and token layout.
2. Re-check the model id and template family.
3. Re-run a tiny image fixture to confirm the processor path before a full model run.

### Gradio/FastAPI demo import failures

**Where it shows up**: demo launch.

**Likely cause**: missing optional dependencies such as `gradio`, `fastapi`, `uvicorn`, or `python-multipart`.

**Recovery**:

1. Install the demo dependencies required by the route.
2. Prefer the generated lazy-loading service skeleton over the original import-time demo script.
3. Verify the endpoint names and payload fields before testing the server.

## Debugging order

1. Run the environment check script.
2. Verify the import path for the relevant sub-skill.
3. Validate the prompt/image layout with the bundled helper.
4. Only then try a real model download or demo launch.
