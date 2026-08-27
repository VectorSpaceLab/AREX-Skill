# Deployment troubleshooting

## Quick triage

| Symptom | Likely cause | Action |
|---|---|---|
| Online quantization fails during or after `from_pretrained` | `device_map="auto"` was used with `model.quantize(...)` | Remove `device_map` for online quantization. Load in CPU memory with `torch_dtype=torch.float16`, call `model.quantize(4 or 8)`, then `.cuda()`. |
| `ModuleNotFoundError: bitsandbytes` | BitsAndBytes is not installed in the runtime environment | Install a BitsAndBytes build compatible with the installed Torch/CUDA stack, then rerun `scripts/quantize_model.py --dry-run --validate-imports ...`. |
| BitsAndBytes emits CUDA or `CUDA_HOME` warnings | Optional compiled ops or CUDA discovery are imperfect | Treat warnings as non-blocking only if CUDA tensor allocation and a BitsAndBytes layer smoke test pass. Otherwise repair the CUDA/Torch/BitsAndBytes version alignment. |
| CPU inference works but is unusably slow | CPU float32 deployment is a fallback path | Use it only for correctness/smoke checks, reduce sequence length and batch size, or move to CUDA quantization / an external optimized CPU stack. |
| `normalize_lm_head.py` cannot find `pytorch_model.bin` | Checkpoint uses sharding or another format | The bundled conversion helper targets the documented single-file PyTorch checkpoint. Use a dedicated sharded/safetensors conversion path instead. |
| `lm_head.weight` key is missing | Checkpoint layout differs from the documented state dict | Inspect the checkpoint keys. Do not guess-rewrite another tensor unless you know the target architecture expects it. |
| Quantized model runs out of memory | Model size, sequence length, batch size, or KV cache still exceeds device capacity | Prefer 4-bit over 8-bit, reduce batch/sequence length, close other GPU processes, or use a smaller model family. |
| Quality regresses more than expected | 4-bit quantization and workload mismatch | Try 8-bit, fp16/bf16, or task-specific evaluation. The documented 4-bit drop is about 1-2 points on cited aggregate benchmarks, not a universal guarantee. |

## `device_map="auto"` and online quantization

Online Baichuan2 quantization is not the same as loading an already quantized checkpoint. The documented flow is:

1. Load the original model into CPU memory.
2. Call `model.quantize(4)` or `model.quantize(8)`.
3. Move the quantized model to CUDA with `.cuda()`.

Because `device_map="auto"` shards or places modules during loading, it conflicts with the online `quantize()` path. Use `device_map="auto"` only for the pre-quantized 4-bit load or the offline 8-bit save/reload path.

## BitsAndBytes and CUDA compatibility

A known-good inspection stack imported BitsAndBytes `0.50.1`, ran Torch `2.5.1+cu121`, allocated a CUDA tensor, and completed a `bitsandbytes.nn.Linear8bitLt` CUDA forward pass. Use the same style of checks on a target host:

```bash
python scripts/quantize_model.py --dry-run --validate-imports --mode online --bits 4
```

If imports pass but full model quantization fails, the remaining issue is often model memory, CUDA driver/runtime mismatch, or an API difference in the installed Transformers/BitsAndBytes versions.

## CPU slowness and memory

The CPU recipe intentionally uses `torch.float32`. That makes it portable but slow and memory-heavy. Start with:

- batch size 1,
- short prompt and generation lengths,
- no concurrent model copies,
- enough host RAM for weights plus KV cache and Python overhead.

If the user expects production throughput, route them to CUDA quantization, a converted checkpoint for an external optimization stack, or a separate serving stack.

## Checkpoint conversion assumptions

`normalize_lm_head.py` assumes:

- an input directory, not a remote model id;
- a single `pytorch_model.bin` file;
- a state-dict-like checkpoint mapping;
- a tensor key named `lm_head.weight`;
- row-wise L2 normalization with default `dim=1`.

If any assumption is false, stop and inspect the checkpoint format. Do not overwrite the original directory. For a safe first pass, run:

```bash
python scripts/normalize_lm_head.py --input-dir ./model --output-dir ./model-normalized --dry-run --validate-key
```

## Precision and batch-size tradeoffs

- **fp16/bf16**: best baseline for CUDA memory/performance when quantization is not required.
- **8-bit**: lower memory with moderate precision risk; often a good compromise when 4-bit quality is too low.
- **4-bit**: lowest documented memory path; verify task quality and tokenizer/generation settings.
- **float32 CPU**: portability and CPU-only loading, not speed.

For any route, batch size and sequence length can dominate runtime memory through the KV cache. When debugging OOM, reduce batch size and maximum generation length before changing model code.
