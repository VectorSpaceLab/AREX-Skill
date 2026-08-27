# optimize-models troubleshooting

Start with the smallest failing step: import, load, metadata, one compression family, save, optional prediction. Do not debug a full joint flow until single-family compression works.

## Import and optional dependency failures

### `coremltools.optimize.coreml` fails to import

Likely causes:

- Broken `coremltools` installation or incompatible Python/runtime dependencies.
- Optional framework packages imported by `coremltools` are installed but ABI-incompatible.
- Local package shadowing, such as a file named `coremltools.py` in the working directory.

Actions:

1. Run the root environment diagnostic if available.
2. Try importing the smallest module needed: `import coremltools.optimize.coreml as cto`.
3. If the import crashes instead of raising Python exceptions, reproduce in a clean environment with only `coremltools` and required conversion dependencies.
4. Use the bundled smoke helper's `--help` first; it avoids importing `coremltools` in the parent process.

### `coremltools.optimize.torch` fails to import

This is expected when PyTorch is not installed or not compatible. Do not claim Torch optimizers work until the specific submodule imports.

Actions:

- For Core ML artifacts, use `coremltools.optimize.coreml` instead.
- For PyTorch source optimization, install a compatible PyTorch version and retest the exact optimizer import.
- If Torch is intentionally absent, present only Core ML package compression workflows.

## Model type and conversion errors

### Core ML optimizer rejects the model type

Symptoms include errors mentioning `mlprogram`, graph pass application, or unsupported model representation.

Actions:

1. Confirm the artifact is an `MLModel` and an `mlprogram` package.
2. If it is a neuralnetwork/classic `.mlmodel` or an original framework model, route to conversion before compression.
3. Re-convert with a deployment target compatible with the requested compression feature.
4. If the failure is inside MIL graph rewriting, route to MIL/debugging.

### Compression runs but no weights change

Likely causes:

- All weights are below `weight_threshold`.
- Selected ops are unsupported by that compression family.
- `op_type_configs` or `op_name_configs` skipped the only eligible weights.
- Palettization `unique` mode found too many unique values.
- Block size/granularity constraints caused per-block compression to skip the tensor.

Actions:

1. Call `get_weights_metadata(mlmodel, weight_threshold=0)` to inspect eligible weights.
2. For smoke tests only, set `weight_threshold=0`.
3. For production, lower `weight_threshold` gradually and target only large layers.
4. Verify exact op names before adding `op_name_configs`.

## Config validation failures

### Linear quantization config is rejected

Check:

- `mode` must be `"linear_symmetric"` or `"linear"`.
- `dtype` must be `"int8"`, `"uint8"`, `"int4"`, or `"uint4"`.
- `granularity` must match allowed values for the current config.
- `block_size` must be non-negative and compatible with the weight shape when per-block quantization is used.
- `weight_threshold` must be non-negative or `None` where accepted.

### Palettizer config is rejected

Check:

- `mode` must be `"kmeans"`, `"uniform"`, `"unique"`, or `"custom"`.
- `nbits` is required for `"kmeans"` and `"uniform"`.
- `nbits` must not be set for `"unique"` or `"custom"`.
- Valid `nbits` values are `1`, `2`, `3`, `4`, `6`, and `8`.
- `lut_function` is required for `"custom"` and must be omitted otherwise.
- Dict/YAML loaders do not support passing a callable `lut_function`; construct custom configs in Python.

### Pruner config is rejected

Check:

- `threshold` must be non-negative.
- `minimum_sparsity_percentile` must be between `0` and `1`.
- `target_sparsity` must be between `0` and `1`.
- `block_size` and `n_m_ratio` are structured pruning choices for supported `linear` and `conv` layers, not arbitrary ops.
- Do not set contradictory pruning modes unless the config class explicitly supports the combination.

## Calibration and prediction issues

### Activation quantization cannot calibrate

Likely causes:

- `sample_data` keys do not match model input names.
- Multiple inputs were provided with unnamed sample entries.
- Input array shape/dtype does not match the Core ML model spec.
- Runtime platform cannot execute the model for calibration.
- Temporary calibration model is too large.

Actions:

1. Inspect model inputs with the model IO sub-skill.
2. Supply `sample_data` as `[{"input_name": numpy_array, ...}, ...]`.
3. Use a small representative calibration subset first.
4. Lower `calibration_op_group_size` if temporary model loading hangs or consumes too much memory.
5. If prediction/runtime is unavailable on the current platform, run weight-only compression locally and defer activation calibration to a supported runtime.

### Compressed model saves but prediction changes too much

Actions:

1. Compare uncompressed vs compressed outputs on representative samples where prediction is available.
2. Also compare compressed vs `decompress_weights(compressed)` to distinguish runtime compressed execution from graph rewrite issues.
3. Skip sensitive layers by op name, especially output heads, normalization-adjacent weights, embeddings, and small classifier layers.
4. Prefer int8/per-channel before int4, blockwise, or joint compression.
5. Test one compression family at a time.

## Joint compression failures

Symptoms include large accuracy regressions, unexpected model size, or graph-pass errors after the second compression call.

Actions:

1. Verify each single compression family independently.
2. Decompress the first compressed model and inspect the graph/spec before applying the second family.
3. For palettize-then-quantize, start with `granularity="per_tensor"` for LUT quantization.
4. For prune-then-quantize/palettize, confirm enough non-zero or sparse structure remains after pruning.
5. Keep `joint_compression=True` only when intentionally compressing an already-compressed representation.

## Bundled smoke helper failures

Command:

```bash
python sub-skills/optimize-models/scripts/optimize_coreml_smoke.py --output smoke.mlpackage --compression linear
```

Interpretation:

- `--help` fails: the Python interpreter itself or script path is wrong.
- Child process import fails: fix the `coremltools` environment before debugging a model.
- Conversion fails: route to conversion/MIL debugging; the minimal MIL program should be convertible in a healthy environment.
- Compression fails: inspect the optimizer import and config; retry with `--compression none` to isolate conversion from optimization.
- Save fails: check output path permissions and whether an existing `.mlpackage` directory needs removal or a new path.

The helper uses a child process so it can report Python exceptions and non-zero child exits cleanly. Native crashes in dependencies still require environment repair.
