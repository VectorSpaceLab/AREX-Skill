# PyTorch Workflows

## 1) BF16 / FP16 with TE layers

Use `torch.autocast` for BF16/FP16 compute. Keep the TE module in the dtype you want for its parameters, and call `loss.backward()` outside the autocast region.

```python
import torch
import transformer_engine.pytorch as te

layer = te.Linear(1024, 4096, params_dtype=torch.float32, device="cuda")
x = torch.randn(32, 1024, device="cuda")

with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
    y = layer(x)

loss = y.sum()
loss.backward()
```

### When to use each dtype

- `params_dtype=torch.float32` + `torch.autocast(dtype=torch.bfloat16)`:
  best default for BF16 training with FP32 master weights.
- `params_dtype=torch.float32` + `torch.autocast(dtype=torch.float16)`:
  FP16 training; use `torch.amp.GradScaler("cuda")` for the loss.
- `params_dtype=torch.bfloat16` + BF16 inputs without autocast:
  direct BF16 path when you want inputs and parameters to match exactly.

### Direct BF16 path without `torch.autocast`

```python
layer = te.Linear(1024, 4096, params_dtype=torch.bfloat16, device="cuda")
x = torch.randn(32, 1024, dtype=torch.bfloat16, device="cuda")
y = layer(x)
loss = y.sum()
loss.backward()
```

## 2) FP8 / MXFP8 / NVFP4 guarded recipe flow

Always gate low-precision recipes before construction.

```python
from transformer_engine.common.recipe import DelayedScaling, MXFP8BlockScaling, NVFP4BlockScaling
import torch
import transformer_engine.pytorch as te

ok, reason = te.is_fp8_available(return_reason=True)
if not ok:
    raise RuntimeError(reason)

recipe = DelayedScaling()
layer = te.Linear(1024, 1024, device="cuda")

with te.autocast(enabled=True, recipe=recipe):
    y = layer(torch.randn(32, 1024, device="cuda"))
loss = y.sum()
loss.backward()
```

### Recipe choices

- `DelayedScaling`: the common delayed-scaling FP8 path.
- `Float8CurrentScaling`: per-tensor current scaling.
- `MXFP8BlockScaling`: block-scaled FP8 / current-scaling family.
- `NVFP4BlockScaling`: 4-bit path for Blackwell-class hardware and supported stacks.

### Guarding rule

- Use `is_fp8_available(...)` for delayed-scaling / current-scaling FP8.
- Use `is_mxfp8_available(...)` for MXFP8.
- Use `is_fp8_block_scaling_available(...)` for FP8 block scaling.
- Use `is_nvfp4_available(...)` for NVFP4.

If a check returns `False`, keep the model on BF16/FP16 instead of forcing the recipe.

### FP8 compute rule

- Forward inside `te.autocast(...)`.
- Backward outside `te.autocast(...)`.
- Do not replace `te.autocast` with `torch.autocast` for FP8/FP4 paths.

## 3) Quantized model initialization and master weights

Use `quantized_model_init` when the model should store quantized parameters at construction time.

```python
from transformer_engine.common.recipe import DelayedScaling
import torch
import transformer_engine.pytorch as te

recipe = DelayedScaling()
with te.quantized_model_init(
    enabled=True,
    recipe=recipe,
    preserve_high_precision_init_val=True,
):
    model = te.TransformerLayer(
        hidden_size=1024,
        ffn_hidden_size=4096,
        num_attention_heads=16,
        params_dtype=torch.bfloat16,
        device="cuda",
    )
```

### Selection notes

- Use `preserve_high_precision_init_val=True` when FP32 master weights must be seeded from the original initializer.
- Clear the preserved CPU values after the optimizer has consumed them.
- This is the preferred pattern for FP8 training with master weights and for meta-device / FSDP-style initialization flows.

## 4) Validation workflow

Recommended smoke and sanity sequence:

```bash
python scripts/pytorch_bf16_smoke.py --help
python scripts/pytorch_bf16_smoke.py --device cuda --in-features 16 --out-features 32 --batch-size 4
```

Expected output:

- Torch and CUDA version facts.
- Current device name and compute capability.
- BF16 availability reported as true.
- FP8 / MXFP8 / NVFP4 availability reported with either true or an explanation string.
- A tiny BF16 `Linear` forward/backward pass with a printed output shape.

If this passes, you have a reliable import and BF16 baseline before moving on to larger `LayerNormLinear`, `GroupedLinear`, or `TransformerLayer` flows.
