# Reasoning and agentic troubleshooting

Use this guide after the config inspector flags a risk, a launch fails early, or an agentic service does not produce usable trajectories. Route generic Ray/placement startup to `setup-and-cluster` and metrics/checkpoint/evaluation analysis to `operations-evaluation-debugging`.

## Fast triage sequence

1. **Classify the workflow**: reasoning GRPO/PPO, VLM reasoning, coding online RL, offline code judge, SearchR1, rStar2, WideSeek-R1, AgentLightning, SFT, or reward-model training.
2. **Run static inspection** on the exact YAML the user intends to launch.
3. **Resolve placeholders** in model paths, dataset paths, output paths, service addresses, and credentials.
4. **Check length budget**: `runner.seq_length`, `data.max_prompt_length`, and `algorithm.sampling_params.max_new_tokens`.
5. **Check logprob source**: `algorithm.recompute_logprobs` and `rollout.return_logprobs` must provide old logprobs for actor training.
6. **Check external services** from the workflow table below.
7. **Only then inspect distributed runtime logs** for backend OOMs, NCCL/Ray failures, or model conversion issues.

## Symptom matrix

| Symptom | Likely cause | What to check | Fix direction |
| --- | --- | --- | --- |
| Config launches but generation immediately stops or returns empty responses | Generation budget too small or stop ids/strings too broad | `runner.seq_length`, `data.max_prompt_length`, `sampling_params.max_new_tokens`, `stop`, `stop_token_ids` | Increase `seq_length`, reduce prompt length, remove overly broad stop sequences, or enable detokenization for stop strings. |
| Actor training asserts missing old logprobs | `recompute_logprobs: false` and rollout did not return logprobs | `algorithm.recompute_logprobs`, `rollout.return_logprobs`, backend support | Enable recomputation or rollout logprobs; for rStar2-style down-sampling, keep rollout logprobs available. |
| PPO config runs like GRPO or fails to create critic | Missing critic block or placement | `algorithm.adv_type: gae`, `algorithm.group_size: 1`, `critic.use_critic_model`, `component_placement` | Add critic group/config or switch to GRPO/raw advantage intentionally. |
| GRPO reward is flat or unstable | `group_size` too small, low sampling diversity, reward not comparable within groups | `algorithm.group_size`, temperature, prompt grouping, reward type | Use `group_size >= 2`, temperature around 0.7-1.0, and comparable rewards for completions of the same prompt. |
| Prompt filtering removes all data | Prompt tokens exceed `data.max_prompt_length` | data loader warnings, max prompt length, chat template expansion | Raise `max_prompt_length`, reduce system/tool prompt, or disable filtering only if truncation is acceptable. |
| VLM data loader fails on images | Wrong `image_keys`, unsupported payload, missing files, lazy parquet dependency | `data.image_keys`, `lazy_loading`, image paths/bytes, parquet dependencies | Correct image key names and ensure every worker can read media. |
| SGLang OOM during init or decode | Static memory/KV cache too high, too many requests, CUDA graph capture memory | `gpu_memory_utilization`, `max_running_requests`, `cuda_graph_max_bs`, `enforce_eager` | Lower concurrency or memory utilization; try `enforce_eager: true` to isolate CUDA graph issues. |
| vLLM OOM or stalls | Too many batched tokens, prefix cache/chunked prefill interaction, unsupported attention backend | `vllm.max_num_batched_tokens`, attention backend, prefix caching, model version | Lower max batched tokens, disable optional vLLM features, or switch backend if model support is incomplete. |
| Weight validation fails on first sync | Actor and rollout start from different checkpoints or resume conflicts with validation | `rollout.validate_weight`, `validate_weight_first_sync`, `runner.resume_dir`, model path | Disable first-sync validation when resuming; ensure actor converter source and rollout model path match. |
| Megatron conversion starts unexpectedly | `actor.megatron.use_hf_ckpt: true` and no resume checkpoint | converter `hf_model_path`, TP/PP sizes, save path | Confirm conversion is intended and paths are writable; route conversion operations to operations if checkpoint manipulation is needed. |
| Agent loop hangs | Tool workers not started, service unreachable, parser never recognizes final answer/tool call | `agentloop.toolcall_parser`, tool service host/port, `max_*_turns`, tool response length | Test service reachability separately, fix parser/model prompt alignment, reduce turn limits for smoke tests. |
| Online coding receives no training samples | Client sends only completions, not feedback, or wrong feedback URL/token | completion endpoint, tracking endpoint, headers, server rollout logs | Verify client config points completion traffic to the online router and feedback to tracking ingestion. |
| Offline code rewards fail | Missing LLM judge env vars or auth/model mismatch | `LLMASJUDGE_API_URL`, `LLMASJUDGE_API_KEY`, `LLMASJUDGE_MODEL` | Set credentials or switch to a local/mock reward only for tests. |
| WideSeek online tools fail | Missing Serper/Jina keys or network denied | `SERPER_API_KEY`, `JINA_API_KEY`, `tools.online`, `tools.use_jina` | Provide keys, disable Jina if not used, or switch to offline retrieval. |
| WideSeek judge reward fails | Placeholder judge host/port or unavailable local judge rollout | `agentloop.llm_ip`, `llm_port`, `use_local_judge`, extra rollout config | Set external judge endpoint or configure local judge model group. |
| rStar2 tool calls time out | Redis/code judge server/workers unavailable or saturated | `tools.codejudge.*`, server logs, worker pool size | Start/scale isolated code-judge service; reduce concurrency for smoke tests. |
| AgentLightning Ray serialization error | Passing in-process store object instead of HTTP endpoint | LightningStore endpoint, rollout worker init logs | Use an HTTP-addressable store endpoint reachable from Ray workers. |

