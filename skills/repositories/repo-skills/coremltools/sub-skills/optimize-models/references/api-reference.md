# optimize-models API reference

This reference is for operating with public `coremltools.optimize.coreml` and optional `coremltools.optimize.torch` APIs. Import the smallest submodule you need, and treat Torch APIs as optional until PyTorch and `coremltools.optimize.torch` import successfully.

## Core ML package compression APIs

Use these when the user already has an `MLModel` of type `mlprogram`.

```python
import coremltools as ct
import coremltools.optimize.coreml as cto

mlmodel = ct.models.MLModel("model.mlpackage")
```

| Task | API | Required config | Notes |
| --- | --- | --- | --- |
| Weight linear quantization | `cto.linear_quantize_weights(mlmodel, config, joint_compression=False)` | `OptimizationConfig(global_config=OpLinearQuantizerConfig(...))` | Converts float weight constants to compressed constexpr forms. Supports 4-bit and 8-bit integer weight storage; computation remains float. |
| Weight palettization | `cto.palettize_weights(mlmodel, config, joint_compression=False)` | `OptimizationConfig(global_config=OpPalettizerConfig(...))` | Replaces supported weights with LUT/index representations. Use for repeated or clusterable weights. |
| Weight pruning | `cto.prune_weights(mlmodel, config, joint_compression=False)` | `OptimizationConfig(global_config=OpThresholdPrunerConfig(...)` or `OpMagnitudePrunerConfig(...))` | Stores sufficiently sparse weights in sparse representation. |
| Decompression | `cto.decompress_weights(mlmodel)` | None | Produces an `MLModel` with compressed weights decompressed back to dense constants for debugging/compatibility checks. |
| Weight metadata | `cto.get_weights_metadata(mlmodel, weight_threshold=2048)` | None | Returns weight/op metadata useful for op-type and op-name targeting. |
| Activation quantization | `cto.linear_quantize_activations(mlmodel, config, sample_data, calibration_op_group_size=-1)` | `OptimizationConfig(...)` plus sample input dictionaries | Requires representative Core ML input dictionaries and model execution during calibration. Use with weight quantization for A8W8 flows. |

### `OptimizationConfig` targeting precedence

```python
config = cto.OptimizationConfig(
    global_config=cto.OpPalettizerConfig(mode="kmeans", nbits=4),
    op_type_configs={"linear": cto.OpPalettizerConfig(mode="uniform", nbits=6)},
    op_name_configs={"classifier_head": None},
)
```

Precedence is `op_name_configs` > `op_type_configs` > `global_config`. A `None` value skips compression for that op type or op name. Use `get_weights_metadata` before relying on exact op names.

## Core ML config classes

### `OpLinearQuantizerConfig`

Common safe start:

```python
q_config = cto.OptimizationConfig(
    global_config=cto.OpLinearQuantizerConfig(
        mode="linear_symmetric",
        dtype="int8",
        granularity="per_channel",
        block_size=32,
        weight_threshold=2048,
    )
)
compressed = cto.linear_quantize_weights(mlmodel, q_config)
```

Important fields:

- `mode`: `"linear_symmetric"` or `"linear"`.
- `dtype`: `"int8"`, `"uint8"`, `"int4"`, or `"uint4"`.
- `granularity`: `"per_tensor"`, `"per_channel"`, or `"per_block"`.
- `block_size`: used for per-block quantization; if an axis is not divisible by the block size, that weight can be skipped.
- `weight_threshold`: only compress weights with more elements than this threshold; default is `2048`. Lower to `0` for a tiny smoke model, not for a production first pass.

### `OpPalettizerConfig`

Common safe start:

```python
p_config = cto.OptimizationConfig(
    global_config=cto.OpPalettizerConfig(
        mode="kmeans",
        nbits=4,
        granularity="per_tensor",
        weight_threshold=2048,
    )
)
compressed = cto.palettize_weights(mlmodel, p_config)
```

Important fields:

- `mode`: `"kmeans"`, `"uniform"`, `"unique"`, or `"custom"`.
- `nbits`: required for `"kmeans"` and `"uniform"`; valid values are `1`, `2`, `3`, `4`, `6`, and `8`. Do not set it for `"unique"` or `"custom"`.
- `lut_function`: required only for `"custom"`; create the config directly rather than from YAML/dict.
- `granularity`: `"per_tensor"` or `"per_grouped_channel"`.
- `group_size` and `channel_axis`: affect grouped-channel palettization.
- `cluster_dim`: values greater than `1` request vector palettization.
- `enable_per_channel_scale`: normalizes output channels before palettization.
- `num_kmeans_workers`: increase for large k-means jobs only after confirming CPU budget.
- `weight_threshold`: default is `2048`.

