# optimize-models workflows

Use this decision tree to choose between Core ML package compression and optional PyTorch-side optimization. For original model conversion, artifact inspection, prediction, or MIL pass debugging, route through the sub-skill links in `SKILL.md` first.

## 1. Identify the starting artifact

| Starting point | Use | Avoid |
| --- | --- | --- |
| `.mlpackage` or `MLModel` that is an `mlprogram` | `coremltools.optimize.coreml` | Re-converting unless the model is not an `mlprogram` or has wrong deployment target. |
| `.mlmodel` neuralnetwork/classic model | Convert/re-export to `mlprogram` first if package compression is required | Calling Core ML optimization APIs that require `mlprogram`. |
| PyTorch source model | Optional `coremltools.optimize.torch` if PyTorch imports and data/training loop are available; then convert | Claiming Torch optimization works when PyTorch is absent or import fails. |
| TensorFlow/sklearn/tree model | Convert to Core ML first | Torch optimization APIs. |

## 2. Choose the compression family

### Weight quantization

Choose when model size and memory bandwidth matter and small numerical error is acceptable.

- Start with `OpLinearQuantizerConfig(mode="linear_symmetric", dtype="int8", granularity="per_channel")`.
- For more compression, test `dtype="int4"` or blockwise settings on selected large layers.
- Use `op_name_configs={name: None}` to skip sensitive layers.
- Validate by comparing against the uncompressed model or a decompressed debug model.

### Palettization

Choose when weights have repeated values, clusterable distributions, or the target model benefits from LUT/index compression.

- Start with `OpPalettizerConfig(mode="kmeans", nbits=4, granularity="per_tensor")` for Core ML data-free compression.
- Use `mode="unique"` only when weights already lie on a small discrete lattice; do not set `nbits` for unique mode.
- Use `mode="uniform"` for deterministic histogram-like LUTs.
- Increase `num_kmeans_workers` only when CPU budget and multiprocessing are acceptable.
- For PyTorch fine-tuning palettization, use `DKMPalettizer` only after PyTorch imports and a training loop exists.

### Pruning

Choose when many weights are already zero/near-zero, or when a training/fine-tuning plan can tolerate sparsity.

- For Core ML, use `OpThresholdPrunerConfig` when near-zero weights already exist.
- Use `OpMagnitudePrunerConfig(target_sparsity=...)` for percentile pruning.
- Use `block_size` or `n_m_ratio` only for supported `linear` and `conv` layers and test carefully.
- Sparse representation is stored only when the final sparsity satisfies the configured minimum or target conditions.

### Activation quantization

Choose when representative Core ML input dictionaries are available and calibration can run.

- Prepare `sample_data` as a list of dictionaries matching Core ML model input names.
- Run `linear_quantize_activations` first, then optional `linear_quantize_weights` for A8W8.
- If calibration creates very large temporary models, reduce `calibration_op_group_size`.
- Prediction/calibration execution has platform/runtime limits; route to model IO and prediction guidance when needed.

## 3. Data-free Core ML package compression flow

```python
import coremltools as ct
import coremltools.optimize.coreml as cto

mlmodel = ct.models.MLModel("model.mlpackage")

# Inspect large weights before choosing skips.
metadata = cto.get_weights_metadata(mlmodel, weight_threshold=2048)
print(list(metadata.keys())[:10])

# Conservative first pass: int8 per-channel weight quantization.
config = cto.OptimizationConfig(
    global_config=cto.OpLinearQuantizerConfig(
        mode="linear_symmetric",
        dtype="int8",
        granularity="per_channel",
        weight_threshold=2048,
    )
)
compressed = cto.linear_quantize_weights(mlmodel, config)
compressed.save("model-w8.mlpackage")
```

Escalation path:

1. If all targeted weights are skipped, lower `weight_threshold` or target a larger op by name/type.
2. If accuracy drops, skip output/classifier/norm-adjacent layers by op name and retest.
3. If size reduction is insufficient, compare W8 quantization, W4 quantization, palettization, and pruning separately before joint compression.
4. If a compressed model fails to load, call `decompress_weights` and inspect both specs before changing conversion.

## 4. Calibration-data Core ML activation quantization flow