## Sequence-length and prompt-budget diagnostics

For any reasoning or agentic run, compute:

```text
generation_budget = runner.seq_length - data.max_prompt_length
```

Guidelines:

- Any explicit `max_new_tokens` must fit inside `generation_budget`. For example, `runner.seq_length: 2048` and `data.max_prompt_length: 1800` leave only 248 completion tokens, so `max_new_tokens: 1024` is inconsistent and likely to trigger truncation or backend OOM.
- Pure math short-answer tasks can work with a smaller prompt budget and large completion budget.
- Search/tool tasks need enough room for tool-call syntax, tool responses, and final answer tags.
- WideSeek-style long-context workflows often use very large `runner.seq_length`; reducing it without reducing turn limits can silently truncate trajectories.
- Chat templates and tool schemas expand prompt length. If filtering removes data, check the post-template prompt, not just raw JSON length.
- VLM prompts include image placeholders and processor-specific tokens; keep `max_prompt_length` conservative.

## Backend memory checklist

### SGLang

Try these in order for memory failures:

1. Lower `rollout.max_running_requests`.
2. Lower `rollout.cuda_graph_max_bs` to match the actual batch/concurrency.
3. Lower `rollout.gpu_memory_utilization`, especially in collocated actor/rollout placement.
4. Set `rollout.enforce_eager: true` for diagnosis if graph capture fails or warm-up is too expensive.
5. Disable `sglang.use_torch_compile` unless deliberately benchmarking it.
6. For agentic runs, shorten `max_tool_response_length` or turn limits before shrinking model context too far.

### vLLM

Try these in order:

1. Set or lower `rollout.vllm.max_num_batched_tokens`.
2. Reduce `data.rollout_batch_size`, `algorithm.group_size`, or rollout micro-batch fields.
3. Disable optional prefix caching or chunked prefill if the model/version combination is unstable.
4. Verify `VLLM_ATTENTION_BACKEND` compatibility through config (`FLASH_ATTN` vs `XFORMERS`).
5. Switch to SGLang if the workflow relies heavily on agentic stop-string parsing or unsupported multimodal behavior.

