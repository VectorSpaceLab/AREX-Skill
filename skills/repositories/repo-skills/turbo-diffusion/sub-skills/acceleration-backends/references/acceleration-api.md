# Acceleration API and option semantics

This reference explains the backend-facing APIs and runtime flags that decide TurboDiffusion's acceleration behavior. For end-user command construction, route to the appropriate inference, serving, or checkpoint sub-skill.

## Import surfaces

Prefer fully qualified imports in reusable code:

```python
from turbodiffusion.ops import Int8Linear, FastRMSNorm, FastLayerNorm
from turbodiffusion.SLA import SparseLinearAttention, SageSparseLinearAttention
```

Some source-authored scripts import top-level names (`ops`, `SLA`, `rcm`, `imaginaire`, `serve`, `modify_model`). When using those scripts from a source checkout, apply the source-layout `PYTHONPATH` rule in [backend-build.md](backend-build.md#source-layout-import-quirk).

## Custom-op modules

| API | Backend dependency | Meaning | Notes |
| --- | --- | --- | --- |
| `int8_quant(x)` | `turbo_diffusion_ops`, CUDA | Quantizes a floating tensor to INT8 plus per-block scales | Used by `Int8Linear`; input should be CUDA float16/bfloat16-like activation or weight data. |
| `int8_linear(x, w_q, w_s)` | `turbo_diffusion_ops`, CUDA | Quantizes activation then runs custom INT8 GEMM against quantized weights | Requires `w_q.dtype == torch.int8`. |
| `Int8Linear.from_linear(linear, quantize=True)` | `turbo_diffusion_ops`, CUDA when quantizing | Replaces a `torch.nn.Linear` with stored INT8 weight and scale buffers | `quantize=False` creates the target module shape without quantizing, useful before loading a quantized checkpoint state dict. |
| `FastRMSNorm.from_rmsnorm(rmsnorm)` | Triton/CUDA for forward | Converts Wan RMSNorm into fast RMSNorm | Stores weight as a buffer and computes through Triton. |
| `FastLayerNorm.from_layernorm(layernorm)` | Triton/CUDA for forward | Converts Wan LayerNorm into fast LayerNorm | Preserves affine/bias configuration when present. |

The INT8 and FastNorm modules are small building blocks. They are not model checkpoints and do not download assets.

## SLA modules

| API | Backend dependency | Meaning | Failure mode |
| --- | --- | --- | --- |
| `SparseLinearAttention(head_dim, topk, ...)` | CUDA/Triton SLA kernels | Plain sparse-linear attention path | Tiny random tensors can produce non-finite values and should not be treated as a full correctness proof; validate in model context when possible. |
| `SageSparseLinearAttention(head_dim, topk, ...)` | SpargeAttn package plus CUDA | SageAttention-backed fast SLA path | Constructor asserts when `SAGESLA_ENABLED` is false: `Install SpargeAttn first to enable SageSLA.` |

`SageSparseLinearAttention` detects GPU architecture internally and chooses block layouts for SM90 versus other supported architectures. Head dimension is expected to be 64 or 128 for the SageSLA kernel path.

## Runtime flag decisions

| User situation | Recommended backend choice | Why |
| --- | --- | --- |
| Quantized TurboDiffusion checkpoint name or documentation includes `-quant` | Use `--quant_linear`; require `turbo_diffusion_ops` import and CUDA custom-op smoke success | Quantized checkpoints carry INT8 Linear state expected by `Int8Linear`. |
| Unquantized checkpoint on high-memory GPU class | Do not pass `--quant_linear` | Unquantized weights should remain BF16/FP16 Linear. |
| Need fastest documented attention path and willing to install optional kernels | Use `--attention_type sagesla`; verify SpargeAttn/SageSLA first | README examples default to SageSLA after optional SpargeAttn installation. |
| SpargeAttn is missing or not approved | Use `--attention_type sla` or `original` | `sagesla` will assert without SpargeAttn. Plain `sla` remains the nearest TurboDiffusion sparse-linear fallback but still needs CUDA/Triton. |
| Debugging backend errors or comparing quality | Use `--attention_type original` | Removes SLA/SageSLA replacement from the model. |
| User wants better quality than default top-k | Consider `--sla_topk 0.15` for TurboDiffusion Wan workflows | The public README recommends 0.15 for better video quality over the default 0.1. |
| User wants original normalization layers | Add `--default_norm` | In the source logic, omitting `--default_norm` replaces Wan LayerNorm/RMSNorm with FastNorm variants. |

TurboT2AV uses related concepts but a separate backend implementation: SageSLA `topk=0.3`, FastNorm, and TileLang W8A8. Route TurboT2AV command and TileLang decisions to `turbot2av-extension` rather than reusing TurboDiffusion `quant_linear` semantics directly.

## Replacement helper behavior

TurboDiffusion's model modification logic uses three key helpers:

### `replace_attention(model, attention_type, sla_topk)`

- Accepts only `attention_type in {"sla", "sagesla"}`.
- Walks model modules and replaces Wan self-attention local attention blocks.
- For `sla`, constructs `SparseLinearAttention(head_dim=dim // num_heads, topk=sla_topk, BLKQ=128, BLKK=64)`.
- For `sagesla`, constructs `SageSparseLinearAttention(head_dim=dim // num_heads, topk=sla_topk)` and therefore requires SpargeAttn.

### `replace_linear_norm(model, replace_linear=False, replace_norm=False, quantize=True, skip_layer="proj_l")`

- Walks `model.blocks.named_modules()`.
- Replaces `torch.nn.Linear` only when `replace_linear=True`.
- Skips names containing `skip_layer` by default; this prevents quantizing the SLA projection layer named `proj_l`.
- Replaces Wan RMSNorm and LayerNorm with `FastRMSNorm` / `FastLayerNorm` only when `replace_norm=True`.
- Uses `quantize=False` to create INT8 module shells before loading a quantized state dict; uses `quantize=True` when converting a loaded model into a quantized checkpoint.

### `create_model(dit_path, args)`

- Selects a Wan architecture on the meta device.
- Loads the checkpoint state dict.
- Replaces attention first when `args.attention_type` is `sla` or `sagesla`.
- Replaces Linear and Norm modules before state-dict assignment: `replace_linear=args.quant_linear`, `replace_norm=not args.default_norm`, `quantize=False`.
- Loads the state dict with assignment semantics, moves the model to CUDA, and sets eval mode.

This means a quantized inference checkpoint and the `--quant_linear` flag must agree. If they do not, state-dict keys/shapes or runtime custom-op calls can fail.

## Safe preflight sequence for backend choices

1. Decide whether the selected checkpoint is quantized.
2. Decide `attention_type`:
   - `sagesla`: require SpargeAttn.
   - `sla`: require CUDA/Triton and treat tiny random forward as a warning-only signal.
   - `original`: no SLA module replacement.
3. Decide normalization:
   - omit `--default_norm` for FastNorm;
   - add `--default_norm` for original Wan norms.
4. Run [the diagnostic script](../scripts/check_acceleration_backend.py) with `--require-cuda` and, when needed, `--require-sagesla`.
5. Only after backend readiness is clear, route to command-building or checkpoint-conversion sub-skills.
