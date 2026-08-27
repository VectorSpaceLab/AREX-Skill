# Direct Quantized API Reference

This reference covers direct `bitsandbytes` module and functional APIs for custom PyTorch code. Signatures were verified from the installed package API snapshot and cross-checked against source/tests for behavior notes.

## Module constructors

| API | Verified signature | Use | Notes |
| --- | --- | --- | --- |
| `bitsandbytes.nn.Linear8bitLt` | `(input_features: int, output_features: int, bias=True, has_fp16_weights=True, threshold=0.0, index=None, device=None)` | LLM.int8 linear layer | Load floating-point weights first, then call `.to(device)` to quantize. `threshold` enables outlier routing; `has_fp16_weights=False` stores only quantized weights after quantization. |
| `bitsandbytes.nn.Linear4bit` | `(input_features, output_features, bias=True, compute_dtype=None, compress_statistics=True, quant_type='fp4', quant_storage=torch.uint8, device=None)` | Base 4-bit linear layer | Load fp16/bf16/fp32 weights first, then call `.to(device)` to create packed 4-bit weights and `quant_state`. `quant_type` is usually `fp4` or `nf4`. |
| `bitsandbytes.nn.LinearNF4` | `(input_features, output_features, bias=True, compute_dtype=None, compress_statistics=True, quant_storage=torch.uint8, device=None)` | NF4-specialized 4-bit linear | Same lifecycle as `Linear4bit` with `quant_type='nf4'`; common for QLoRA-style research modules. |
| `bitsandbytes.nn.LinearFP4` | `(input_features, output_features, bias=True, compute_dtype=None, compress_statistics=True, quant_storage=torch.uint8, device=None)` | FP4-specialized 4-bit linear | Same lifecycle as `Linear4bit` with `quant_type='fp4'`. |
| `bitsandbytes.nn.Embedding8bit` | `(num_embeddings, embedding_dim, device=None, dtype=None)` | 8-bit embedding | Construct and move to the target device before relying on quantized forward behavior. |
| `bitsandbytes.nn.Embedding4bit` | `(num_embeddings, embedding_dim, dtype=None, quant_type='fp4', quant_storage=torch.uint8, device=None)` | Base 4-bit embedding | `embedding_dim` should be divisible by the packing factor used by the backend; tests cover warning/error paths for incompatible shapes. |
| `bitsandbytes.nn.EmbeddingNF4` | `(num_embeddings, embedding_dim, dtype=None, quant_storage=torch.uint8, device=None)` | NF4 4-bit embedding | Same caveats as `Embedding4bit`; select backend-supported `quant_storage`. |
| `bitsandbytes.nn.EmbeddingFP4` | `(num_embeddings, embedding_dim, dtype=None, quant_storage=torch.uint8, device=None)` | FP4 4-bit embedding | Same caveats as `Embedding4bit`. |
| `bitsandbytes.nn.Params4bit` | `(data: Optional[torch.Tensor] = None, requires_grad=False, quant_state: Optional[bitsandbytes.functional.QuantState] = None, blocksize: Optional[int] = None, compress_statistics: bool = True, quant_type: str = 'fp4', quant_storage: torch.dtype = torch.uint8, module: Optional[ForwardRef('Linear4bit')] = None, bnb_quantized: bool = False, **kwargs) -> 'Params4bit'` | Parameter wrapper for 4-bit module weights | Owns/proxies `quant_state` metadata after quantization and is important for state dict and FSDP traversal. |
| `bitsandbytes.nn.Int8Params` | `(data: Optional[torch.Tensor] = None, requires_grad=True, has_fp16_weights=False, CB: Optional[torch.Tensor] = None, SCB: Optional[torch.Tensor] = None, **kwargs)` | Parameter wrapper for int8 module weights | `CB` and `SCB` are quantized weight/statistics fields; loading them into an unquantized module causes common checkpoint errors. |

## Functional and matmul APIs

