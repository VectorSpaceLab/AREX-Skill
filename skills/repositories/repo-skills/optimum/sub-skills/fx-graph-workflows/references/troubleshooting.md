# FX graph workflow troubleshooting

Use this guide when Optimum FX transformations, GraphModule validation, reversible chains, or optional tensor-parallel imports fail.

## Missing or incompatible imports

### `ModuleNotFoundError: No module named 'torch'`

Optimum FX transformations require PyTorch. Install a CPU PyTorch build for graph-optimization work. CUDA is not required for `optimum.fx.optimization` smoke tests.

Quick check:

```python
import torch
from optimum.fx.optimization import ChangeTrueDivToMulByInverse
```

### Transformers FX support is unavailable

If Transformers-based symbolic tracing fails, check:

```python
from optimum.fx.utils import are_fx_features_available
print(are_fx_features_available())
```

Optimum's FX utilities gate on a Transformers version with the required FX features. Upgrade Transformers if the gate is false. For simple local modules, use `torch.fx.symbolic_trace` and the bundled smoke script to separate package health from Transformers model tracing.

### `optimum.fx.parallelization` import fails on Python 3.11

Observed symptom:

```text
ValueError: mutable default <class 'slice'> for field index is not allowed: use default_factory
```

Cause: Python 3.11 dataclass validation rejects the `slice(...)` default used by the tensor-parallel `ParameterSlice` dataclass in this inspected version. The repository tensor-parallel workflow used Python 3.10.

Recovery:

1. Do not edit installed package files as part of a user task.
2. Use a Python 3.10 environment for tensor-parallel work, or refresh this generated skill after an upstream fix.
3. Keep CPU FX optimization work separate; `optimum.fx.optimization` can still be usable even when `optimum.fx.parallelization` cannot import.

## GraphModule and transformation failures

### Raw `torch.nn.Module` passed to a transformation

Symptom: attribute errors involving `.graph`, `.recompile`, or FX node fields.

Recovery:

```python
model.eval()
traced = torch.fx.symbolic_trace(model)
transformed = ChangeTrueDivToMulByInverse()(traced)
```

For Transformers models, use a compatible Transformers FX tracer and explicit input names when the model forward signature needs them.

### Graph does not lint or compiled code is stale

Causes:

- `lint_and_recompile=False` was used and no later lint/recompile was run.
- A custom transformation erased a node still used by another node.
- A custom transformation changed `node.args` or module attributes inconsistently.

Recovery:

```python
graph_module.graph.lint()
graph_module.recompile()
```

When composing transformations, let the outer transformation call perform lint/recompile, or call it manually once at the end.

### `reverse=True` fails or does not restore the graph

Common causes:

- Reverse was called with a different transformation object whose signature does not match node markers.
- The graph was modified between forward and reverse calls, losing marker metadata or stored node attributes.
- A one-way `Transformation` was included in a composed chain, so the composition is not reversible.
- Reverse was called on an untransformed graph.

Recovery:

- Keep and reuse the same transformation or composed object.
- Confirm every transformation in a chain subclasses `ReversibleTransformation` before relying on `reverse=True`.
- For `MergeLinears`, do not remove the merged node attributes needed to reconstruct original linears.
- For `FuseBiasInLinear`, do not erase inserted concat/ones nodes before reverse.

### Computation-preserving assertion fails

Checklist:

- Was the model in `eval()` before tracing? BatchNorm fusion expects stable running statistics.
- Are input tensors identical for original, transformed, and restored calls?
- Are random seeds fixed and dropout disabled?
- Are tolerances appropriate for dtype and fused arithmetic? Start with `rtol=1e-4`, `atol=1e-5` for float32 inference smoke checks.
- Is the transformation actually declared `preserves_computation=True`?
- Did a denominator in `ChangeTrueDivToMulByInverse` become dynamic? That transform only rewrites static denominator nodes.
- Did a BatchNorm fusion skip because the Conv/Linear output had multiple users or feature dimensions did not align?

### BatchNorm fusion does nothing

This can be expected. The fusion transforms are conservative:

- `FuseBatchNorm2dInConv2d` only fuses `Conv2d -> BatchNorm2d` when the conv output has no other users.
- `FuseBatchNorm1dInLinear` only fuses supported `Linear -> BatchNorm1d` or `BatchNorm1d -> Linear` shapes when the producer output has no unsafe fanout.
- Training-mode behavior is not the target; use `eval()`.

## Native/source test pitfalls

### Tiny model tests download from the Hub

Some native FX transformation tests instantiate tiny Transformers models by model identifier. That can download configs, tokenizers, or weights unless everything is already cached. For required local validation, use:

```bash
python scripts/fx_transform_smoke.py
```

Run native model tests only when the task explicitly allows model cache/network use.

### Tensor-parallel native tests require more than an import

The tensor-parallel tests use CUDA, `torch.compile`, distributed process spawning, process groups, model identifiers, and multiple world sizes. Do not treat them as CPU smoke tests.

## Tensor-parallel runtime failures

### No CUDA, NCCL, or distributed process group

Symptoms may include failures from `torch.distributed`, unavailable CUDA devices, or attempts to construct `ParallelExecutionCtx` without a valid `tp_group`.

Recovery:

- Use CUDA-capable PyTorch and GPUs.
- Initialize `torch.distributed` per rank before creating the tensor-parallel group.
- Prefer NCCL for CUDA distributed execution.
- Assign `current_device` to the rank-local CUDA device.

### `torch.compile` unavailable or too old

Native tests require PyTorch `>= 2.3.0` for `torch.compile` tensor-parallel execution. Upgrade PyTorch in a compatible CUDA environment before running the automatic parallelism workflow.

### Dimension not divisible by world size

Layer replacements require divisible dimensions:

- `ColumnParallelLinear`: `out_features % world_size == 0`.
- `RowParallelLinear`: `in_features % world_size == 0`.
- `VocabParallelEmbedding`: `num_embeddings % world_size == 0`.

Use a smaller tensor-parallel group, a model with compatible dimensions, or a custom strategy outside this generated skill.

### `parallelize_model` tries to download files

`parallelize_model` accepts model identifiers and may fetch config/weights. To avoid network access:

```python
model = parallelize_model(
    local_model_dir,
    ctx,
    local_files_only=True,
    skip_load_weights=True,  # dry runs only
)
```

Use a local model directory when downloads are not allowed. Do not use `skip_load_weights=True` as proof of full weight-loading correctness.

## Routing mistakes

- GPTQ quantization, `GPTQQuantizer`, `load_quantized_model`, and `gptqmodel` issues belong to `gptq-quantization`.
- `optimum-cli export`, `TasksManager`, exporter backend registration, and accelerated pipeline dispatcher issues belong to `exporters-and-cli`.
- `DummyInputGenerator`, `NormalizedConfig`, preprocessing task processors, and base config serialization belong to `utilities-and-configs`.
