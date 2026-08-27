# Direct Module and Functional Workflows

These recipes are for direct PyTorch/bitsandbytes use. They avoid Hugging Face `BitsAndBytesConfig`; route those tasks to `transformers-integrations`.

## Replace a linear layer directly

Use the same dimensions and bias setting as the source `torch.nn.Linear`, copy/load floating-point weights, then move the quantized layer to the target device.

```python
import torch
import bitsandbytes as bnb

src = torch.nn.Linear(128, 64, bias=True, dtype=torch.float16)
q = bnb.nn.Linear8bitLt(
    src.in_features,
    src.out_features,
    bias=src.bias is not None,
    has_fp16_weights=False,
    threshold=0.0,
)
q.load_state_dict(src.state_dict(), strict=False)
q = q.to("cuda")  # quantization happens here for CUDA workflows
```

For 4-bit/NF4:

```python
q4 = bnb.nn.LinearNF4(
    src.in_features,
    src.out_features,
    bias=src.bias is not None,
    compute_dtype=torch.bfloat16,
    compress_statistics=True,
    quant_storage=torch.uint8,
)
q4.load_state_dict(src.state_dict(), strict=False)
q4 = q4.to("cuda")  # creates packed weight and quant_state
```

Key lifecycle rule: construction alone does not prove a quantized forward will work. The module quantizes its weight when moved to the target device. Forgetting `.to(device)` is the most common direct-use mistake.

## Load quantized checkpoints safely

`Linear8bitLt` checkpoints can contain quantized fields such as `weight.CB` and `weight.SCB`. A fresh module that has not been quantized yet may reject those fields or report an `SCB` mismatch.

Recommended sequence when the checkpoint is already quantized:

1. Instantiate the same bitsandbytes module class with matching dimensions and flags.
2. Move it to the same kind of target device used for quantized inference/training.
3. Load the quantized state dict after the module has initialized its quantized parameter state.
4. If the checkpoint was saved before quantization, load first and then call `.to(device)`.

When in doubt, inspect state dict keys:

```python
keys = list(state_dict)
quantized_int8 = any(key.endswith((".SCB", ".CB")) or ".SCB" in key or ".CB" in key for key in keys)
quantized_4bit = any("quant_state" in key or "bitsandbytes__" in key for key in keys)
```

If `quantized_int8` is true, do not load it into a plain `torch.nn.Linear`; use `Linear8bitLt`. If `quantized_4bit` is true, preserve both packed weight and quantization metadata.

## Use 4-bit functional primitives

```python
import torch
import bitsandbytes.functional as F

x = torch.randn(256, dtype=torch.float16, device="cuda")
packed, state = F.quantize_4bit(
    x,
    blocksize=64,
    quant_type="nf4",
    compress_statistics=True,
    quant_storage=torch.uint8,
)
roundtrip = F.dequantize_4bit(packed, state)
```

Practical rules:

- Use `quant_type="nf4"` for normally distributed neural weights; use `fp4` when matching FP4-specific checkpoints or experiments.
- Use a supported blocksize. The lower-level registered op accepts `32, 64, 128, 256, 512, 1024, 2048, 4096`.
- Keep `packed` and `state` together. The state records shape, dtype, blocksize, code, absmax statistics, and nested statistics.
- Do not mix devices: packed tensors, `QuantState` tensors, inputs, and output buffers should be on compatible devices.

## Use `matmul_4bit`

```python
import torch
import bitsandbytes as bnb
import bitsandbytes.functional as F

A = torch.randn(8, 128, dtype=torch.float16, device="cuda")
B = torch.randn(64, 128, dtype=torch.float16, device="cuda")
Bq, qstate = F.quantize_4bit(B, blocksize=64, quant_type="nf4")
out = bnb.matmul_4bit(A, Bq.t(), qstate)
```

The packed weight orientation must match the matmul call used by the target code. If adapting from a module, prefer using the module forward unless a custom kernel path is truly needed.

## Use int8 vectorwise primitives

```python
import torch
import bitsandbytes.functional as F

A = torch.randn(16, 128, dtype=torch.float16, device="cuda")
A8, row_stats, outlier_cols = F.int8_vectorwise_quant(A, threshold=0.0)
A_dequant = F.int8_vectorwise_dequant(A8, row_stats)
```

With `threshold > 0`, values above the threshold can be tracked through `outlier_cols`. This is part of the LLM.int8 outlier path and should not be confused with 4-bit `quant_type` selection.

## Use blockwise quantization

```python
import torch
import bitsandbytes.functional as F

x = torch.randn(8192, device="cuda")
qx, qstate = F.quantize_blockwise(x, blocksize=4096, nested=True)
y = F.dequantize_blockwise(qx, qstate)
```

Use blockwise APIs for custom quantization experiments where 4-bit packing is not the desired format. CPU paths are useful for tiny checks with default/larger block sizes; small non-default CPU block sizes may be slow or unavailable depending on backend.

## Embedding layers

For direct embedding replacement, keep `num_embeddings` and `embedding_dim` identical to the source embedding. With 4-bit embeddings, choose an embedding dimension and storage dtype supported by the active backend. Tests exercise warning/error behavior for unsupported embedding dimensions and storage combinations, so do not silence divisibility/storage warnings without changing the model shape or backend.

```python
emb = bnb.nn.EmbeddingNF4(num_embeddings=32000, embedding_dim=128, quant_storage=torch.uint8)
emb = emb.to("cuda")
```

## State dict and FSDP caveats

- For 8-bit modules, `Int8Params` may carry `CB` and `SCB`. Save/load code must preserve these fields for quantized checkpoints.
- For 4-bit modules, `Params4bit` owns/proxies `QuantState`; packed state dict keys can include `quant_state` and `bitsandbytes__<type>` metadata.
- If FSDP or sharding code traverses a 4-bit parameter, preserve the proxied `QuantState` attributes and use a `quant_storage` dtype supported by the backend/sharding path.
- If a state dict loses `quant_state`, recreate it by re-quantizing from original floating weights; do not guess `absmax`, `code`, or nested statistics.

## CPU-safe inspection workflow

When an agent or CI runner only needs to prove imports, signatures, and module construction, run:

```bash
python scripts/quantized-module-smoke.py
```

This default path constructs modules on CPU and inspects signatures without calling quantized forwards or native GPU kernels. Use `--device cuda --run-forward` only in an environment where the target backend is installed and expected to execute quantized kernels.
