# Rollout backends, data formats, and service integration

Use this reference to reason about RLinf text/VLM rollout, logprob flow, data loaders, and external services before launching a reasoning or agentic workflow.

## Backend selection matrix

| Dimension | SGLang rollout | vLLM rollout |
| --- | --- | --- |
| Config selector | `rollout.rollout_backend: sglang` | `rollout.rollout_backend: vllm` |
| Worker selected by package | SGLang worker, or SGLang HTTP agent worker when `rollout.sglang.serving_mode: worker_http` | vLLM async worker |
| Strengths | Agentic stop strings, serverless generation, HTTP serving mode, SGLang router/server support, direct tool-call parsing hooks. | Prefix-heavy generation, chunked prefill, prefix caching, vLLM sampling/logprob support where compatible. |
| Memory knobs | `rollout.gpu_memory_utilization`, `max_running_requests`, `cuda_graph_max_bs`, `sglang.attention_backend`, `sglang.use_torch_compile`, `enforce_eager`. | `rollout.gpu_memory_utilization`, `vllm.max_num_batched_tokens`, `vllm.enable_chunked_prefill`, `vllm.enable_prefix_caching`, `vllm.attention_backend`, `enforce_eager`. |
| Logprob path | `rollout.return_logprobs` controls whether SGLang returns rollout logprobs; recomputation can bypass them. | `rollout.return_logprobs` maps to vLLM `SamplingParams(logprobs=0)`. |
| Agentic fit | Preferred by coding online RL, SearchR1, rStar2, WideSeek-R1, and AgentLightning HTTP serving patterns. | Works for ordinary reasoning/VLM configs when model/version support is adequate. |
| Initialization pitfalls | CUDA graph warm-up can be slow; unknown SGLang server args fail at worker initialization; wrong `trust_remote_code` or tokenizer path fails early. | vLLM environment variables are set by the worker; multiprocessing spawn and attention backend/version compatibility matter. |

## Core rollout config fields

```yaml
rollout:
  group_name: RolloutGroup
  rollout_backend: sglang       # sglang or vllm
  gpu_memory_utilization: 0.5-0.8
  tensor_parallel_size: 1
  pipeline_parallel_size: 1
  enforce_eager: false
  distributed_executor_backend: mp
  detokenize: false             # true for string stop parsing/debug/agent loops
  padding: null
  eos: null
  return_logprobs: ${not:${algorithm.recompute_logprobs}}
  max_running_requests: 64
  cuda_graph_max_bs: 128
  model:
    model_path: /model/path
    model_type: qwen2.5
    precision: ${actor.model.precision}
```

Key implications:

- `tensor_parallel_size * pipeline_parallel_size` is the per-engine GPU requirement. Placement must allocate contiguous hardware ranks for some rollout launchers.
- `gpu_memory_utilization` reserves backend static memory. Lower it when actor/rollout are collocated or when KV cache OOMs occur; raise it cautiously for long-context decode.
- `max_running_requests` controls concurrency and memory pressure. For long contexts or image inputs, reduce it before lowering batch size globally.
- `cuda_graph_max_bs` should not exceed `max_running_requests`. If warm-up or graph capture fails, set `enforce_eager: true` as a diagnostic.
- `detokenize: false` is faster for pure RL token workflows; set `true` when stop strings, tool parsers, text debugging, or agent loops need generated text.

## Sampling and sequence budget

`algorithm.sampling_params.max_new_tokens` is commonly derived as:

```yaml
max_new_tokens: ${subtract:${runner.seq_length}, ${data.max_prompt_length}}
```

Preflight rules:

- `runner.seq_length` must be greater than `data.max_prompt_length`.
- Any explicit `max_new_tokens` must be less than or equal to `runner.seq_length - data.max_prompt_length`. A config such as `runner.seq_length: 2048`, `data.max_prompt_length: 1800`, and `max_new_tokens: 1024` has only 248 available generation tokens and is OOM/truncation-prone.
- A small difference truncates reasoning/tool use even if rollout succeeds.
- Agentic workflows often need larger `seq_length` because the prompt grows with tool responses and turns.
- `stop` strings require detokenized text handling; `stop_token_ids` can work without detokenization if ids match the tokenizer.
- For GRPO, use stochastic sampling (`do_sample: true`, temperature around 0.7-1.0) to create response diversity.
- For validation/eval, lower temperature or fewer samples may be appropriate, but keep group-size divisibility constraints.

## Logprob, recomputation, and weight-sync flow

