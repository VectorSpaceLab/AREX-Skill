# Troubleshooting Advanced Control

Related routes: [root backend requirements](../../../references/model-and-backend-requirements.md) · [core-generation](../../core-generation/SKILL.md) · [prompt-conditioning](../../prompt-conditioning/SKILL.md) · [specialized-workflows](../../specialized-workflows/SKILL.md)

Use this file when the advanced-control surface fails or when the user is about to reach for an experimental node that is not the right first move.

## First question: do you actually need advanced control?

If the user only wants:

- a normal T2V/I2V/V2V graph -> route to `core-generation`
- prompt, Gemma, or generic guider setup -> route to `prompt-conditioning`
- IC-LoRA, motion track, HDR, audio, masks, or upscaling recipes -> route to `specialized-workflows`

Do not recommend advanced patches as a generic quality fix.

## Q8 and VAE patching

### Missing backend

Source-level failure:

- `Q8 kernels are not available. To use this feature install the q8_kernels package...`
- `LTXV Q8 Patcher is not applied to the model. Please use LTXQ8Patch node before loading lora or install q8_kernels.`

What to check:

1. Is `q8_kernels` importable?
2. Did the graph patch the exact model instance that the LoRA loader uses?
3. Is the Q8 loader wired after the patch node?
4. Is the VAE patch only being used when the Q8 backend is actually present?

### Environment warning

- A newer CUDA wheel may be recommended for optimized operations on current NVIDIA GPUs.
- A successful import does not prove optimized Q8 execution.
- If ComfyUI reports a `comfy_kitchen` custom-op registration error, fix the environment first.

### Practical fix order

1. Run [../scripts/q8_preflight.py](../scripts/q8_preflight.py).
2. Confirm CUDA is visible.
3. Confirm the q8 backend imports.
4. Rewire the graph so `LTXQ8Patch` is upstream of `LTXVQ8LoraModelLoader`.
5. Only then revisit the VAE patch if the graph actually needs it.

## STG and APG

Common messages and causes:

- `Preset X not found in the presets list.` -> the preset string does not match a bundled preset.
- Manual schedule lists with different lengths -> sigma slots will misalign.
- `skip_steps_sigma_threshold` set too aggressively -> early steps may zero out the result.
- `cfg_star_rescale` overused -> the negative path can become too weak.

Checklist:

1. Confirm whether the user wants the simple STG guider or the advanced schedule.
2. Confirm whether the preset should override manual fields.
3. Confirm that the block list matches the model family.
4. Remember that `block_indices` and `stg_layers_indices` are not the same thing.

## Attention bank, flow-edit, and RF samplers

Source-level failure strings:

- `Can not inject more steps than were saved.`
- `You must save at least as many steps as you want to inject.`

Checklist:

1. Make sure the forward/save pass runs before the reverse/inject pass.
2. Make sure `inject_steps` is less than or equal to `save_steps`.
3. Make sure the attention bank is not filtered down to an empty block set.
4. Make sure the graph is using the exported `LTXRF*` nodes rather than a dead helper path.

## Latent normalization and decoder noise

- `Latents have more frames than reference` means per-frame normalization was asked to do more work than the reference supports.
- `Reference has only one frame, using it for all frames` is a deliberate fallback, not an error.
- If `clip_outliers` is too aggressive, the normalized latent may look flattened or over-sanitized.

For decoder noise, remember that the node only changes the VAE decode settings. It does not repair a bad latent or a mismatched sampler.

## When to stop and route elsewhere

Stop using this skill when the issue is actually about:

- model selection or loader sequencing -> `core-generation`
- prompt / conditioning / generic guider setup -> `prompt-conditioning`
- IC-LoRA or workflow recipes -> `specialized-workflows`

## Good diagnostic order

1. Confirm the task really belongs here.
2. Check whether the advanced feature is optional or experimental.
3. Check the exact node order.
4. Check the exact parameter lengths.
5. Check whether the same graph still works without the trick node.
