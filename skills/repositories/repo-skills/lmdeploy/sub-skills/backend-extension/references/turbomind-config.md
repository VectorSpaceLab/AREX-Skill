# TurboMind Config

TurboMind is LMDeploy's high-throughput backend built around persistent batching and a KV-cache manager. The Python API exposes `TurbomindEngineConfig`; converted TurboMind model directories also contain `triton_models/weights/config.ini`, whose inference fields mirror many runtime concepts.

## Persistent Batch And KV Cache

- Persistent batching keeps a fixed set of batch slots alive during the process and admits requests as slots become free.
- Cache hits let a conversation reuse existing history KV without re-decoding the full context.
- The KV-cache manager allocates device-memory blocks, reuses evicted slots, and can reconstruct evicted histories from compact token IDs on cache miss.
- Prefix caching is most useful when many requests share a long system prompt or prefix; a prefix shorter than one cache block may not improve performance.

## `TurbomindEngineConfig` To Engine Mapping

The TurboMind wrapper transfers the Python config into the C++ engine config roughly as follows:

| Python field | Runtime concept |
| --- | --- |
| `dtype` | C++ data type (`float16` or `bfloat16` after `auto` resolution). |
| `cache_block_seq_len` | Token length per KV block. |
| `quant_policy` | KV-cache quantization policy. |
| `max_batch_size` | Max active batch slots. |
| `max_prefill_token_num` | Max prefill tokens per iteration. |
| `session_len` | Max tokens per sequence/session. |
| `cache_max_entry_count` | Fraction of free memory or explicit KV block count. |
| `cache_chunk_size` | KV-block allocation chunk policy. |
| `enable_prefix_caching` | Prefix cache enable switch. |
| `num_tokens_per_iter`, `max_prefill_iters` | SplitFuse-like prefill iteration controls. |
| `async_` | TurboMind async execution switch. |
| `attn_tp_size`, `attn_dp_size`, `attn_cp_size`, `mlp_tp_size`, `outer_dp_size` | Distributed layout fields. |
| `devices`, `nnodes`, `node_rank`, `communicator` | Device and multi-node execution fields. |

## `config.ini` Concepts

A TurboMind model directory may contain `triton_models/weights/config.ini`. Treat it as a model/runtime description, not a generic editable config. Model-attribute fields should not be changed unless regenerating/converting the model.

Model attributes that should stay tied to the weights:

- `model_name`, `head_num`, `kv_head_num`, `vocab_size`, `num_layer`, `inter_size`.
- `norm_eps`, `attn_bias`, `start_id`, `end_id`.
- `rotary_embedding`, `rope_theta`, `size_per_head`.
- `weight_type`, `group_size`.

Inference fields commonly tuned through Python config or conversion/runtime configuration:

- `session_len`: max sequence length/context window.
- `max_batch_size`: max active batch size.
- `cache_max_entry_count`: memory fraction or explicit KV block count depending on value/version.
- `cache_block_seq_len`: token length of each KV block.
- `cache_chunk_size`: allocation chunk policy.
- `enable_prefix_caching`: shared-prefix reuse switch.
- `quant_policy`: KV-cache quantization.
- `rope_scaling_factor` and `use_logn_attn`: long-context attention behavior.

## Cache Sizing

For TurboMind 2.x, KV block memory is determined by:

```text
cache_block_seq_len * num_layer * kv_head_num * size_per_head * 2 * sizeof(kv_data_type)
```

`cache_max_entry_count` semantics:

- Decimal between `0` and `1`: fraction of available/free GPU memory reserved for KV blocks in modern LMDeploy versions.
- Integer greater than `0`: explicit total number of KV blocks.
- Too high: startup or first request can fail with CUDA OOM from TurboMind allocator.
- Too low: lower concurrency and more cache misses/eviction.

Practical tuning loop:

1. Lower `cache_max_entry_count` first for TurboMind allocator OOM.
2. Lower `session_len` if long contexts are not required.
3. Lower `max_batch_size` when concurrency is less important than fitting the model.
4. Increase `cache_block_seq_len` only if shared prefixes are long enough and block overhead dominates; otherwise keep the default.
5. Enable `quant_policy=8` or `4` only after confirming backend support and quality/performance trade-offs.

## Prefix Caching

Enable prefix caching when requests share a substantial common prefix:

```python
from lmdeploy import TurbomindEngineConfig

backend_config = TurbomindEngineConfig(
    enable_prefix_caching=True,
    cache_block_seq_len=128,
)
```

Watch for:

- No visible improvement when shared prefix length is less than one block.
- Higher memory retention when many different prefixes compete for cache.
- Workloads with long shared system prompts benefit most.

## KV Quant Policy

LMDeploy defines `QuantPolicy` values globally, but each backend accepts a different subset.

- `0` / `QuantPolicy.NONE`: no KV quantization.
- `4` / `QuantPolicy.INT4`: 4-bit KV cache.
- `8` / `QuantPolicy.INT8`: 8-bit KV cache.
- `16` / `QuantPolicy.FP8` and `17` / `QuantPolicy.FP8_E5M2`: valid in PyTorch config on supported devices, rejected by TurboMind config.
- `42` / `QuantPolicy.TURBO_QUANT`: advanced policy surfaced in the enum; validate backend support before recommending it for a concrete deployment.

If `TurbomindEngineConfig(quant_policy=16)` fails, switch to `0`, `4`, or `8`, or use PyTorch if FP8 KV cache is required.

## Long Context

- `session_len` sets the max per-sequence context budget and directly affects memory pressure.
- `rope_scaling_factor` enables Dynamic NTK-style RoPE scaling when positive.
- `use_logn_attn` enables LogN attention scaling.
- Long-context changes should be paired with model-specific quality checks, not just engine startup.

## Validation Commands

```bash
python - <<'PY'
from lmdeploy import TurbomindEngineConfig
print(TurbomindEngineConfig(cache_max_entry_count=0.5, cache_block_seq_len=128, quant_policy=8))
PY

python sub-skills/backend-extension/scripts/inspect_backend_config.py --backend turbomind --json
python -m lmdeploy check_env
```

If the task references `scripts/test_turbomind_model.py`, treat it as a source-checkout/native-candidate reference. Do not make public skill instructions depend on that source script existing; adapt the underlying intent into local commands or tests for the user's checkout.
