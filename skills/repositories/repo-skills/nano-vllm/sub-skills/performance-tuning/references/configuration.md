# Runtime configuration

`LLM(model, **kwargs)` forwards recognized keyword arguments to the internal
configuration dataclass. These knobs affect scheduler behavior and memory use.

| Knob | Default | Constraints and effect |
| --- | ---: | --- |
| `max_num_batched_tokens` | `16384` | Token budget for a prefill scheduling step. Larger values increase prefill throughput but require more temporary memory. |
| `max_num_seqs` | `512` | Maximum concurrently scheduled sequences. Larger values improve batching until scheduler and KV-cache pressure dominate. |
| `max_model_len` | `4096` | Requested context length; clipped to the model config's positional limit. Lower it to fit more KV blocks. |
| `gpu_memory_utilization` | `0.9` | Fraction of total GPU memory reserved for KV cache after model/warmup allocations. Keep margin for kernels and fragmentation. |
| `tensor_parallel_size` | `1` | Number of NCCL ranks/GPUs, asserted to be between 1 and 8. Model heads, KV heads, vocabulary, and MLP widths must divide across ranks. |
| `enforce_eager` | `False` | When false, decode shapes up to the graph table are captured with CUDA graphs after warmup. When true, run eager kernels only. |
| `kvcache_block_size` | `256` | KV cache granularity and prefix-cache hash unit. Must be divisible by 256. |

## KV-cache sizing

The runner computes available cache blocks from total GPU memory, currently
used memory, peak model warmup memory, current allocations, hidden dimensions,
number of layers, number of KV heads per tensor-parallel rank, and block size.
If the computed block count is non-positive, construction asserts. Recovery is
usually to reduce `max_model_len`, batch pressure, or selected model size; do
not increase workload first.

KV-cache tensor layout is effectively:

```text
2 x num_hidden_layers x num_blocks x block_size x kv_heads_per_rank x head_dim
```

The leading `2` stores key and value caches. Prefix caching is block-level: only
complete blocks before the final prompt block are hashed and reused.

## Scheduler behavior

- Waiting sequences enter prefill first.
- The scheduler fills `max_num_batched_tokens` while respecting
  `max_num_seqs` and available KV blocks.
- If the remaining budget is too small, only the first selected sequence may be
  chunked; later sequences wait to avoid many fragmented partial prefills.
- Decode schedules one token for each running sequence until `max_num_seqs` or
  KV-block availability stops it.
- If appending a token would need a new KV block and none are free, another
  running sequence can be preempted and moved back to waiting.

## Tensor parallelism

Each rank builds the same model graph with sharded parameters. Rank 0 owns the
public runner and communicates method calls to nonzero ranks through shared
memory. All ranks initialize NCCL. Tensor parallelism helps only when the model
and workload are large enough to offset process and communication overhead.

Start with `tensor_parallel_size=1`. Increase it only after validating:

- that enough GPUs are visible;
- that model attention heads, key-value heads, vocabulary, hidden/MLP dimensions
  divide cleanly;
- that the localhost rendezvous port and shared memory are available;
- that the process is launched under a normal main guard.

## CUDA graph versus eager

The default path captures decode graphs for a set of batch sizes after warmup.
Use `enforce_eager=True` to isolate correctness, dynamic-shape, or capture
problems. If eager passes but graph mode fails, the prompt/model/backend is
valid and the problem is graph capture or graph replay state.
