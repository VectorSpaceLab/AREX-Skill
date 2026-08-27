# JAX Troubleshooting

Use this guide when a `transformer_engine.jax` or `transformer_engine.jax.flax` workflow fails. Start with the bundled synthetic smoke before dataset examples.

```bash
python skills/disco/transformer-engine/sub-skills/jax/scripts/jax_bf16_smoke.py --device cuda
```

If running from this sub-skill directory:

```bash
python scripts/jax_bf16_smoke.py --device cuda
```

## Quick triage table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'jax'` | Current Python environment does not have JAX installed. | Use the target runtime environment that contains JAX/JAXLIB and Transformer Engine JAX support. Then run the import-only check. |
| `ImportError`, undefined symbol, or failure while importing `transformer_engine.jax` | TE JAX extension was not built/installed for the active Python, CUDA, or JAX/JAXLIB stack. | Import `jax` first; verify `jax.__version__` and `jaxlib.__version__`; reinstall/build Transformer Engine with JAX support for the same Python/CUDA stack. |
| CUDA/cuDNN/cuBLASLt version assertion when entering `te.autocast(enabled=True, recipe=...)` | Recipe hardware/software gate failed. | Query `get_supported_quantization_recipes()` and fall back to BF16 if the desired recipe is absent. |
| BF16 DenseGeneral works but FP8 recipe list is empty | Expected on A100-class compute capability 8.0. | Do not force `DelayedScaling`, `Float8CurrentScaling`, MXFP8, or NVFP4. Keep the path BF16/FP16. |
| OOM before the first model step or during import/JIT warmup | JAX/XLA preallocated most GPU memory, or another framework/process already holds memory. | Set `XLA_PYTHON_CLIENT_PREALLOCATE=false` before importing JAX. Optionally set `XLA_PYTHON_CLIENT_MEM_FRACTION` to a bounded value. |
| `score_mod requires fused attention` | `score_mod` was requested while `NVTE_FUSED_ATTN=0`. | Set `NVTE_FUSED_ATTN=1` before process start or remove `score_mod`. |
| `score_mod requires fused attention, but no fused attention kernel is available` | Shape/dtype/layout/GPU/cuDNN combination has no eligible fused-attention kernel. | Reduce to a supported shape/layout, remove `score_mod`, or use unfused attention without score modification. |
| Fused attention warning and performance lower than expected | TE fell back to JAX-native unfused attention. | Check `NVTE_FUSED_ATTN`, dtype, mask/bias/layout, sequence length, GPU architecture, and cuDNN version. |
| CUDA uninitialize/custom-call initialization errors | TE custom calls ran before JAX initialized CUDA. | Import `jax` first and create a trivial JAX value before TE-specific custom-call probes in diagnostic scripts. |
| Process abort around cuBLAS/cuBLASLt handle creation | Version mismatch, memory pressure, stale CUDA context, or custom-call backend issue. | Disable XLA preallocation, reduce shapes, run a fresh process, confirm CUDA/cuBLASLt compatibility, and isolate with `NVTE_JAX_CUSTOM_CALLS` if needed. |
| Dataset download/import failures in MNIST/encoder-style workflows | Optional dataset stack (`tfds`, tokenizers, network access) is unrelated to TE kernel validity. | Use synthetic smoke tests first; treat dataset-backed validation as optional and task-specific after kernel/API checks pass. |

## Import and version checks

Always import `jax` before `transformer_engine.jax` in new scripts:

```bash
python - <<'PY'
import jax
print("jax", jax.__version__)
try:
    import jaxlib
    print("jaxlib", jaxlib.__version__)
except Exception as exc:
    print("jaxlib import failed", type(exc).__name__, exc)

import transformer_engine.jax as te
import transformer_engine.jax.flax as te_flax
print("te", te.__all__)
print("te_flax", te_flax.__all__)
PY
```

If `jax` import fails, the current shell is not the TE JAX runtime. If `jax` imports but `transformer_engine.jax` fails, the active TE installation likely lacks JAX support or was compiled against incompatible CUDA/JAX components.

## JAX/JAXLIB/CUDA/cuDNN mismatch

Transformer Engine JAX loads a compiled framework extension. All of these must be mutually compatible:

- Python ABI and package environment.
- `jax` and `jaxlib` versions.
- CUDA runtime and driver versions used by JAXLIB.
- TE's compiled JAX extension and linked CUDA/cuDNN/cuBLASLt libraries.
- GPU architecture required by the selected kernels or recipes.

Common recovery steps:

1. Start a fresh process; do not rely on a partially failed Python session.
2. Import `jax` first and print visible devices.
3. Import `transformer_engine.jax` and `transformer_engine.jax.flax`.
4. Run the BF16 smoke script before any FP8 recipe.
5. Only then test low-precision recipes with support guards.

## XLA preallocation and OOM

JAX often preallocates GPU memory. That can cause TE initialization, cuBLASLt handle creation, or unrelated framework imports to fail even for small models.

Set memory controls before importing JAX:

```bash
export XLA_PYTHON_CLIENT_PREALLOCATE=false
# Optional bounded pool; tune for the workload.
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.5
python train_or_smoke.py
```

