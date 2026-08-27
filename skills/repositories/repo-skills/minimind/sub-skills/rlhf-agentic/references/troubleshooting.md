# MiniMind Post-Training Troubleshooting

## Purpose

Use this matrix when DPO, distillation, PPO, GRPO/CISPO, or Agentic RL planning fails validation, stalls, diverges, or produces poor downstream behavior.

## Quick triage

1. Validate data before investigating model code: run [validate_post_training_jsonl.py](../scripts/validate_post_training_jsonl.py) with the intended schema.
2. For Agentic reward issues, run [reward_toolcall_smoke.py](../scripts/reward_toolcall_smoke.py) with a representative `<tool_call>` and `gt` fixture.
3. Confirm external assets: starting policy weight, teacher weight for distillation, reward-model directory for PPO/GRPO/Agent, and optional SGLang service.
4. Reduce to torch rollout, small batch, short generation, and debug logs before trying distributed/SGLang throughput.
5. Route final model-quality concerns to `inference-serving`; this sub-skill diagnoses training/reward setup, not serving behavior.

## Failure matrix

| Symptom | Likely cause | Recovery |
|---|---|---|
| `chosen`/`rejected` missing or validator detects RLAIF records in DPO data | Wrong schema for DPO | Use DPO pair JSONL from [data-formats.md](data-formats.md), or route the task to PPO/GRPO if online reward is required. |
| RLAIF validator warns that the final assistant contains substantive content | RLAIF/PPO/GRPO generates responses online and does not train against that final content | Keep a simple placeholder final assistant, or route supervised targets to `training-basics`. |
| Agentic validator errors on `gt` | `gt` is missing, scalar, nested, or too ambiguous | Use top-level `"gt": ["target"]` or numeric scalars in a list. Avoid nested objects. |
| Agentic validator warns about missing `tools` | Tool-use objective lacks OpenAI-style function definitions on the system message | Add system `tools`, or treat the record as no-tool RLAIF with an explicit reward-model route. |
| Malformed `<tool_call>` JSON is ignored | Model/sample emits invalid JSON inside complete tags, or arguments are a non-JSON string | Use the smoke helper to isolate parsing. Penalize/fix data examples with broken tags, single quotes, trailing commas, or non-object arguments. |
| Tag-count reward penalties are negative | `<tool_call>` and `</tool_call>` counts differ | Add valid closing tags in synthetic data; in model output, lower temperature or increase format-specific examples. |
| Tool call name is penalized despite valid JSON | Name is not present in the sample's tool list | Ensure the system `tools` list contains the exact function name and that route uses the intended tool set. |
| Tool call arguments are penalized | Missing required argument, wrong type, or arguments string failed JSON parse | Check tool-specific required fields in [rollout-and-reward.md](rollout-and-reward.md). Use object arguments when possible. |
| `gt` hit not detected even though answer looks right | Final text lacks the canonical target string/number, includes a rounded value, or `gt` is overly broad/ambiguous | Put the canonical scalar in `gt`; include exact numeric target in final response; avoid targets like `"9"` when many numbers appear. |
| Reward Model load fails | `reward_model_path` points to a missing external checkpoint, incomplete directory, incompatible model, or unsupported dtype/device | Set an explicit local reward-model directory, verify tokenizer/config/weights, and test a tiny scoring call before training. If unavailable, redesign to rule/`gt` reward or stop. |
| Missing starting policy checkpoint | `from_weight`/architecture flags do not match available raw MiniMind weights | Confirm hidden size, layers, dense/MoE suffix, and weight prefix. Route checkpoint preparation to `training-basics`. |
| Distillation teacher load fails | Teacher architecture flags or teacher weight prefix do not match the actual teacher checkpoint | Match `teacher_hidden_size`, `teacher_num_layers`, `teacher_use_moe`, and `from_teacher_weight`; do not assume MoE/dense suffixes are interchangeable. |
| Distillation learns poorly | `alpha`/temperature imbalance, weak teacher, overlong truncation, or mismatched student/teacher vocab | Start from moderate `alpha=0.5`, temperature around `1.0-2.0`, and verify teacher quality; increase CE weight if teacher distribution dominates incorrectly. |
| DPO loss unstable or model forgets | Learning rate too high, `beta` too high, poor pair quality, or assistant masks empty after truncation | Keep DPO LR very small, lower `beta`, reduce max length only after checking assistant spans, and inspect pair quality with the validator. |
| DPO no improvement on correctness tasks | DPO is offline preference alignment and does not explore or execute tools | Use GRPO/CISPO or Agentic RL when correctness depends on generated candidates, tool execution, or `gt`. |
| PPO memory much higher than GRPO | PPO keeps Actor and Critic plus Ref/Reward components | Reduce batch, `max_seq_len`, `max_gen_len`, and `mini_batch_size`; consider GRPO/CISPO if Critic is unnecessary. |
| PPO Critic loss dominates or reward improves slowly | Critic estimates are poor early in training | Use short debug runs, lower update aggressiveness, monitor KL/clip fraction, and consider GRPO/CISPO for simpler single-network optimization. |
| PPO `approx_kl` crosses early stop often | Policy update too aggressive or old/new log-probs misaligned | Lower learning rate, reduce update iterations, inspect `debug_log_ratio`, and verify rollout policy synchronization. |
| GRPO/CISPO group reward std near zero | Degenerate groups: all generations receive similar rewards | Increase `num_generations` if memory allows, improve reward resolution, simplify tasks to MiniMind capability range, or add denser rewards. |
| GRPO/CISPO KL grows quickly | KL penalty too weak or learning rate too high | Increase `beta`, reduce learning rate, reduce generation length, or reset from a closer SFT checkpoint. |
| CISPO behaves like no learning | Importance weights clipped too hard or rewards nearly constant | Check `epsilon_high`, group reward variance, and reward function resolution. |
| Agentic contexts appear shifted or observations are learned as targets | Response masks/context packing are wrong after tool observations | Check debug logs for prompt length, sequence length, and completion text. Tool observation spans must have response mask `0`. |
| Agentic valid tool calls but final reward low | Final answer after tool use omits `gt` or trajectory is marked unfinished | Make final response state the result explicitly; adjust `max_gen_len` or task complexity; check max-turn limit. |
| Agentic reward hacking | Model learns to emit reward-triggering strings/tags without real task completion | Add stricter `gt` validation, diversify tasks, inspect no-tool answers, and evaluate with held-out tool tasks via `inference-serving`. |
| General Q&A worsens after Agentic/RLAIF | Narrow reward optimization trades off broad factuality/robustness | Treat as expected risk. Keep SFT baseline, compare with final evaluation, and choose weights by target capability rather than assuming global improvement. |
| SGLang health check fails | Service not running, wrong host/port, unavailable CUDA, or missing SGLang dependency | Fall back to torch rollout. Only retry SGLang after user confirms local service setup and model/tokenizer compatibility. |
| SGLang `/generate` lacks log-probs | Service or model launch parameters do not support returned logprobs | Use torch rollout or relaunch service with compatible settings; do not train with dummy old log-probs. |
| SGLang `update_policy` fails | Shared checkpoint path not writable/safe, service cannot load updated weights, model format mismatch, or HTTP error | Stop the run. Use a dedicated shared path, check service logs, or fall back to torch. Stale rollout weights break on-policy assumptions. |
| DDP deadlock during PPO/GRPO/Agent | Ranks diverged due to early break, update failure, uneven data, or unsynchronized exception | Use debug mode on one process first. For multi-GPU, keep synchronized KL/update decisions and fail all ranks together. Resume only from a consistent checkpoint. |
| OOM at rollout or loss step | Batch, `num_generations`, `max_seq_len`, `max_gen_len`, `max_total_len`, Critic/Reward Model, or SGLang cache exceeds memory | Lower sequence/generation caps first, then batch/generations. PPO may need smaller `mini_batch_size`; Agentic may need shorter `max_total_len`. |
| Very slow training | Reward Model scoring, multi-turn rollout, SGLang update sync, or CPU fallback is bottlenecking | Profile route choice. Prefer GRPO/CISPO over PPO for lower model count; use SGLang only after correctness is proven. |
| Debug output is too large | `debug_mode` prints full contexts/completions at interval | Increase `debug_interval`, reduce batch/generations for debug runs, and disable before scale-up. |
| `use_compile` causes unexpected failures | Torch compile wrapper interacts with DDP or rollout update | Disable compile for first correctness pass; enable only after policy update and rollout synchronization are stable. |
| WandB/SwanLab logging blocks or credentials missing | Optional telemetry dependency/account not configured | Leave logging disabled for validation and short runs. Do not block schema/reward debugging on telemetry. |

## Debug flag guide

| Route | Flags | Use when |
|---|---|---|
| PPO | `debug_mode`, `debug_interval`, `debug_log_ratio` | Inspect sampled contexts/responses/rewards and verify old/new log-prob ratio starts near 1. |
| GRPO/CISPO | `debug_mode`, `debug_interval` | Inspect all generations in each group and compare rewards. |
| Agentic RL | `debug_mode`, `debug_interval` | Inspect full multi-turn context, prompt length, sequence length, generated completion, `gt`, and reward. |
| Distillation/DPO | `log_interval`, small save interval in a short run | Watch CE/KL/DPO/aux loss before scaling. |

## When to stop instead of patching

Stop and ask for a revised plan when:

- the reward model is unavailable and no rule/`gt` replacement exists;
- the required starting/teacher checkpoint cannot be identified;
- SGLang is required by the user but no local service can be verified;
- data schema validation fails for a large fraction of records;
- `gt` cannot be expressed as scalar targets;
- the objective asks for both broad factuality improvement and narrow Agentic reward optimization without an evaluation trade-off plan.
