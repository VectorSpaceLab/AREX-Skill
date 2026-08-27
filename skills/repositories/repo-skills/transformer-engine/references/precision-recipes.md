# Precision recipes and hardware compatibility

Read this reference when the task is about BF16/FP16 versus FP8/MXFP8/NVFP4 selection, recipe availability, or a GPU capability question that is not tied to a single framework.

## Shared facts

- BF16/FP16 are the safe baseline for Ampere and newer GPUs.
- A100/SM80 can validate BF16/FP16 TE paths, but it should be treated as unsupported for FP8, MXFP8, and NVFP4 runtime claims.
- FP8 delayed/current scaling requires compute capability 8.9 or newer.
- FP8 block scaling requires compute capability 9.0 or newer and a sufficiently new CUDA/cuBLASLt stack.
- MXFP8 is Blackwell-class in practice; NVFP4 is Blackwell-class and newer.
- JAX support probes can return an empty recipe list on A100 even when BF16 dense paths work.

## Recipe families

| Recipe or format | Where it appears | Practical use |
| --- | --- | --- |
| `Format` | `transformer_engine.common.recipe` | Low-level format enum used by all recipe classes. |
| `DelayedScaling` | PyTorch and JAX FP8 workflows | Classic tensor-FP8 delayed scaling. Gate by FP8 availability first. |
| `Float8CurrentScaling` | PyTorch and JAX FP8 workflows | Tensor-FP8 current scaling. Also gate by FP8 availability. |
| `Float8BlockScaling` | PyTorch and JAX block-scaling workflows | Block-scaled FP8 variant. Requires stronger hardware/software support than plain BF16. |
| `MXFP8BlockScaling` | Blackwell-class workflows | Block-scaled FP8 for Blackwell-era hardware. |
| `NVFP4BlockScaling` | Blackwell-class workflows | 4-bit recipe family for Blackwell-era hardware. |
| `CustomRecipe` | Advanced users | User-defined quantization or expert routing recipe. |

## Runtime support probes

Use the support probe that matches the framework you are using.

### PyTorch

- `transformer_engine.pytorch.is_bf16_available(return_reason=True)`
- `transformer_engine.pytorch.is_fp8_available(return_reason=True)`
- `transformer_engine.pytorch.is_mxfp8_available(return_reason=True)`
- `transformer_engine.pytorch.is_fp8_block_scaling_available(return_reason=True)`
- `transformer_engine.pytorch.is_nvfp4_available(return_reason=True)`
- `transformer_engine.pytorch.get_device_compute_capability()`
- `transformer_engine.pytorch.get_cudnn_version()`

### JAX

- `transformer_engine.jax.quantize.get_supported_quantization_recipes()`
- `transformer_engine.jax.quantize.is_scaling_mode_supported(...)`

## Selection guidance

1. If the task only needs BF16 or FP16, keep the model in BF16/FP16 and use the framework's ordinary precision control.
2. If the task asks for FP8 or lower, call the support probe before constructing the module or recipe.
3. If the support probe is false, keep a BF16/FP16 fallback path and surface the reason string.
4. Do not infer recipe availability from model shape alone.
5. If a process is a mixed PyTorch/JAX environment, use the framework-specific sub-skill for the code path you are actually modifying.

## Framework-specific precision rules

### PyTorch

- Use `torch.autocast(device_type="cuda", dtype=torch.bfloat16)` for BF16/FP16 compute.
- Use `transformer_engine.pytorch.autocast(...)` for FP8/MXFP8/NVFP4 compute recipes.
- Keep `.backward()` outside the TE autocast block.

### JAX

- Initialize TE modules inside `transformer_engine.jax.autocast(enabled=True, recipe=...)` when quantization metadata is required.
- Keep the non-param Flax collections produced by TE across train and eval steps.
- Import `jax` before `transformer_engine.jax` in smoke scripts and standalone programs.

## Useful runtime checker

Run the bundled runtime inspector for a quick cross-framework summary:

```bash
python scripts/inspect_transformer_engine_runtime.py --framework both
```

The output should include the installed package versions, CUDA device facts, and support-fact lines for the selected framework path.
