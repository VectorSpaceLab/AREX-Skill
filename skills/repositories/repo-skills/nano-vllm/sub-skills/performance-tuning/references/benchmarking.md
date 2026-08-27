# Benchmarking nano-vLLM

The package's benchmark pattern constructs random token-id prompts, warms up
the engine, generates a fixed number of output tokens, and reports output-token
throughput. This isolates engine scheduling and decode throughput more than it
measures user-facing chat formatting.

## Control the workload

Record these fields for every benchmark:

- model directory and model config family;
- GPU model/count and tensor-parallel size;
- `enforce_eager` versus CUDA graph mode;
- `max_model_len`, `max_num_batched_tokens`, `max_num_seqs`,
  `gpu_memory_utilization`, and `kvcache_block_size`;
- request count and input/output length ranges;
- EOS policy (`ignore_eos=True` for fixed-token throughput, respecting EOS for
  user-like behavior);
- warmup prompt and whether progress bars/logging were disabled.

Use the same token-id workload when comparing modes. String prompts introduce
extra tokenizer work and prompt-template differences.

## Bundled benchmark helper

Run a dry validation first:

```bash
python scripts/benchmark_generation.py --model /path/to/qwen3 --num-seqs 16 --dry-run
```

A full small benchmark:

```bash
python scripts/benchmark_generation.py \
  --model /path/to/qwen3 \
  --num-seqs 32 \
  --min-input-len 64 --max-input-len 256 \
  --min-output-len 16 --max-output-len 64 \
  --max-model-len 1024 \
  --enforce-eager
```

For fixed-token throughput, pass `--ignore-eos`; for application-like behavior,
pass `--respect-eos`. Do not compare fixed-token and EOS-respecting runs as if
they measured the same thing.

## Interpret output

The helper reports:

```text
Total: <requested_output_tokens>tok, Time: <seconds>s, Throughput: <tokens/s>tok/s
```

The numerator is the requested token budget, matching the package's benchmark
style. If EOS is respected, actual generated tokens can be smaller; use
`--ignore-eos` for strict fixed-token throughput. Always include the elapsed
seconds because small workloads can be dominated by warmup or launch overhead.

## Safety and scaling

- Begin with small `num_seqs` and lengths, then grow one axis at a time.
- Avoid benchmark-scale runs in shared sessions unless the user provides a time
  and VRAM budget.
- If a run OOMs, reduce context length/output length or batch count before
  raising `gpu_memory_utilization`.
- Do not run the benchmark against a remote model id; weights must already be
  local.
- Do not present a single run as a stable performance claim. Repeat after a
  fresh process if comparing eager and graph modes.