| API | Verified signature | Return | Notes |
| --- | --- | --- | --- |
| `bitsandbytes.matmul` | `(A: torch.Tensor, B: torch.Tensor, out: Optional[torch.Tensor] = None, state: Optional[bitsandbytes.autograd._functions.MatmulLtState] = None, threshold=0.0, bias: Optional[torch.Tensor] = None)` | Tensor | Autograd helper for int8 matmul. Pass a `MatmulLtState` when managing cached quantized state. `threshold` controls outlier handling. |
| `bitsandbytes.matmul_4bit` | `(A: torch.Tensor, B: torch.Tensor, quant_state: bitsandbytes.functional.QuantState, out: Optional[torch.Tensor] = None, bias: Optional[torch.Tensor] = None)` | Tensor | Requires packed 4-bit weight tensor plus the matching `QuantState`. Losing or mismatching `quant_state` invalidates the result. |
| `bitsandbytes.autograd._functions.MatmulLtState` | `(force_no_igemmlt: bool = False, CB: Optional[torch.Tensor] = None, SB: Optional[torch.Tensor] = None, SCB: Optional[torch.Tensor] = None, SBt: Optional[torch.Tensor] = None, CBt: Optional[torch.Tensor] = None, subB: Optional[torch.Tensor] = None, outlier_pool: Optional[bitsandbytes.autograd._functions.GlobalOutlierPooler] = None, idx: Optional[torch.Tensor] = None) -> None` | State object | Caches int8 transformed weights/statistics and optional outlier data. |
| `bitsandbytes.functional.QuantState` | `(absmax, shape=None, code=None, blocksize=None, quant_type=None, dtype=None, offset=None, state2=None)` | State object | Stores enough metadata to dequantize packed tensors: `absmax`, original `shape`, `code`, `blocksize`, `quant_type`, `dtype`, and optional nested state. |
| `bitsandbytes.functional.quantize_4bit` | `(A: torch.Tensor, absmax: Optional[torch.Tensor] = None, out: Optional[torch.Tensor] = None, blocksize=None, compress_statistics=False, quant_type='fp4', quant_storage=torch.uint8) -> tuple[torch.Tensor, bitsandbytes.functional.QuantState]` | `(packed, quant_state)` | Quantizes floating tensors to packed 4-bit storage. Source ops accept blocksizes `32, 64, 128, 256, 512, 1024, 2048, 4096`. |
| `bitsandbytes.functional.dequantize_4bit` | `(A: torch.Tensor, quant_state: Optional[bitsandbytes.functional.QuantState] = None, absmax: Optional[torch.Tensor] = None, out: Optional[torch.Tensor] = None, blocksize: Optional[int] = None, quant_type='fp4') -> torch.Tensor` | Tensor | Prefer passing the original `QuantState`. Manual `absmax`/`blocksize`/`quant_type` must match quantization exactly. |
| `bitsandbytes.functional.quantize_blockwise` | `(A: torch.Tensor, code: Optional[torch.Tensor] = None, absmax: Optional[torch.Tensor] = None, out: Optional[torch.Tensor] = None, blocksize=4096, nested=False) -> tuple[torch.Tensor, bitsandbytes.functional.QuantState]` | `(quantized, quant_state)` | Dynamic blockwise quantization. CPU tests use larger/default blocksizes; small non-default CPU blocks can be slow or unsupported. |
| `bitsandbytes.functional.dequantize_blockwise` | `(A: torch.Tensor, quant_state: Optional[bitsandbytes.functional.QuantState] = None, absmax: Optional[torch.Tensor] = None, code: Optional[torch.Tensor] = None, out: Optional[torch.Tensor] = None, blocksize: int = 4096, nested=False) -> torch.Tensor` | Tensor | Use the matching `QuantState` when available, especially with nested statistics. |
| `bitsandbytes.functional.int8_vectorwise_quant` | `(A: torch.Tensor, threshold=0.0)` | `(quantized, row_stats, outlier_cols)` | Quantizes rows to int8 and returns per-row stats plus optional outlier column indices when `threshold > 0`. |
| `bitsandbytes.functional.int8_vectorwise_dequant` | `(A: torch.Tensor, stats: torch.Tensor)` | Tensor | Dequantizes int8 rows with their row stats. |
| `bitsandbytes.functional.int8_linear_matmul` | `(A: torch.Tensor, B: torch.Tensor, out: Optional[torch.Tensor] = None, dtype=torch.int32)` | Tensor | Low-level int8 matrix multiply returning integer accumulation by default. |
| `bitsandbytes.functional.int8_mm_dequant` | `(A: torch.Tensor, row_stats: torch.Tensor, col_stats: torch.Tensor, out: Optional[torch.Tensor] = None, bias: Optional[torch.Tensor] = None)` | Tensor | Dequantizes int8 matmul output using row/column statistics and optional bias. |

## Parameter notes

- `input_features`/`output_features` follow `torch.nn.Linear`: input shape ends in `input_features`; output ends in `output_features`.
- `compute_dtype` controls 4-bit compute, not the packed storage dtype. If `None`, bitsandbytes chooses a default based on input/backend behavior.
- `compress_statistics=True` on 4-bit modules/quantization uses nested statistics to reduce metadata size; preserve the nested `QuantState` when saving/loading.
- `quant_storage` defaults to `torch.uint8`. Non-uint8 storage exists for sharding/FSDP-style workflows but must be supported by the target backend and kept consistent with the device.
- `threshold` in int8 APIs is not a precision knob for 4-bit quantization. It marks large activations/features as outliers for the int8 path.
- `QuantState.as_dict()`/`from_dict()` patterns are used by tests for state serialization; keep packed quantized tensors and their state dictionaries together.