## Service-specific checks

| Workflow | Minimal static service check | Minimal live check (only when user permits network/service probing) |
| --- | --- | --- |
| Coding online RL | Ports are non-conflicting and client has completion + feedback URLs. | HTTP health/completion request to online router; POST a synthetic feedback payload to tracking endpoint. |
| Offline code judge | Judge env vars are set and not placeholders. | One small chat-completion request to judge endpoint. |
| SearchR1 | `tools.search.server_addr` is concrete. | HTTP request to retrieval server with one query. |
| rStar2 | `tools.codejudge.host_addr`/`host_port` are concrete; concurrency is sane. | Submit a harmless `print(1)` code task through the code judge API. |
| WideSeek offline | Qdrant retrieval/access service address is concrete. | One `/retrieve` and one `/access` request. |
| WideSeek online | `SERPER_API_KEY`; `JINA_API_KEY` if `use_jina`. | One low-cost search/access call if permitted. |
| AgentLightning | Store endpoint is HTTP and model server addresses are reachable from workers. | One store write/read and one model completion through the HTTP server. |

Do not perform live service probes if the user only asked for static config review or if credentials/network use are not authorized.

## Data-format pitfalls

- Reasoning JSON/JSONL loaders support only `.json` and `.jsonl`; VLM loaders additionally support parquet and directories.
- `apply_chat_template: true` expects prompt records already structured as chat messages for text reasoning; for VLM, `use_chat_template` uses processor logic.
- Math/code rewards often expect answers as lists; string answers may be normalized, but nested answer dictionaries should be preserved for WideSeek.
- `filter_prompt_by_length: true` drops overlong samples. If all samples disappear, the loader asserts that no samples remain.
- `data.val_rollout_batch_size` in eval must divide validation dataset size in the reasoning eval runner.
- Agentic rollout batch size multiplied by `group_size` must be divisible across reward/tool workers where applicable.

## Agentic parser and prompt issues

Tool-call parsers are registered by name, with common names:

```text
qwen2.5, searchr1-qwen, rstar2-qwen, wideseek_r1-qwen
```

If the model generates natural-language tool calls rather than the expected tags/JSON:

1. Confirm `agentloop.toolcall_parser` matches the prompt template.
2. Confirm the tokenizer/chat template did not strip tool schema tags.
3. Set `rollout.detokenize: true` while debugging parser behavior.
4. Lower turn limits and print outputs for one small smoke run if the user permits.
5. For rStar2, keep the code tool schema and answer tags aligned with the custom chat template.

## SFT / reward-model issues

| Symptom | Cause | Fix direction |
| --- | --- | --- |
| SFT runs eval only | `data.train_data_paths` is null or missing in VLM SFT pattern | Add train path or confirm eval-only intent. |
| Reward-model early stopping never triggers | Monitor metric name mismatch | Check emitted eval metric names and `runner.early_stop.monitor`. |
| FSDP SFT memory spike | Large global batch, no gradient checkpointing, mixed precision mismatch | Lower micro/global batch, enable checkpointing, check `mixed_precision`. |
| LoRA not training expected modules | `is_lora` or trainable module list mismatched to model family | Confirm LoRA fields and trainable module names; route code changes to extension sub-skill. |
| Megatron SFT conversion or load failure | HF path/converter model name/TP-PP mismatch | Align converter metadata with actor model parallel sizes and checkpoint source. |

## When to stop and ask

Stop before launch when any of the following remain unknown:

- Model/tokenizer path or model type.
- Dataset path, format, prompt key, answer key, or image keys for VLM.
- Whether external services are allowed and reachable.
- GPU/node budget sufficient for actor/rollout/critic/judge groups.
- Whether the user wants live online training versus offline validation.
- Whether a placeholder path/address is intentionally left for later.
