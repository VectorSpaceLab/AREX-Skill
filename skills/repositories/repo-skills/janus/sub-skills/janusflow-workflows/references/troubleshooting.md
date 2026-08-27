# JanusFlow Troubleshooting

## Purpose

Use this when the JanusFlow understanding or generation path fails.

## `ModuleNotFoundError: No module named 'diffusers'`

**Likely cause**: the JanusFlow model path imports diffusers for the SDXL VAE and related helpers.

**Recovery**

1. Install a diffusers build compatible with the selected torch wheel.
2. Re-run the JanusFlow import check.
3. Only then try a generation run.

## `AttributeError: module 'torch' has no attribute 'xpu'`

**Likely cause**: the chosen diffusers release expects a newer torch stack than the one installed.

**Recovery**

1. Downgrade diffusers to a version compatible with your torch wheel.
2. Re-run the import check.
3. Keep the compatible version documented in the workflow notes.

## `fp16` VAE instability or wrong dtype errors

**Symptoms**

- The VAE fails to load.
- The generated image is unstable or the decode step errors.

**Likely cause**: the repo notes say to use `bfloat16` for the SDXL VAE.

**Recovery**

1. Keep the VAE in `bfloat16`.
2. Confirm the VAE dtype before generation.
3. Re-run with the documented dtype after the environment is fixed.

## Attention-mask or cache issues

**Symptoms**

- The flow loop errors partway through the ODE updates.
- Shapes do not match the LLM input.

**Likely causes**

- The attention mask length is wrong.
- The generation token was not trimmed before the flow loop.
- The cached state was not rebuilt correctly after the first step.

**Recovery**

1. Re-check the `inputs_embeds` length before the loop.
2. Confirm the mask shape uses the extra generation token.
3. Keep the cached state local to the helper.

## Poor output quality

**Likely causes**

- Wrong prompt tags.
- Wrong `cfg_weight` or `num_inference_steps`.
- Wrong checkpoint or missing VAE access.

**Recovery**

1. Try the published defaults first.
2. Reduce the batch size if VRAM is tight.
3. Compare the JanusFlow prompt path with the Janus / Janus-Pro autoregressive path to avoid mixing them.

## GPU or memory failures

**Symptoms**

- OOM during latent updates or VAE decode.
- CUDA errors during model loading.

**Recovery**

1. Lower the batch size.
2. Use the dry-run helper to confirm the prompt and dependency plan.
3. Switch to a compatible CUDA environment before retrying the real run.
