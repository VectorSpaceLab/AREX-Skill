---
name: performance-tuning
description: "Tune nano-vLLM batching, KV-cache capacity, CUDA graph/eager
  execution, tensor parallelism, and benchmark throughput for local Qwen3
  inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Performance tuning

Use this route after a small generation smoke test works and the task is to
increase throughput, fit a model/workload into VRAM, diagnose scheduler/KV-cache
behavior, or compare benchmark settings. For basic prompting and output schema,
start with [../offline-inference/SKILL.md](../offline-inference/SKILL.md).

## Fast path

1. Keep the model, tokenizer, prompt lengths, EOS policy, and hardware fixed
   while changing one runtime knob at a time.
2. For correctness triage use `enforce_eager=True`; for throughput, test the
   default CUDA graph path after eager mode is stable.
3. Tune `max_model_len`, `max_num_batched_tokens`, `max_num_seqs`, and
   `gpu_memory_utilization` together because they determine KV-cache pressure.
4. Use `tensor_parallel_size=1` as the baseline. Increase it only when multiple
   visible GPUs and divisible Qwen3 dimensions are available.
5. Use [scripts/benchmark_generation.py](scripts/benchmark_generation.py) with
   `--dry-run` before loading weights.

Read [references/configuration.md](references/configuration.md) for each knob,
[references/benchmarking.md](references/benchmarking.md) for workload design,
and [references/troubleshooting.md](references/troubleshooting.md) for OOM,
NCCL, graph capture, and benchmark-variance failures.

## What the scheduler optimizes

Nano-vLLM schedules prefill before decode. Prefill can fill the current
`max_num_batched_tokens` budget, and only the first waiting sequence can be
chunked when the remaining budget is smaller than its uncached prompt. Decode
steps schedule one token per running sequence, preempting sequences when no KV
block can be appended. Prefix caching hashes full KV blocks and can reuse a
matching prefix across requests.

## Benchmark command pattern

```bash
python scripts/benchmark_generation.py \
  --model /path/to/local-qwen3 \
  --num-seqs 64 \
  --min-input-len 64 --max-input-len 512 \
  --min-output-len 32 --max-output-len 256 \
  --enforce-eager \
  --dry-run
```

Remove `--dry-run` only after validating the workload and environment. Use
`--respect-eos` for user-like runs and `--ignore-eos` for fixed-token
throughput comparisons. The bundled benchmark reports total requested output
tokens, elapsed time, and tokens/second; it does not claim parity with any
other backend unless the comparison controls the same workload.

## Route boundaries

- Route prompt formatting, chat templates, and `SamplingParams` usage to
  offline inference.
- Route Qwen3 architecture, packed weights, or tensor-parallel layer changes to
  [../model-internals/SKILL.md](../model-internals/SKILL.md).
- Do not treat a successful dry run or import check as proof of full CUDA
  throughput; full validation needs model weights and a bounded GPU run.
