# Continuous Batching

Continuous batching is a serving-oriented generation workflow that lets new requests join while active requests are decoding. It requires model execution, a paged KV cache, and backend support; do not treat it as a pure configuration-only feature.

## Core APIs

- `ContinuousBatchingConfig(...)` controls scheduler, KV cache, compile, CUDA graph, prefix caching, offload, and per-request processor behavior.
- `ContinuousBatchingManager(model, tokenizer, generation_config=..., continuous_batching_config=...)` runs a background manager for request submission and result retrieval.
- `generate_batch(...)` is a higher-level batch-oriented path for supported cases.
- `GenerationConfig(...)` still controls generation semantics such as `max_new_tokens`, EOS, and sampling.

## Request Lifecycle

1. A request enters the waiting queue.
2. The scheduler admits prompt tokens into a prefill step as budget allows.
3. The paged KV cache stores reusable key/value blocks.
4. Decode steps generate one or more tokens while new prefill work may join.
5. Streaming requests emit partial outputs; completed requests move to done.
6. Cancelled requests free cache blocks and stop producing outputs.

## Important `ContinuousBatchingConfig` Decisions

| Area | Options | Use when |
| --- | --- | --- |
| KV budget | `max_memory_percent`, `num_blocks`, `block_size`, `max_batch_tokens` | You need predictable memory and token throughput. |
| Request cap | `max_requests_per_batch`, `safety_margin` | Large vocabularies or many concurrent prompts cause logits/KV pressure. |
| Scheduler | `scheduler_type="fifo"` or `"prefill_first"` | FIFO favors fairness; prefill-first can reduce time-to-first-token for queued prompts. |
| Per-request sampling | `per_request_processors=True` | Requests need different `temperature`, `top_k`, or `top_p` in one manager. |
| Prefix caching | `allow_block_sharing` | Many requests share system prompts or prefixes. |
| CUDA graphs | `use_cuda_graph`, padding interval sizes | Stable shapes and long-running serving make graph capture worthwhile. |
| Compile | `default_compile_level`, `varlen_compile_config`, `decode_compile_config` | Warmup cost is acceptable for throughput. |
| Offload | `cpu_offload_space`, `cpu_offload_space_safety_threshold` | Long sessions risk filling GPU KV cache and recomputation is expensive. |
| Logprobs | `return_logprobs=True` | Downstream scoring, RL, or audit workflows need per-token log probabilities. |

## Paged Attention Requirements

Continuous batching requires paged attention. Configure the model with a paged attention implementation when loading it.

| Backend | `attn_implementation` | Extra dependency |
| --- | --- | --- |
| FlashAttention | `"paged|flash_attention_2"` | `flash-attn` package |
| PyTorch SDPA | `"paged|sdpa"` | PyTorch native support |
| Eager | `"paged|eager"` | No extra attention package beyond backend |

If a non-paged backend such as `"flash_attention_2"` is used, continuous batching may add the `"paged|"` prefix at startup when possible. Agents should still make the intended paged backend explicit in production guidance.

## Per-request Sampling

When `per_request_processors=True`, the manager can apply request-specific `temperature`, `top_k`, and `top_p`. The associated processor must be activated by a non-default value in the base generation config. For example, set `temperature` to a value other than `None` or `1` in `GenerationConfig` if requests will vary temperature later.

```python
from transformers.generation import ContinuousBatchingConfig, GenerationConfig

generation_config = GenerationConfig(max_new_tokens=64, do_sample=True, temperature=0.7, top_p=0.9)
cb_config = ContinuousBatchingConfig(per_request_processors=True, max_requests_per_batch=128)
```

## Streaming and Shutdown

Operational rules:

- Use `add_request(...)` or `add_requests(...)` to submit work; pass `streaming=True` for partial outputs.
- Use `get_result(...)` for queued outputs or `request_id_iter(...)` for one streaming request.
- Call `stop()` to stop accepting new requests and let active work finish.
- Call `destroy()` when distributed resources should be released permanently; a destroyed manager cannot be restarted.
- After `stop()`, new submissions are dropped and should be treated as application-level errors.

## Tensor Parallelism and Sliding Window

For large models, continuous batching can work with tensor parallel loading such as `tp_plan="auto"` when the architecture supports it. The tensor parallel size must be compatible with model attention heads, including `num_key_value_heads`. Sliding-window attention changes cache behavior; prefix sharing is automatically constrained when layers are not full attention.

## Safe Planning Without Hardware

When no GPU/model environment is available, document a plan rather than claiming runtime validation:

- Model loading needs backend dependencies such as `torch`.
- Paged attention implementation must be selected and installed.
- KV cache sizing depends on free GPU memory, dtype, heads, layers, and block size.
- Compile and CUDA graph settings should be benchmarked after warmup.
- Offload needs host RAM capacity and, when available, `psutil` for safety threshold checks.

Route HTTP serving and `transformers serve` command details to `../serving-cli/SKILL.md`; keep this reference focused on generation semantics and manager configuration.
