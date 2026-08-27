# Performance troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `config.num_kvcache_blocks > 0` assertion fails | Not enough memory remains for any KV-cache block after model/warmup allocations. | Lower `max_model_len`, workload size, or model size; keep `gpu_memory_utilization` realistic. |
| OOM during prefill | `max_num_batched_tokens` or prompt lengths are too large for temporary attention/workspace memory. | Reduce prefill token budget or input lengths; try eager mode to separate graph state from capacity. |
| OOM during decode | Too many active sequences or output tokens consume KV blocks. | Reduce `max_num_seqs`, output length, or request count. |
| Prefix caching does not help | Prompts do not share full block-aligned prefixes or final prompt blocks are not cached. | Group requests with long identical prefixes and understand caching happens per complete KV block. |
| Tensor parallel run hangs | Spawned ranks, NCCL rendezvous, shared memory, or visible-device setup is wrong. | Use a main guard, start with TP=1, check GPU count, free the rendezvous port, and avoid nested multiprocessing. |
| Tensor-parallel assertion | Heads, KV heads, vocab, hidden size, or intermediate size is not divisible by rank count. | Use the model-internals contract checker and pick a smaller TP size. |
| CUDA graph mode fails but eager passes | Shape/backend is valid, but graph capture/replay is not. | Use `enforce_eager=True` for correctness; benchmark graph mode separately after a fresh process. |
| Benchmark throughput varies widely | Warmup, GPU clocks, tiny workloads, logging/progress bar overhead, or competing processes dominate. | Increase workload carefully, disable progress bars, repeat runs, and record GPU utilization. |
| Output-token denominator is misleading | EOS was respected, so fewer tokens were actually generated than requested. | Use `--ignore-eos` for fixed-token throughput or compute actual generated token totals from outputs. |