RLinf has two logprob sources:

1. **Rollout logprobs** from SGLang/vLLM when `rollout.return_logprobs: true`.
2. **Recomputed logprobs** from actor/inference workers when `algorithm.recompute_logprobs: true`.

Typical decisions:

| Situation | Recommended setting | Reason |
| --- | --- | --- |
| Standard GRPO training | `recompute_logprobs: true`, `return_logprobs: false` | Stable actor-side old/ref logprobs, less rollout memory. |
| TIS or rollout-train KL monitoring | `recompute_logprobs: true`, `return_logprobs: true` | Needs both rollout and recomputed logprobs. |
| rStar2 down-sampling pattern | `recompute_logprobs: false`, `return_logprobs: true` | Selected configs use rollout logprobs because down-sampling is not compatible with recomputation. |
| Coding online RL | `recompute_logprobs: true` | Runner asserts this. |
| Eval-only | `return_logprobs: false` unless metrics need them | Saves memory and latency. |

If `recompute_logprobs` is false and `return_logprobs` is also false, actor training will likely lack `old_logprobs`. Treat that as a risky config unless a custom actor path fills them.

## Training backend fields

### Megatron actor

Important fields:

```yaml
actor:
  training_backend: megatron
  mcore_gpt: true
  spec_name: decoder_gpt
  offload_optimizer: true
  offload_weight: true
  offload_grad: true
  model:
    tensor_model_parallel_size: 1-2+
    pipeline_model_parallel_size: 1+
    sequence_parallel: true|false
    recompute_method: block
    recompute_granularity: full
    seq_length: ${runner.seq_length}
    encoder_seq_length: ${runner.seq_length}
  tokenizer:
    tokenizer_model: /model-or-tokenizer/path
    trust_remote_code: true
    padding_side: right
  megatron:
    use_hf_ckpt: true
    ckpt_convertor:
      hf_model_path: ${rollout.model.model_path}
```

Notes:

- `use_hf_ckpt: true` converts HF checkpoints before initial Megatron training when not resuming.
- `offload_*` lowers memory but can increase sync latency.
- Tensor/pipeline parallel sizes must fit placement and model architecture.
- Multi-agent actor variants may require `enable_dp_load_balance: true` and `pack_traj: true` because trajectory lengths vary strongly.

### FSDP/FSDP2 actor

Important fields:

```yaml
actor:
  training_backend: fsdp
  enable_offload: true|false
  micro_batch_size: 1
  global_batch_size: 8+
  model:
    model_type: ${rollout.model.model_type}
    model_path: ${rollout.model.model_path}
    precision: fp32|bf16|fp16
    is_lora: false
  fsdp_config:
    strategy: fsdp|fsdp2
    sharding_strategy: full_shard|shard_grad_op|hybrid_shard|no_shard
    cpu_offload: false
    reshard_after_forward: true
    enable_gradient_accumulation: true
    gradient_checkpointing: true|false
    mixed_precision:
      param_dtype: bf16|fp16|fp32
```

Notes:

- FSDP configs often keep model `precision: fp32` while using mixed-precision FSDP params for runtime efficiency.
- FSDP2 plus gradient checkpointing is common for newer VLMs.
- `actor.enable_offload` and `fsdp_config.cpu_offload` are different knobs; do not enable CPU offload blindly without understanding memory/latency trade-offs.

## Data families

### Text reasoning (`data.type: math` or `reasoning`)

Expected record after optional chat-template processing:

```json
{"prompt": "question text", "solutions": ["reference answer"]}
```

Config fields:

```yaml
data:
  type: math
  prompt_key: prompt
  answer_key: solutions
  max_prompt_length: 1024
  filter_prompt_by_length: true
  apply_chat_template: false
  train_data_paths: [/data/train.jsonl]
  val_data_paths: [/data/val.jsonl]
```

The loader supports JSON and JSONL. If `apply_chat_template: true`, the prompt field should hold chat messages compatible with the tokenizer’s chat template. String answers are normalized to a list.

### VLM reasoning/SFT (`data.type: vlm`)

Expected record shape varies by dataset class, but common keys are:

```json
{
  "problem": "<image>\nProblem description",
  "images": "image bytes/path/PIL-compatible payload",
  "answer": "\\boxed{x}"
}
```

Config fields:

```yaml
data:
  type: vlm
  dataset_name: robo2vlm
  prompt_key: problem
  answer_key: answer
  image_keys: [images]
  use_chat_template: true
  lazy_loading: true
```

