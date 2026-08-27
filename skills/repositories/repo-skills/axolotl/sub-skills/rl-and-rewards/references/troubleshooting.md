# RL and Reward Troubleshooting

Use this guide when an Axolotl GRPO, EBFT, vLLM, NeMo Gym, Hatchery, or async RL run fails before training, hangs at rollout generation, or trains with no reward signal.

## Reward Function Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Import error for `rewards.name` | Reward module is not importable from the training working directory | Run from the directory containing the module, package it, or adjust the import path in `trl.reward_funcs` |
| Reward returns scalar for a batch | Function scores only one completion | Return a list with `len(completions)` finite numeric values; run `python scripts/validate_reward_function.py rewards.py:name` |
| Reward length mismatch | Filtering, zipping, or exception path dropped scores | Always append exactly one score per completion, including fallback scores |
| All rewards equal | Reward parser never finds the answer, answer column removed, or reward too coarse | Preserve answer columns in the transform, log parsed values locally, add format reward only as auxiliary shaping |
| Reward changes between identical calls | Randomness, clock use, mutable global state, external service state, or file reads | Make the reward deterministic or explicitly isolate external environment scoring |
| `math_verify` or alarm-based verifier fails in threads | Verifier requires a process main thread | Set `trl.reward_num_workers` to use subprocess reward workers |

## vLLM and Weight Sync

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Trainer waits for vLLM | Server is not started, wrong host/port, or health endpoint not ready | Start `axolotl vllm-serve config.yaml`, verify the configured host/port, then start training |
| Rewards stay flat after a previous run | Stale vLLM server state or mismatched base model | Restart vLLM between experiments and verify `base_model` matches the trainer config |
| Weight sync is slow | Full-model/NCCL sync path is contending with generation | Use LoRA or QLoRA with `trl.vllm_lora_sync: true` when appropriate |
| vLLM OOM | `gpu_memory_utilization`, context length, tensor parallel size, or model size is too aggressive | Lower `gpu_memory_utilization`, set `vllm.max_model_len`, reduce model size, or adjust vLLM GPU allocation |
| Trainer OOM during scoring | `micro_batch_size`, `num_generations`, vocabulary logits, or completion length too large | Reduce `micro_batch_size`, `num_generations`, or `max_completion_length`; consider streaming partial batches |
| Response validation or missing logprobs | Wrong serve path or incompatible vLLM server | Use Axolotl's serving command for GRPO configs and confirm LoRA sync settings match the server mode |

## Async GRPO Issues

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Async run deadlocks with distributed training | Background rollout thread conflicts with distributed collectives | Disable `async_prefetch` for that launch or route distributed launch details to `distributed-and-performance` |
| Config rejected for sequence parallel plus async | Incompatible trainer paths | Disable one of sequence/context parallel GRPO or async data-producer GRPO |
| Learning degrades with async | vLLM weights too stale | Lower `vllm_sync_interval`, enable `vllm_importance_sampling_correction`, prefer `importance_sampling_level: token` |
| Replay worsens instability | Replayed log-probs are stale or replay buffer dominates fresh data | Keep `replay_recompute_logps: true`, reduce `replay_buffer_size`, or disable replay |
| Many skipped batches | Zero reward variance within prompt groups | Improve reward granularity, increase `num_generations`, fix answer parsing, or use re-roll later in training |

## EBFT Issues

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| EBFT requested without vLLM on structured mode | Structured rollout generation usually needs vLLM | Start `axolotl vllm-serve` or intentionally switch to strided/no-vLLM settings for a small local experiment |
| User expects vLLM for strided mode | Mode confusion | Strided EBFT is trainer-local and does not require vLLM |
| DataLoader fails on strings | Strided transform left raw text columns in the mapped dataset | Use a transform that emits tensors and removes original string columns |
| `completion_mean` errors | Prompt lengths are unavailable | Use a dataset transform that emits `prompt_length` or choose another `embed_method` |
| `alignment` stays low | Feature layers or pooling are not useful for the task | Try `[0.25, 0.5, 0.75]`, `last_token`, or `completion_mean` where supported |
| Diversity dominates reward | `diversity_coef` too high, whitening/temperature mismatch, or mode collapse | Reduce `diversity_coef`, increase temperature, inspect `ebft/diversity`, and keep whitening enabled |
| Strided checkpoint error | Gradient checkpointing mode conflicts with flex-attention masks | Use reentrant gradient checkpointing with flex attention |

## NeMo Gym and Environment Services

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| NeMo Gym config validation fails | Missing `nemo_gym_datasets` or server config fields | Provide dataset entries with `path` and server routing, or set auto-start false when servers are external |
| Multi-turn silently behaves single-turn | Agent `/run` server unavailable or `nemo_gym_multi_turn` false | Enable multi-turn and verify the agent service, not just `/verify` resources |
| Tool calls fail validation | Tool schema lacks strict settings or allows extra properties | Use strict tool schemas with no additional properties for agent environments |
| Empty completions from environment proxy | Context length leaves no room for completion | Ensure server `max_model_len` exceeds prompt plus `max_completion_length` |
| LoRA runtime loading fails in OpenAI-style vLLM | Server lacks runtime LoRA support | Start vLLM with LoRA runtime loading enabled when using integration-specific OpenAI server paths |

## Safety Checklist Before Training

- Run the local reward validator for custom reward functions.
- Confirm config fields under `trl:` and `vllm:` refer to the same host and port.
- Confirm `base_model`, chat template, and stop-token settings match between trainer and generation server.
- Keep secrets out of YAML examples and logs; use environment variables or user-local config for backend keys.
- Treat `axolotl train`, live vLLM serving, external environments, and model loading as expensive runtime actions requiring user approval in interactive workflows.
