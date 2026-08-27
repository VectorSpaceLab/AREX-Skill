# Conversion Troubleshooting

## Full converter fails on `qtorch`

### Symptoms
- Import-time errors mention `qtorch`.
- The build fails while trying to compile `quant_cuda` or another CUDA extension.
- The traceback mentions `CUDA_HOME`, `nvcc`, or `ninja`.

### Likely causes
- The optional quantization helper cannot find a usable CUDA toolkit.
- The environment does not have the build tools required for the extension.

### Recovery
- Install `ninja`.
- Set `CUDA_HOME` to a valid CUDA install root if the toolkit exists.
- Confirm that `nvcc` is available before trying the full converter again.
- If you only need metadata export or LoRA surgery, use the bundled lightweight helpers instead.

## Dummy-meta export fails

### Symptoms
- The script refuses a path.
- The input does not look like a safetensors file or directory.

### Likely causes
- The input is not a `.safetensors` file or a directory containing them.

### Recovery
- Point the script at a valid safetensors source.
- Use the directory mode only when the directory really contains `.safetensors` files.

## LoRA extraction or merge skips many keys

### Symptoms
- The output has fewer tensors than expected.
- The script prints many skipped, failed, or incomplete pairs.

### Likely causes
- The source and target checkpoints are not the same family.
- The LoRA weights use a naming convention that the mapping logic does not expect.
- The source and target shapes do not match.

### Recovery
- Re-check the checkpoint family and branch.
- Re-check the LoRA format.
- Use `--diff-only` if the goal is to preserve raw weight deltas instead of rank decomposition.

## Output-format confusion

### Symptoms
- The output file has the wrong suffix.
- The user expects one format but the script wrote another.

### Likely causes
- The output suffix does not match the selected output format.
- A path was given without a suffix and the script auto-appended one.

### Recovery
- Re-read the script help text.
- Pick the output format explicitly and then check the written path.

## What not to do

- Do not route a runtime generation failure into this sub-skill just because the model uses a converted checkpoint.
- Do not treat a copied checkpoint as valid until the key mapping and tensor counts look sensible.
- Do not rely on the full converter when a lightweight helper is enough.
