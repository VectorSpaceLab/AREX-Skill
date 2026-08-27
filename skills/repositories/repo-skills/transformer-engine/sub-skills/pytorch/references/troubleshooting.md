# PyTorch Troubleshooting

## 1) Import order and compile toggles

- Import `torch` before `transformer_engine.pytorch`.
- If import-time tracing or `torch.compile` interaction is unstable, set `NVTE_TORCH_COMPILE=0` **before** importing TE.
- If the import fails with a package or shared-object error, check that the installed TE metapackage and framework extension versions match.

### Symptom pattern

- `Could not find transformer_engine` / extension load failure
- import succeeds in one environment but not another
- failures only appear after `torch.compile` or graph capture is enabled

### Action

- Re-run with the smoke script's import order.
- Disable `NVTE_TORCH_COMPILE`.
- Confirm the runtime is using a matching TE install instead of an incomplete source checkout.

## 2) PyTorch version and FSDP2 support

- TE requires PyTorch 2.1 or newer.
- FSDP2-style flows that use `fully_shard` or `torch.distributed.fsdp._fully_shard` need a PyTorch build that actually provides that API.
- DCP checkpointing of quantized tensors needs the safe-serialization path that appears in newer PyTorch releases.

### Action

- If `torch.distributed.fsdp._fully_shard` is missing, use the non-FSDP path or upgrade PyTorch.
- If quantized checkpoint loading fails, verify the runtime supports `torch.serialization.add_safe_globals`.

## 3) CUDA / cuBLAS / cuDNN mismatches

When the failure mentions `cublasLtGetVersion`, handle creation, or an unavailable fused kernel, suspect a runtime library mismatch before suspecting model code.

### Good facts to log

- `get_device_compute_capability()`
- `get_cudnn_version()`
- `te.is_bf16_available(return_reason=True)`
- `te.is_fp8_available(return_reason=True)`
- `te.is_mxfp8_available(return_reason=True)`
- `te.is_nvfp4_available(return_reason=True)`

### Common mismatch signs

- cuBLASLt handle aborts or version-related crashes.
- `GroupedLinear` works in BF16 but fails when a low-precision recipe is enabled.
- Attention or grouped GEMM paths fail only on a subset of GPUs.

### Action

- Compare the logged CUDA/cuBLAS/cuDNN versions with the recipe you are trying to use.
- Re-test with the smallest BF16 `Linear` smoke before retrying larger blocks.

## 4) Precision availability and hardware gates

### Do not force unsupported recipes

- A100-class hardware should use BF16/FP16 paths, not FP8/MXFP8/NVFP4.
- Use the specific availability function for the precision you want.
- If the availability check returns false, respect the reason string and switch to a supported precision.

### Typical gate failures

- FP8 recipe requested on a GPU that only supports BF16/FP16.
- MXFP8 or NVFP4 requested on a stack that lacks the required cuBLAS or hardware support.
- FP8 block scaling requested without the needed cuBLAS support level.

### Action

- Keep a BF16 or FP16 fallback path in every script.
- Do not treat "unsupported" as a transient warning.

## 5) Shape, memory, and preallocation issues

- Some FP8 linear paths expect dimensions aligned to 16.
- Large models can OOM during construction if you instantiate full-precision weights first.
- `quantized_model_init(enabled=True)` exists to avoid holding both high-precision and quantized copies when you do not need them.

### Action

- Reduce to the bundled BF16 smoke shape first.
- Use `quantized_model_init` and, for large sharded setups, meta-device initialization plus sharding.
- Preserve high-precision init values only when you actually need them for optimizer master weights.

## 6) Full TransformerLayer vs tiny smoke

The bundled smoke uses `te.Linear` on purpose.

### Why

- It verifies import, BF16 kernels, and backward flow with minimal moving parts.
- Full `TransformerLayer` examples are more sensitive to mixed CUDA/cuBLAS/cuDNN stacks and to distributed configuration.

### Action

- If the smoke passes but a full block fails, investigate the larger block's recipe, topology, and overlap settings before changing the smoke.
- Reintroduce `LayerNormLinear`, `GroupedLinear`, attention, or sharding only after the baseline is stable.