```python
import numpy as np
import coremltools.optimize.coreml as cto

sample_data = [
    {"input": np.random.rand(1, 3, 224, 224).astype("float32")},
    # Replace with representative real samples.
]

act_config = cto.OptimizationConfig(
    global_config=cto.OpLinearQuantizerConfig(mode="linear_symmetric", dtype="int8")
)
a8_model = cto.linear_quantize_activations(mlmodel, act_config, sample_data)

weight_config = cto.OptimizationConfig(
    global_config=cto.OpLinearQuantizerConfig(mode="linear_symmetric", dtype="int8")
)
a8w8_model = cto.linear_quantize_weights(a8_model, weight_config)
```

Use this only when calibration inputs are representative. Random data is acceptable for a smoke test, not for a production compression decision.

## 5. Optional Torch pre-export optimization flow

Use this only when `import coremltools.optimize.torch` and the requested optimizer submodule import successfully.

General pattern:

```python
# Pseudocode: choose the concrete optimizer for the family.
optimizer = OptimizerClass(torch_model, OptimizerConfig.from_dict(config_dict))
prepared = optimizer.prepare()
for batch in calibration_or_training_data:
    output = prepared(batch)
    # Run loss/backward/optimizer steps if the chosen optimizer requires fine-tuning.
    optimizer.step()
final_torch_model = optimizer.finalize(prepared, inplace=True)
```

Then convert the final Torch model using conversion guidance. Keep source-model conversion details out of this sub-skill and route to conversion when needed.

### Torch workflow selection

| Need | Recommended Torch API family | Requires |
| --- | --- | --- |
| Data-free quantization | `PostTrainingQuantizer` | PyTorch model, supported modules. |
| QAT or activation-aware quantization | `LinearQuantizer` | PyTorch model, calibration/training loop. |
| GPTQ quantization | `LayerwiseCompressor` with GPTQ config | Calibration data and layer selection. |
| Data-free palettization | `PostTrainingPalettizer` | PyTorch model. |
| Sensitive k-means palettization | `SKMPalettizer` | Calibration data and loss function. |
| Differentiable palettization | `DKMPalettizer` | Training loop and `step()` schedule. |
| Magnitude pruning | `MagnitudePruner` | Optional scheduler/training loop. |
| SparseGPT pruning | `LayerwiseCompressor` with SparseGPT config | Calibration data and layer selection. |

## 6. Joint compression flow

Always test single compression families first. Joint compression combines trade-offs and can make failures harder to isolate.

### Core ML package examples

Palettize then quantize LUT:

```python
pal_config = cto.OptimizationConfig(global_config=cto.OpPalettizerConfig(mode="kmeans", nbits=4))
pal_model = cto.palettize_weights(mlmodel, pal_config)

lut_q_config = cto.OptimizationConfig(
    global_config=cto.OpLinearQuantizerConfig(mode="linear_symmetric", dtype="int8", granularity="per_tensor")
)
pal_w8_model = cto.linear_quantize_weights(pal_model, lut_q_config, joint_compression=True)
```

Prune then quantize non-zero values:

```python
prune_config = cto.OptimizationConfig(global_config=cto.OpMagnitudePrunerConfig(target_sparsity=0.8))
pruned = cto.prune_weights(mlmodel, prune_config)

q_config = cto.OptimizationConfig(global_config=cto.OpLinearQuantizerConfig(mode="linear_symmetric"))
pruned_q = cto.linear_quantize_weights(pruned, q_config, joint_compression=True)
```

Prune then palettize non-zero values:

```python
pruned_pal = cto.palettize_weights(pruned, pal_config, joint_compression=True)
```

## 7. Minimal smoke workflow

Use the bundled helper before debugging a user's large model:

```bash
python sub-skills/optimize-models/scripts/optimize_coreml_smoke.py --help
python sub-skills/optimize-models/scripts/optimize_coreml_smoke.py --output smoke.mlpackage
python sub-skills/optimize-models/scripts/optimize_coreml_smoke.py --output smoke-w8.mlpackage --compression linear
```

The helper keeps `coremltools` imports in a child process so `--help` remains safe even in broken optional-dependency environments. It reports non-zero child exits instead of hiding import, conversion, or optimization failures.
