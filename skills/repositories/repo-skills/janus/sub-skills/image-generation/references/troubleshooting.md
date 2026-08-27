# Image Generation Troubleshooting

## Purpose

Use this when the generation loop or decode step fails.

## `CUDA` / `.cuda()` failures

**Symptoms**

- `.cuda()` raises an error.
- The model never starts because the example assumes a GPU.

**Likely causes**

- No CUDA-capable torch runtime.
- Wrong torch wheel for the host GPU.
- A CPU-only environment is trying to run a GPU-only generation pattern.

**Recovery**

1. Check CUDA visibility with the environment script.
2. Use the dry-run helper if you only need prompt validation.
3. Switch to a CUDA-capable environment for the actual generation run.

## `pad_id` is missing or wrong

**Symptoms**

- The unconditional branch is not masked as expected.
- Generation quality collapses.

**Likely causes**

- The processor/tokenizer mismatch is wrong.
- The prompt uses the wrong family-specific template.

**Recovery**

1. Inspect the formatted prompt.
2. Confirm the selected family.
3. Re-run the bundled dry-run helper.

## `past_key_values` issues

**Symptoms**

- A loop variable is undefined on the first pass.
- The generation loop reuses caches incorrectly.

**Likely causes**

- The token loop was copied without a proper first-iteration initialization.

**Recovery**

1. Ensure the first forward pass seeds the cache correctly.
2. Keep the loop state local to the helper.
3. Prefer the generated script over hand-written ad hoc loops.

## Shape mismatch in `decode_code`

**Symptoms**

- Decoding fails or produces oddly shaped images.

**Likely causes**

- `img_size` and `patch_size` do not match the decoder shape.
- The number of generated tokens does not match the expected image token count.

**Recovery**

1. Keep the default `576`, `384`, and `16` values unless you know the decoder math.
2. Confirm the output tensor shape before decoding.
3. Reduce the sample count while debugging.

## Poor or unstable output quality

**Likely causes**

- Wrong model family or checkpoint.
- Template mismatch.
- Seed not fixed.
- Guidance too low or too high.

**Recovery**

1. Try the default `cfg_weight=5` and a fixed seed.
2. Verify the family and checkpoint id.
3. Re-check the prompt format before changing sampler settings.

## Output directory problems

**Symptoms**

- Images are not written.
- The helper fails when saving files.

**Likely causes**

- The output directory does not exist.
- The current user cannot write there.

**Recovery**

1. Use a writable output directory.
2. Create the directory before the run.
3. Re-run the helper after the path is fixed.
