---
name: deployment
description: "Route Baichuan2 quantization, CPU deployment, and
  Baichuan1-optimization checkpoint conversion."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# deployment

Use this sub-skill when a task is about deploying Baichuan2 with smaller GPU memory, CPU-only loading, or checkpoint conversion for Baichuan 1-style optimization stacks.

Do **not** use this sub-skill for interactive chat UX, web/API serving, prompt formatting, or fine-tuning/LoRA. Route those requests to the sibling inference or fine-tuning sub-skills.

## Route by user intent

- **4-bit or 8-bit quantization, BitsAndBytes, CUDA memory reduction, pre-quantized Chat weights**: read [references/quantization.md](references/quantization.md) and use [scripts/quantize_model.py](scripts/quantize_model.py) for a dry-run plan or a bounded helper run.
- **CPU-only deployment**: read [references/cpu-deployment.md](references/cpu-deployment.md). Use a float32 CPU model load; expect slow inference and do not treat CPU as proof of CUDA quantization readiness.
- **Reuse Baichuan 1 compilation, quantization, or other inference optimizations**: read [references/conversion.md](references/conversion.md) and use [scripts/normalize_lm_head.py](scripts/normalize_lm_head.py) to create a separate checkpoint directory with normalized `lm_head.weight`.
- **Deployment failure, dependency warnings, checkpoint layout mismatch, or memory/precision tradeoff**: read [references/troubleshooting.md](references/troubleshooting.md) before changing model code.

## Operating decisions

1. **Online quantization is CUDA-native.** Load the full model into CPU memory with `torch_dtype=torch.float16`, omit `device_map="auto"`, call `model.quantize(4)` or `model.quantize(8)`, then move the quantized model to CUDA.
2. **4-bit choices differ by workflow.** For lowest-memory Chat inference, prefer the published 4-bit Chat checkpoints when available. For local online quantization, Baichuan2 uses BitsAndBytes 4-bit quantization with NF4 format.
3. **8-bit offline saving uses the Transformers/BitsAndBytes path.** Load with an 8-bit quantization configuration and `device_map="auto"`, then save to a new directory for future reloads.
4. **CPU deployment is a separate float32 path.** It does not use BitsAndBytes, CUDA, or `model.quantize`; it is useful for CPU-only correctness checks or very low-throughput runs, but is expected to be slow.
5. **Baichuan 1 optimization reuse requires checkpoint conversion first.** Normalize `lm_head.weight` in a copied Baichuan2 checkpoint directory; do not overwrite the original checkpoint.

## Bundled helpers

- `scripts/quantize_model.py --dry-run --validate-imports ...` prints the selected quantization plan without loading model weights.
- `scripts/quantize_model.py --mode online --bits 4|8 ...` performs the README-style online quantization route when CUDA is available.
- `scripts/quantize_model.py --mode offline-8bit --save-dir ...` saves an 8-bit quantized model directory.
- `scripts/normalize_lm_head.py --dry-run --validate-key ...` checks a single-file PyTorch checkpoint layout before writing anything.
- `scripts/normalize_lm_head.py --input-dir ... --output-dir ...` writes a normalized-`lm_head` checkpoint into a new directory.

## Evidence and verification anchors

This sub-skill is anchored in the documented Baichuan2 quantization, CPU deployment, and Baichuan 1 migration snippets. Environment inspection also verified a CUDA-capable stack with Torch `2.5.1+cu121`, Transformers `5.15.0`, BitsAndBytes `0.50.1`, a successful CUDA tensor smoke check, and a successful `bitsandbytes.nn.Linear8bitLt` forward smoke check.