The bundled smoke script sets `XLA_PYTHON_CLIENT_PREALLOCATE=false` automatically if the variable is absent, then imports JAX.

## FP8/MXFP8/NVFP4 support gates

Use runtime guards rather than hardware assumptions:

```python
from transformer_engine.jax.quantize import (
    ScalingMode,
    get_supported_quantization_recipes,
    is_scaling_mode_supported,
)

print([type(r).__name__ for r in get_supported_quantization_recipes()])
for mode in [
    ScalingMode.DELAYED_TENSOR_SCALING,
    ScalingMode.CURRENT_TENSOR_SCALING,
    ScalingMode.MXFP8_1D_SCALING,
    ScalingMode.NVFP4_1D_SCALING,
]:
    ok, reason = is_scaling_mode_supported(mode)
    print(mode.name, ok, reason)
```

Gate summary:

- Delayed/current tensor FP8: compute capability 8.9 or newer plus compatible CUDA/cuBLASLt.
- MXFP8: Blackwell-class path guarded by compute capability 9.9 or newer plus CUDA/cuBLASLt 12.8 or newer and a sufficiently new JAX.
- NVFP4: compute capability 10.0 or newer plus CUDA/cuBLASLt 12.8 or newer and a sufficiently new JAX.
- A100 BF16 success does not imply any FP8 recipe support.

If `te.autocast(enabled=True, recipe=...)` raises an assertion, surface the guard reason and continue with BF16/FP16 unless the task explicitly requires that low-precision format.

## Autocast and missing quantization metadata

In JAX, initialize TE modules inside `te.autocast(enabled=True, recipe=...)`. If a model is initialized outside autocast and only applied inside it, the variable tree may lack `fp8_metas` or other collections needed by the recipe.

Correct structure:

```python
with te.autocast(enabled=True, recipe=recipe, mesh_resource=te.MeshResource()):
    model = te_flax.TransformerLayer(...)
    variables = model.init(rngs, x, deterministic=True)
```

Then keep the non-param variable collections (`fp8_metas`, `_overwrite_with_gradient`, or other TE state) across train and eval steps. Do not put those collections into the optimizer as model parameters.

## Fused attention fallback and score modification

Normal `DotProductAttention` behavior:

- `NVTE_FUSED_ATTN=1` by default.
- TE attempts a cuDNN fused-attention kernel.
- If no eligible fused kernel exists, TE can warn and fall back to JAX-native unfused attention.

`score_mod` behavior:

- `score_mod` and `score_mod_bprop` require fused attention.
- If fused attention is disabled, TE raises `ValueError`.
- If no fused kernel is available, TE raises `ValueError`.
- cuDNN Python frontend support and version matching may be required for score-modified attention.
- Softcap-style score modification can have stricter GPU architecture requirements than plain BF16 attention.

Debug controls must be set before importing JAX/TE:

```bash
# Force unfused attention for diagnosis. Do not use with score_mod.
export NVTE_FUSED_ATTN=0

# Prefer deterministic kernels when available.
export NVTE_ALLOW_NONDETERMINISTIC_ALGO=0
```

## `NVTE_JAX_CUSTOM_CALLS`

`NVTE_JAX_CUSTOM_CALLS` controls TE JAX custom-call primitive dispatch. Use it only for diagnosis because disabling custom calls can change performance and coverage.

```bash
# Disable all TE JAX custom calls for isolation.
export NVTE_JAX_CUSTOM_CALLS="false"
python train_or_smoke.py

# Disable only selected primitives.
export NVTE_JAX_CUSTOM_CALLS="GemmPrimitive=false,DBiasQuantizePrimitive=false"
python train_or_smoke.py
```

If disabling a primitive makes a crash disappear, keep the exact primitive name and minimal reproducer for debugging. Do not present the disabled-custom-call run as a performance-valid TE result.

## cuBLASLt handle aborts

A process abort or fatal CUDA error around GEMM setup/handle creation is usually not recoverable inside the same Python process. Use a fresh process and a smaller synthetic case.

Recommended sequence:

1. Set `XLA_PYTHON_CLIENT_PREALLOCATE=false` before import.
2. Run the import-only check.
3. Run `jax_bf16_smoke.py` with tiny shapes.
4. If BF16 works, probe recipe support separately.
5. If only quantized GEMMs abort, report the exact recipe, shape, dtype, GPU model/compute capability, JAX/JAXLIB versions, and CUDA/cuBLASLt versions available from the runtime.
6. If a custom-call-specific failure is suspected, rerun with `NVTE_JAX_CUSTOM_CALLS="GemmPrimitive=false"` to isolate, but do not use that as the final TE performance configuration.

## Dataset examples are not default validation

The MNIST and encoder examples require optional dataset/download/tokenization dependencies and can fail for reasons unrelated to Transformer Engine JAX kernels. Use synthetic checks first:

1. Import-only check.
2. BF16 DenseGeneral forward/gradient smoke.
3. Optional BF16 `TransformerLayer` tiny forward.
4. Recipe support probe.
5. Only then add dataset-backed validation if the project specifically needs end-to-end data loading coverage.
