# Conversion and Profiling Troubleshooting

## Purpose

Read this when export, throughput, or loss-landscape workflows fail even though the model and config look reasonable.

## Missing export dependency

### Symptom
- `ImportError` for `coremltools` or a related export dependency.

### Cause
- The current environment only has the base package, not the optional export stack.

### Recovery
- Install the export dependency only if the user actually asked for CoreML conversion.
- If the user only needs a train/eval smoke, keep the export dependency optional.

## CoreML support warning

### Symptom
- `coremltools` prints a warning about scikit-learn support.

### Cause
- The installed scikit-learn version is outside the range that the conversion API expects.

### Recovery
- Treat the warning as a signal that the conversion path may be partially disabled.
- Recheck the conversion stack if the user needs the scikit-learn converter path specifically.

## Missing input image or wrong export preprocessing

### Symptom
- Conversion succeeds only with a random tensor, or it fails when an image path is provided.

### Cause
- `conversion.input_image_path` is missing or the preprocessing path does not match the recipe.

### Recovery
- Provide an explicit image path when you want a deterministic export smoke.
- Verify the preprocessing keys in the config before retrying.

## Model not exportable

### Symptom
- The conversion wrapper fails even though the model builds and trains.

### Cause
- The chosen family does not expose a compatible export path, or the family needs an export-friendly wrapper first.

### Recovery
- Confirm the family in `../../../references/model-overview.md`.
- Check whether the model has a `get_exportable_model()` path.
- If not, switch back to the model sub-skill before retrying export.

## Benchmarking problems

### Symptom
- Throughput numbers are noisy or slower than expected.
- The benchmark takes too long for a simple smoke check.

### Cause
- Warmup and iteration counts are too large, the JIT path is not the intended path, or the device/backend does not match the recipe.

### Recovery
- Start with a tiny batch size and a small iteration count.
- Turn on `--benchmark.use-jit-model` only when you want the traced path.
- Keep CPU and CUDA benchmarking separate when comparing numbers.

## Loss-landscape issues

### Symptom
- The loss-landscape run fails before it produces any output.

### Cause
- The config or checkpoint does not match the model, or the grid settings are not compatible with the selected run.

### Recovery
- Reconfirm the checkpoint and the family selection.
- Use a small grid first.
- Switch back to the training or model sub-skill if the failure is really a checkpoint or registry problem.
