# Performance and Benchmarks

## Purpose

Use this reference before interpreting bitsandbytes speed or memory claims. Benchmark scripts and examples are evidence, but this runtime skill does not bundle long-running benchmarks as default commands.

## What bitsandbytes Optimizes

- LLM.int8() reduces model weight memory for inference by using vectorwise int8 quantization and outlier handling.
- 4-bit/NF4/FP4 quantization reduces model weight memory further and is commonly used for QLoRA-style finetuning.
- 8-bit optimizers reduce optimizer-state memory, not activations, gradients, dataloader buffers, or all temporary tensors.
- Paged optimizers are most relevant under accelerator memory pressure and need supported backend memory APIs.

## Benchmark Cautions

- Do not compare CPU-only smoke tests with CUDA/XPU performance claims.
- Keep model size, batch size, sequence length, dtype, backend, PyTorch version, and device placement identical when comparing memory.
- Warm up before timing accelerator kernels.
- Use peak memory around forward, backward, and optimizer step separately when diagnosing missing savings.
- Treat repository benchmark programs as hardware-dependent reference evidence; do not run them automatically unless the user asks for a benchmark and accepts the cost.

## Routing

- For optimizer memory-savings questions, use `../sub-skills/optimizers-training/references/optimizer-workflows.md` and its troubleshooting reference.
- For Hugging Face model memory decisions, use `../sub-skills/transformers-integrations/references/integration-workflows.md`.
- For direct module primitive behavior, use `../sub-skills/quantized-modules-functions/references/workflows.md`.
