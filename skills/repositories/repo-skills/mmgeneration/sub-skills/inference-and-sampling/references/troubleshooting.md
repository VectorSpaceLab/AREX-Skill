# Inference and Sampling Troubleshooting

## Purpose

Use this when a sample, translation, or checkpoint-loading command fails.

## Common failures

### `init_model` cannot load the checkpoint

**Symptoms**
- Missing-file error.
- Shape mismatch or state-dict mismatch while loading weights.

**Likely causes**
- The checkpoint does not match the config family.
- The checkpoint was not downloaded or is not reachable.
- A translation checkpoint is being loaded with an unconditional config, or vice versa.

**Recovery**
- Confirm the config and checkpoint pair from the same model family.
- Re-check the repo's model family in `references/model-overview.md`.

### Conditional sampling complains about labels

**Symptoms**
- Length mismatch errors.
- Type errors for the label argument.

**Likely causes**
- A label list length does not match `num_samples`.
- The label is not a plain integer, integer tensor, or list of integers.

**Recovery**
- Use a single integer when you want one label repeated.
- Use a list whose length matches the requested sample count when you want per-sample labels.

### Translation sampling fails on the model assertion

**Symptoms**
- `sample_img2img_model` asserts that the model is not a translation model.

**Likely causes**
- The config builds an unconditional model, not a `BaseTranslationModel` subclass.

**Recovery**
- Use a Pix2Pix or CycleGAN family config.
- Confirm the input pipeline keys match the translation dataset layout.

### The image path or domain path is wrong

**Symptoms**
- Missing keys in the test pipeline.
- The translated output is empty or not the expected domain.

**Likely causes**
- `target_domain` does not exist in the model.
- The pipeline expects `img_a`/`img_b` or `pair_path` keys that are not being populated.

**Recovery**
- Read `references/data-formats.md`.
- Check the model's test pipeline and domain names before calling the helper.

### DDPM returns a dict instead of a tensor

**Symptoms**
- Downstream code assumes the output is always a tensor.

**Likely causes**
- A sampling kwarg such as `save_intermedia=True` changed the return type.

**Recovery**
- Inspect the dict keys before saving or post-processing.
- Use the bundled helper, which writes `.pt` output for dict cases.

### CUDA device selection fails

**Symptoms**
- Device errors while moving the model or tensor.

**Likely causes**
- The requested device is not available.
- The environment has a CPU-only wheel or an incompatible GPU runtime.

**Recovery**
- Use `--device cpu` for a CPU smoke check.
- For GPU claims, fix the wheel/runtime mismatch and re-run the install check with `--check-cuda`.