### `OpThresholdPrunerConfig`

```python
threshold_config = cto.OptimizationConfig(
    global_config=cto.OpThresholdPrunerConfig(
        threshold=1e-12,
        minimum_sparsity_percentile=0.5,
        weight_threshold=2048,
    )
)
compressed = cto.prune_weights(mlmodel, threshold_config)
```

- Sets weights with absolute value below `threshold` to zero.
- Stores sparse representation only if sparsity reaches `minimum_sparsity_percentile`.
- Use when many weights are already near zero.

### `OpMagnitudePrunerConfig`

```python
magnitude_config = cto.OptimizationConfig(
    global_config=cto.OpMagnitudePrunerConfig(
        target_sparsity=0.5,
        weight_threshold=2048,
    )
)
compressed = cto.prune_weights(mlmodel, magnitude_config)
```

Important fields:

- `target_sparsity`: fraction of smallest-magnitude weights to set to zero.
- `block_size`: enables block sparsity for supported `linear` and `conv` layers.
- `n_m_ratio`: enables `n:m` sparsity for supported `linear` and `conv` layers.
- `dim`: axis for structured pruning choices.
- `weight_threshold`: default is `2048`.

## Optional Torch optimization APIs

Only use this section when PyTorch and `coremltools.optimize.torch` import successfully. If import fails, use Core ML package compression or ask the user to install a compatible PyTorch/coremltools environment.

| Workflow | Submodule/classes | When to use |
| --- | --- | --- |
| Data-free Torch weight quantization | `coremltools.optimize.torch.quantization.PostTrainingQuantizer`, `PostTrainingQuantizerConfig` | PyTorch source model exists and you want a compressed Torch model before conversion, without calibration data. |
| Calibration or QAT quantization | `LinearQuantizer`, `LinearQuantizerConfig`, `ModuleLinearQuantizerConfig` | Need activation statistics, fake quantization, or QAT/fine-tuning. |
| Calibration layerwise quantization | `layerwise_compression.LayerwiseCompressor`, `LayerwiseCompressorConfig`, GPTQ algorithm configs | Large models where layerwise calibration is preferred. |
| Data-free Torch palettization | `palettization.PostTrainingPalettizer`, `PostTrainingPalettizerConfig` | Palettize a PyTorch model before tracing/export and Core ML conversion. |
| Calibration palettization | `palettization.SKMPalettizer`, `SKMPalettizerConfig` | Need data/loss-aware sensitive k-means palettization. |
| Fine-tuning palettization | `palettization.DKMPalettizer`, `DKMPalettizerConfig` | Need differentiable k-means palettization in a training loop. |
| Data-free or training-time pruning | `pruning.MagnitudePruner`, `MagnitudePrunerConfig`, `ModuleMagnitudePrunerConfig` | Need pruning masks/hooks and optional schedule during fine-tuning. |
| Calibration pruning | `layerwise_compression.LayerwiseCompressor`, SparseGPT algorithm configs | Need one-shot calibration-data pruning for large layers. |

Torch-side pattern:

```python
# Only after imports succeed.
from coremltools.optimize.torch.pruning import MagnitudePruner, MagnitudePrunerConfig

pruner = MagnitudePruner(torch_model, MagnitudePrunerConfig.from_dict(config_dict))
prepared_model = pruner.prepare()
# Optional: run calibration/fine-tuning loop and pruner.step() as required.
final_model = pruner.finalize(prepared_model, inplace=True)
# Then route to conversion.
```

## Joint compression ordering

- Core ML package: apply one compression type, then call another with `joint_compression=True` when intentionally compressing an already-compressed representation.
- Palettize then quantize: quantize the LUT; per-tensor quantization is the safe starting point.
- Prune then quantize: quantize non-zero values after sparse representation exists.
- Prune then palettize: palettize non-zero sparse values.
- Torch joint flows are more order-sensitive. For pruning plus quantization, prepare/apply the quantizer before the pruner, and finalize in the documented reverse/order-specific manner for that optimizer pair.

## Minimal validation snippets

Inspect targeting before compression:

```python
metadata = cto.get_weights_metadata(mlmodel, weight_threshold=2048)
for weight_name, item in metadata.items():
    print(weight_name, item.val.shape, item.child_ops)
```

Decompress for debug comparison:

```python
compressed = cto.linear_quantize_weights(mlmodel, q_config)
dense_debug = cto.decompress_weights(compressed)
compressed.save("compressed.mlpackage")
dense_debug.save("decompressed_debug.mlpackage")
```

Run the bundled smoke helper:

```bash
python sub-skills/optimize-models/scripts/optimize_coreml_smoke.py --help
python sub-skills/optimize-models/scripts/optimize_coreml_smoke.py --output smoke.mlpackage --compression linear
```