The base VLM loader expands directories into JSON/JSONL/parquet files, supports lazy loading, interleaves `<image>` placeholders, and falls back to placing images before text when no placeholder is present.

### Agentic text datasets

| Workflow | `data.type` | Special fields |
| --- | --- | --- |
| SearchR1 | `math` | prompt/solution JSONL adapted for search-answer reward. |
| rStar2 | `rstar2` | chat-template tools for `python_code_with_standard_io`; optional custom chat template. |
| WideSeek-R1 | `wideseek_r1` | `is_hybrid`, `is_markdown`, `unique_columns`, `data_size`, optional language flags. |
| Coding offline judge | `math` | code FIM records adapted into `prompt` / `solutions`. |

WideSeek answer packaging changes with `is_markdown` and `is_hybrid`: rewards may receive dictionaries containing answer, instance id, required columns, and language. Do not flatten those fields away.

## Reward integration

Built-in rule reward names exposed by the reward registry:

```text
math, vqa, code_offline, searchr1, rstar2
```

Common reward config:

```yaml
reward:
  group_name: RewardGroup
  use_reward_model: false
  reward_type: math
  reward_scale: 1.0
  tokenizer:
    tokenizer_model: ${actor.tokenizer.tokenizer_model}
```

Notes:

- `RewardWorker` computes rule rewards when `use_reward_model: false`.
- If reward text is missing, the worker decodes generated response ids with the configured tokenizer.
- `reward.use_prompt: true` passes decoded prompts to rewards such as offline code judging.
- Down-sampling runs inside reward processing and may need decoded responses plus tokenizer config.

## External service boundaries

| Workflow | Required service or credential | Static config/env indicators | Failure symptom |
| --- | --- | --- | --- |
| Coding online RL | Completion service and feedback ingestion exposed by RLinf; external editor/client sends traffic. | `runner.task_type: coding_online_rl`, `rollout_server.online_router.port`, `rollout_server.tracking_rollout.port`. | Client gets connection refused, no training samples, router stalls during sync. |
| Offline code judge | LLM-as-judge HTTP endpoint. | `LLMASJUDGE_API_URL`, `LLMASJUDGE_API_KEY`, `LLMASJUDGE_MODEL`, `reward_type: code_offline`. | Reward requests fail, all/zero rewards, API auth errors. |
| SearchR1 | Local retrieval server. | `tools.search.server_addr`, `agentloop.toolcall_parser: searchr1-qwen`. | Tool calls time out, empty snippets, reward collapse. |
| rStar2 | Redis-backed code judge server and worker pool. | `tools.codejudge.host_addr`, `host_port`, `concurrency_limit`. | Tool-call HTTP errors, code execution queue stalls. |
| WideSeek-R1 offline | Local Qdrant retrieval/access service. | `tools.online: false`, `tools.search.server_addr`. | Search/access tool errors or high latency. |
| WideSeek-R1 online | Serper and optionally Jina API keys. | `tools.online: true`, `tools.use_jina: true`, `SERPER_API_KEY`, `JINA_API_KEY`. | HTTP 401/403, missing API key errors, no web access. |
| WideSeek-R1 judge | External or RLinf-managed judge model server. | `agentloop.llm_ip`, `llm_port`, `use_local_judge`. | Judge reward/access summary failures. |
| AgentLightning | LightningStore HTTP endpoint and agent framework services. | SGLang worker HTTP serving mode, AgentLightning rollout worker config. | Ray serialization errors or rollout worker cannot reach store/model endpoint. |

## Preflight invariants

Flag and resolve these before launch:

- Placeholder values such as `/path/to`, `TODO`, `LLM_JUDGE_IP`, `LLM_JUDGE_PORT`, or `null` in required model/data/service fields.
- `runner.seq_length <= data.max_prompt_length`.
- `algorithm.adv_type: grpo` with `group_size <= 1`.
- `algorithm.adv_type: gae` for reasoning PPO without `critic.use_critic_model: true`, except custom no-critic configurations with another advantage path.
- `runner.task_type: coding_online_rl` without `algorithm.recompute_logprobs: true` or without SGLang rollout.
- Agentic config with `agentloop` but no `toolcall_parser` and no `tools` block.
- VLM config without `image_keys` or with lazy loading disabled on very large datasets.
- FSDP backend without `actor.fsdp_config`; Megatron backend without `actor.tokenizer` and `actor.megatron` blocks.
