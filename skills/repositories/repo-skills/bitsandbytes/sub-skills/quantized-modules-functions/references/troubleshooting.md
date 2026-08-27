# Quantized Module and Functional Troubleshooting

## Forward fails after constructing a quantized layer

Symptom: a `Linear8bitLt`, `Linear4bit`, or embedding layer constructs successfully but forward fails or behaves like an unquantized module.

Likely cause: the module was not moved to the intended device. bitsandbytes module docs and tests rely on the pattern "load floating weights, then call `.to(device)`" because quantization happens during the device move.

Fix:

1. Construct the bitsandbytes module with matching shape and flags.
2. Load/copy floating weights if starting from a normal PyTorch layer.
3. Call `.to("cuda")`, `.to("xpu")`, `.to("hpu")`, or the intended backend before quantized forward.
4. Only use CPU construction as a signature/import smoke check unless the specific CPU op is known to be supported.

## `SCB` or `CB` errors when loading `Linear8bitLt`

Symptom: loading a checkpoint mentions `SCB`, `CB`, unexpected keys, missing keys, or quantized int8 statistics.

Likely cause: the checkpoint contains quantized `Int8Params` fields, but the destination module is plain `torch.nn.Linear` or an unquantized `Linear8bitLt` that has not initialized quantized state.

Fix:

- Load quantized int8 checkpoints into `bitsandbytes.nn.Linear8bitLt`, not `torch.nn.Linear`.
- Match `input_features`, `output_features`, `bias`, `threshold`, and `has_fp16_weights` to the original module.
- If the state dict contains `weight.CB`/`weight.SCB`, initialize/move the bitsandbytes module to the target device before loading the quantized state.
- If the checkpoint was saved from floating weights before quantization, load first and then call `.to(device)`.

## 4-bit dequantization returns wrong values or fails

Symptom: `dequantize_4bit` fails, returns incorrect shape/dtype, or reports missing metadata.

Likely cause: packed tensor and `QuantState` were separated, mutated, moved to different devices, or reconstructed with mismatched `blocksize`/`quant_type`.

Fix:

- Prefer `packed, state = F.quantize_4bit(...)` followed by `F.dequantize_4bit(packed, state)`.
- Keep `packed`, `state.absmax`, `state.code`, nested `state.state2`, and output tensors on compatible devices.
- Preserve `state.shape`, `state.dtype`, `state.blocksize`, and `state.quant_type` through serialization.
- Re-quantize from original floating weights if `QuantState` was lost; do not invent replacement statistics.

## Unsupported dtype, quant storage, or backend combination

Symptom: errors mention unsupported dtype, `quant_storage`, or backend-specific limitations.

Likely cause: 4-bit and embedding kernels have backend-specific support. HPU/XPU/MPS/CPU paths do not necessarily support every `quant_type`, compute dtype, and storage dtype combination.

Fix:

- Start with `quant_storage=torch.uint8` unless a sharding/FSDP workflow requires another dtype.
- Use `compute_dtype=torch.float16` or `torch.bfloat16` only when the backend supports it.
- Keep input tensors, packed weights, `QuantState`, and module parameters on the same target backend.
- Route native library or backend setup failures to `installation-diagnostics` rather than changing model code blindly.

## Invalid blocksize or slow CPU primitive checks

Symptom: low-level 4-bit op reports invalid blocksize, CPU tests are very slow, or a CPU/MPS 4-bit matmul path skips for blocksize larger than feature size.

Likely cause: registered 4-bit ops accept a fixed blocksize set, and CPU paths are not a full substitute for GPU quantized execution.

Fix:

- For `quantize_4bit`/`dequantize_4bit`/4-bit matmul ops, use blocksizes from `32, 64, 128, 256, 512, 1024, 2048, 4096`.
- For `quantize_blockwise`, use a positive blocksize; default `4096` is a safe starting point for CPU inspection.
- Treat default CPU smoke tests as construction/signature checks, not performance or accuracy validation for GPU kernels.

## Embedding dimension or packing warnings

Symptom: `Embedding4bit`, `EmbeddingNF4`, or `EmbeddingFP4` warns or errors about embedding shape/divisibility.

Likely cause: packed 4-bit embeddings need backend-compatible dimensions and storage layout.

Fix:

- Keep `embedding_dim` compatible with the selected 4-bit packing/backend path.
- Prefer dimensions divisible by common packing widths when designing new models.
- If adapting an existing model with incompatible dimensions, keep that layer unquantized or choose an 8-bit/plain embedding path.

## `quant_state` lost with FSDP, sharding, or state dict transforms

Symptom: after FSDP/sharding/state-dict processing, a 4-bit module no longer has usable `quant_state`, or packed keys like `bitsandbytes__nf4` are missing.

Likely cause: code treated `Params4bit` like a plain `torch.nn.Parameter` and dropped proxied `QuantState` metadata.

Fix:

- Preserve `Params4bit` metadata during traversal and serialization.
- Keep packed tensors and `quant_state` keys together.
- Use non-uint8 `quant_storage` only for workflows that explicitly require it and are backend-supported.
- If metadata is gone, reload from a complete checkpoint or re-quantize from original floating weights.

## Threshold/outlier behavior is confusing

Symptom: changing `threshold` does not affect 4-bit quantization, or int8 output shape/statistics are misunderstood.

Likely cause: `threshold` belongs to LLM.int8/vectorwise outlier handling. It is separate from 4-bit `quant_type` and blocksize.

Fix:

- Use `threshold` with `Linear8bitLt`, `matmul`, and `int8_vectorwise_quant` to control outlier routing.
- Use `quant_type='nf4'` or `'fp4'`, `blocksize`, and `compress_statistics` for 4-bit quantization behavior.
- Inspect `outlier_cols` returned by `int8_vectorwise_quant(A, threshold=...)` when debugging threshold effects.

## Native op is unavailable on CPU-only machines

Symptom: import works, module construction works, but forward or functional quantization fails with a missing native op/backend message.

Likely cause: the installed bitsandbytes package can be imported for inspection, but the requested quantized kernel is not available for the current device/backend.

Fix:

- Use `scripts/quantized-module-smoke.py` without `--run-forward` for CPU-safe checks.
- Run actual quantized forwards only on a supported backend with matching PyTorch/device setup.
- For missing native libraries, wrong CUDA/ROCm/XPU runtime, or backend selection errors, route to `installation-diagnostics`.
