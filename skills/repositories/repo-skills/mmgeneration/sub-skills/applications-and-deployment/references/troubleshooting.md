# Applications and Deployment Troubleshooting

## Purpose

Use this when latent editing, projection, CLIP-guided generation, or TorchServe packaging fails.

## Common failures

### StyleCLIP dies immediately on import

**Symptoms**
- The script exits before parsing the main arguments.
- A missing `clip` dependency is reported.

**Likely causes**
- The optional OpenAI CLIP package is not installed.
- The script's import guard currently raises a string, so the visible failure can become a `TypeError` after the missing-import branch is hit.

**Recovery**
- Install the optional CLIP dependency before rerunning.
- If you only need the workflow description, use the bundled references instead of trying to run the script blindly.

### Projection or interpolation looks wrong

**Symptoms**
- The generated images do not correspond to the input image or expected latent walk.
- The projection file does not deserialize as the script expects.

**Likely causes**
- The checkpoint is not a StyleGAN-like generator.
- The latent format does not match the helper's `w`/`w+` expectation.
- The script is being used with a translation or diffusion model instead of a StyleGAN-family model.

**Recovery**
- Verify the model family in `references/model-overview.md`.
- Check the latent-space assumption before selecting an editing helper.
- Use the projection helper output as the warm-start for downstream editing only when the model family matches.

### StyleGAN editing is unstable or very slow

**Symptoms**
- The optimization loop runs for a long time.
- The results drift or change unexpectedly between runs.

**Likely causes**
- The helper is doing true latent optimization, not a cheap inference call.
- The random seed, truncation, or edit weights were not fixed.

**Recovery**
- Treat the workflow as an expensive expert task.
- Fix the seed and the truncation/edit weights when comparing runs.
- Use a tiny command-planning check before launching a long edit session.

### TorchServe packaging fails

**Symptoms**
- The packager cannot import `model_archiver`.
- The generated archive is missing the config or handler.
- The serving client cannot connect to the inference endpoint.

**Likely causes**
- `torch-model-archiver` is not installed.
- The config/checkpoint pair does not match the unconditional handler's expectations.
- TorchServe is not running or is listening on a different address/port.

**Recovery**
- Install the packaging toolchain first.
- Confirm the handler type matches the checkpoint family.
- Start or point the client at a live TorchServe server before expecting an HTTP response.

### Unconditional handler returns bad image bytes

**Symptoms**
- The response bytes cannot be decoded as an RGB image.
- The output shape is wrong or appears color-swapped.

**Likely causes**
- The handler expects a standard `[-1, 1]` RGB tensor.
- The postprocess step swaps channels before converting to bytes.

**Recovery**
- Verify the model output contract before packaging.
- Keep the handler for unconditional generation only unless you adapt it deliberately.

## When to escalate

Stop and ask for a narrower scope or a different backend when the fix requires:

- A StyleGAN-compatible checkpoint that is not available.
- The optional CLIP package.
- A live TorchServe server or the archiver toolchain.
- GPU resources for the expensive latent-editing path.
