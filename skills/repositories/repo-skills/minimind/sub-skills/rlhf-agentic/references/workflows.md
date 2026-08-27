# MiniMind Post-Training Workflows

## Purpose

Read this when selecting among MiniMind post-training algorithms or preparing a safe configuration plan. This reference distills repository evidence into runtime guidance; it does not require future agents to reopen the evidence files.

## Evidence basis and source-script decisions

The following artifacts were used as source evidence only. Full training entrypoints are intentionally not bundled because they perform long-running training, write checkpoints, may use distributed backends, and depend on user-selected model/data paths. The reusable operating knowledge is distilled here and the safe bundled replacements are the validators and reward/tool-call smoke helpers.

| Source evidence artifact | Runtime decision | Bundled replacement or distilled knowledge |
|---|---|---|
| README and README_en RLHF/RLAIF/Agentic sections | Distill route selection, trade-offs, weight names, and evaluation handoff | This reference plus [rollout-and-reward.md](rollout-and-reward.md) |
| dataset/lm_dataset.py `DPODataset` | Distill DPO `chosen`/`rejected` pair schema and assistant loss-mask behavior | [data-formats.md](data-formats.md) and validator script |
| dataset/lm_dataset.py `RLAIFDataset` | Distill online prompt schema and `thinking_ratio` behavior | [data-formats.md](data-formats.md) and validator script |
| dataset/lm_dataset.py `AgentRLDataset` | Distill multi-turn messages, system `tools`, and top-level `gt` schema | [data-formats.md](data-formats.md), validator script, reward smoke helper |
| trainer/train_distillation.py | Reference-only full training; distill teacher/student settings, MoE/dense relation, `alpha`, `temperature`, and `CE + KL` loss | Distillation section below |
| trainer/train_dpo.py | Reference-only full training; distill pair schema, frozen ref model, log-prob comparison, and `beta` | DPO section below |
| trainer/train_ppo.py | Reference-only full training; distill Actor/Critic/Reference/Reward layout, GAE, clip, KL, rollout, and debug settings | PPO section below |
| trainer/train_grpo.py | Reference-only full training; distill generation grouping, GRPO versus CISPO, token KL, and group reward variance | GRPO/CISPO section below |
| trainer/train_agent.py | Reference-only full training; adapt tool-call parsing, mock-tool validation, `gt` reward, response-mask, and context-packing behavior | [rollout-and-reward.md](rollout-and-reward.md) and reward smoke helper |
| trainer/rollout_engine.py | Adapt backend checks only; do not launch SGLang from the helper | [rollout-and-reward.md](rollout-and-reward.md) and optional dry/probe checks in reward smoke helper |
| trainer/trainer_utils.py `LMForRewardModel` | Distill external Reward Model path, `get_score` use, and score clipping | [rollout-and-reward.md](rollout-and-reward.md) |
| scripts/eval_toolcall.py | Reference-only final evaluation operation; distill signal expectations and route operation to `inference-serving` | Final evaluation handoff section below |

## Algorithm selection matrix

| Goal | Choose | Data schema | Online generation | Extra models/services | Typical output weight prefix | Main risk |
|---|---|---|---|---|---|---|
| Transfer a teacher distribution into a student | White-box distillation | SFT-style conversations | No | Teacher checkpoint plus student checkpoint | `full_dist` | Wrong teacher/student architecture, weak teacher, over-weighting KL or CE |
| Learn from static human/curated preferences | DPO | `chosen`/`rejected` pair JSONL | No | Frozen reference model initialized from policy start | `dpo` | Bad preference pairs, too-large beta, forgetting from high LR |
| Optimize responses using model/rule reward with value estimation | PPO | RLAIF prompt JSONL | Yes, one generation per prompt | Actor, Critic, Ref, Reward Model; optional SGLang | `ppo_actor` | High memory, Critic instability, KL/DDP issues |
| Optimize with grouped candidates and no Critic | GRPO | RLAIF prompt JSONL | Yes, multiple generations per prompt | Policy, Ref, Reward Model; optional SGLang | `grpo` | Degenerate groups with near-identical rewards |
| Use GRPO grouping but avoid clipped-ratio gradient truncation | CISPO | RLAIF or Agentic JSONL | Yes | Same as GRPO/Agentic | `grpo` or `agent` depending route | Ratio clipping, reward hacking, overly narrow target |
| Learn multi-turn tool use with delayed reward | Agentic RL | Agent RL messages/tools/`gt` JSONL | Yes, multi-turn | Policy, Ref, Reward Model, mock tools; optional SGLang | `agent` | Malformed tool calls, invalid `gt`, context misalignment, tool-task overfitting |

## Shared planning rules

- Start from an already usable SFT-style checkpoint unless the user explicitly wants distillation from a different base. Basic pretrain, SFT, LoRA, and tokenizer setup are owned by `training-basics`.
- Match architecture flags to the starting checkpoint: `hidden_size`, `num_hidden_layers`, and `use_moe` decide the raw weight suffix and model shape.
- Treat all post-training jobs as long and stateful. Validate data first, run a tiny smoke or short debug run when possible, then scale sequence length, batch size, generations, and epochs.
- Use explicit external paths for user-provided data, reward models, checkpoints, and optional SGLang shared storage. Do not rely on source defaults for external assets.
- Prefer `from_resume=0` for a new experiment. Use resume only when the checkpoint/resume state matches the same architecture, weight prefix, GPU world size expectations, and optimizer/scheduler state.
- Save weight prefixes indicate downstream handoff: `full_dist`, `dpo`, `ppo_actor`, `grpo`, and `agent` are raw MiniMind weights that should be routed to `inference-serving` for evaluation or conversion.

## Command-shape planning without bundled long-training entrypoints

This sub-skill intentionally bundles safe validators and smoke helpers, not full training launchers. When an authorized training run is needed, construct the command shape from the selected MiniMind post-training entrypoint and the flags below. Resolve the actual entrypoint through the integrated MiniMind root skill or the active execution environment, rather than reopening evidence files from this sub-skill.

Use this non-executable shape for planning reviews:

```text
<minimind-post-training:ROUTE> \
  --data_path DATA_JSONL \
  --from_weight START_WEIGHT \
  --hidden_size HIDDEN_SIZE \
  --num_hidden_layers NUM_LAYERS \
  --use_moe 0_or_1 \
  --save_weight OUTPUT_PREFIX \
  ROUTE_SPECIFIC_FLAGS
```

For distributed training, the same route-specific flags apply; add the launcher and process count only after backend availability and DDP behavior are confirmed.

## White-box distillation plan

Choose distillation when the user has a teacher checkpoint and wants the student to learn token-level teacher preferences, not merely hard teacher answers. Black-box distillation of teacher outputs is closer to SFT and should route to `training-basics`.

Core behavior distilled from evidence:

- The student model performs the trainable forward pass.
- The teacher model is `eval()` and frozen; its logits are truncated to the student vocabulary size if needed.
- Loss is `alpha * CE + (1 - alpha) * KL`, divided by accumulation steps.
- The KL term uses softmax/log-softmax at `temperature` and multiplies by `temperature ** 2`.
- If the student is MoE, the student auxiliary loss is added to CE; dense students do not add MoE aux loss.
- The evidence explicitly supports MoE-teacher to dense-student distillation and larger-teacher to smaller-student distillation.

Important flags:

| Flag | Default from evidence | Planning note |
|---|---:|---|
| `save_weight` | `full_dist` | Output prefix for distilled raw weights. |
| `data_path` | SFT-style JSONL | Same conversation format used by SFT; validate with the training-basics validator if available. |
| `from_student_weight` | `full_sft` | Starting student checkpoint. |
| `from_teacher_weight` | `full_sft` | Teacher checkpoint prefix; must exist and match teacher architecture flags. |
| `student_hidden_size`, `student_num_layers`, `student_use_moe` | `768`, `8`, `0` | Must match student checkpoint shape. |
| `teacher_hidden_size`, `teacher_num_layers`, `teacher_use_moe` | `768`, `8`, `1` | Must match teacher checkpoint shape. |
| `alpha` | `0.5` | Higher favors hard-label CE; lower favors teacher distribution. |
| `temperature` | `1.5` | Typical evidence range is about `1.0` to `2.0`; higher smooths teacher probabilities. |
| `learning_rate` | `5e-6` | Conservative continuation training rate. |
| `max_seq_len` | `340` | Increase only with memory budget. |

## DPO / RLHF plan

Choose DPO when the user has offline preference pairs and wants a stable low-VRAM preference-alignment step. DPO should not be used when the goal requires online exploration, tool execution, or ground-truth verification during rollout.

Core behavior distilled from evidence:

- The policy model and frozen reference model are initialized from the same `from_weight`.
- `chosen` and `rejected` sequences are concatenated in batch order; assistant response tokens are selected by a loss mask.
- The objective compares summed policy and reference log-prob ratios for chosen versus rejected.
- `beta` scales the preference logit and implicitly controls deviation from the reference model.
- No Reward Model, Critic, or rollout engine is used.

Important flags:

| Flag | Default from evidence | Planning note |
|---|---:|---|
| `save_weight` | `dpo` | Output prefix. |
| `data_path` | DPO JSONL | Must contain `chosen` and `rejected`; validate with the bundled validator. |
| `from_weight` | `full_sft` | Starting policy and reference checkpoint. |
| `beta` | `0.15` | Increase cautiously; too high can overfit preference contrasts. |
| `learning_rate` | `4e-8` | Evidence warns to keep this very small to reduce forgetting. |
| `batch_size` | `4` | Pair records expand to chosen/rejected tensors. |
| `max_seq_len` | `1024` | Truncates both chosen and rejected chat templates. |

## PPO / RLAIF plan

Choose PPO when the user needs on-policy response sampling and value-based advantages. It is heavier than GRPO/CISPO because it maintains an Actor and Critic in addition to a frozen Reference and external Reward Model.

Core behavior distilled from evidence:

- RLAIF records are prompts; the assistant target is generated online by the current Actor.
- Torch rollout produces one sampled response per prompt by default.
- Rewards combine length/format/repetition heuristics with the Reward Model score.
- A Critic model estimates token values; GAE uses `gamma` and `lam`.
- PPO uses ratio clipping, value clipping, KL reference penalty, optional early stop by approximate KL, and synchronized DDP KL checks to avoid deadlocks.
- `rollout_engine.update_policy(actor_model)` keeps the rollout model synchronized after saves or setup.

Important flags:

| Flag | Default from evidence | Planning note |
|---|---:|---|
| `save_weight` | `ppo_actor` | Actor output prefix for downstream inference. |
| `data_path` | RLAIF JSONL | Validate as `rlaif`. |
| `from_weight` | `full_sft` | Actor, Ref, and initial Critic source. |
| `reward_model_path` | External reward-model directory | Must be explicitly verified before training. |
| `learning_rate`, `critic_learning_rate` | `3e-7`, `5e-7` | Separate Actor/Critic rates. |
| `clip_epsilon` | `0.2` | PPO policy ratio clip. |
| `vf_coef` | `0.5` | Value loss coefficient. |
| `kl_coef` | `0.02` | Reference KL penalty coefficient. |
| `gamma`, `lam` | `1.0`, `0.95` | GAE controls. |
| `cliprange_value` | `0.2` | Value clipping range. |
| `ppo_update_iters` | `2` | Repeated updates per rollout batch. |
| `early_stop_kl` | `0.25` | Stops PPO minibatch updates safely when KL grows too high. |
| `mini_batch_size` | `2` | Controls PPO update memory. |
| `thinking_ratio` | `0.9` | Probability of prompt template opening thinking for RLAIF. |
| `debug_mode`, `debug_interval`, `debug_log_ratio` | off, `20`, off | Enable for first short run or KL/ratio diagnosis. |

## GRPO / CISPO plan

Choose GRPO/CISPO when the user wants online RLAIF without a Critic. Each prompt produces multiple candidate completions, rewards are grouped by prompt, and advantages are normalized within each group.

Core behavior distilled from evidence:

- `num_generations` controls the number of candidates per prompt.
- Rewards are reshaped to `[batch, num_generations]`; the per-sample advantage is `(reward - group_mean) / (group_std + 1e-4)`.
- Token-level KL is computed against the frozen Reference model.
- `loss_type=grpo` uses symmetric ratio clipping with `epsilon`.
- `loss_type=cispo` uses `min(ratio, epsilon_high).detach() * advantage * log_prob`, preserving a gradient path through log probability while clipping the importance weight.
- Group reward standard deviation near zero means the data/reward is not distinguishing candidates; the policy signal will be weak.

Important flags:

| Flag | Default from evidence | Planning note |
|---|---:|---|
| `save_weight` | `grpo` | Output prefix; CISPO in this route still usually uses this prefix unless overridden. |
| `data_path` | RLAIF JSONL | Validate as `rlaif`. |
| `from_weight` | `full_sft` | Policy and frozen Reference source. |
| `reward_model_path` | External reward-model directory | Required for default reward route. |
| `num_generations` | `6` | Lower for memory; higher for better group contrast. |
| `loss_type` | `cispo` | Choose `grpo` for classic GRPO or `cispo` for CISPO variant. |
| `beta` | `0.1` | Token KL penalty coefficient. |
| `epsilon` | `0.2` | GRPO clip range. |
| `epsilon_high` | `5.0` | CISPO upper importance-weight cap. |
| `thinking_ratio` | `0.9` | Prompt template thinking probability. |

## Agentic RL plan

Choose Agentic RL when the task objective requires generated tool calls, tool observations, re-planning, and delayed trajectory reward. Do not use plain RLAIF data for this route; Agentic data needs top-level `gt` and, for tool-use training, system-provided tools.

Core behavior distilled from evidence:

- Each record provides message history and optional tools; the final conversation message is treated as a placeholder and trimmed from the rollout prompt.
- Rollout can run up to three turns per generation in the evidence implementation.
- If the model emits `<tool_call>{...}</tool_call>`, the call is parsed, a deterministic mock tool is executed, and the observation is appended as a tool message before the next turn.
- Generated assistant tokens are optimized; tool-observation tokens are packed into context with response mask `0` so the policy is not trained to predict the environment output.
- Rewards include tool-call legality, number of valid calls versus `gt` count, final `gt` hits, tag closure penalties, unfinished penalties, repetition penalties, and optional Reward Model scoring for no-tool answers.
- Agentic uses the same grouped GRPO/CISPO objective family as the GRPO route; default evidence chooses CISPO.

Important flags:

| Flag | Default from evidence | Planning note |
|---|---:|---|
| `save_weight` | `agent` | Output prefix for Agentic raw weights. |
| `data_path` | Agent RL JSONL | Validate as `agent-rl`; do not pass plain RLAIF data. |
| `from_weight` | `full_sft` | Policy and frozen Reference source. |
| `reward_model_path` | External reward-model directory | Verify explicitly; missing path blocks default run. |
| `num_generations` | `4` | Generations per prompt/episode. |
| `loss_type` | `cispo` | Choices are `grpo` and `cispo`. |
| `beta`, `epsilon`, `epsilon_high` | `0.1`, `0.2`, `5.0` | KL and ratio controls. |
| `max_seq_len`, `max_gen_len`, `max_total_len` | `1024`, `768`, `2500` | Prompt, single-generation, and packed sequence caps. |
| `thinking_ratio` | `0.1` | Lower by default than RLAIF because thinking plus tool use can be unstable. |
| `debug_mode`, `debug_interval` | off, `20` | Enable to print contexts, completions, rewards, prompt length, and packed sequence length. |

## Rollout engine choice

Default to torch rollout for correctness and minimal dependencies. Choose SGLang only when the user has prepared a local CUDA-capable SGLang service, a tokenizer/model path compatible with that service, and a dedicated shared checkpoint path for weight synchronization.

| Engine | Use when | Required checks | Fallback |
|---|---|---|---|
| `torch` | First run, CPU/GPU debug, minimal dependencies, no service orchestration | MiniMind model can generate on selected device; sequence length fits memory | Reduce lengths/batch/generations if OOM |
| `sglang` | Throughput matters and a local service is already running | Health endpoint, `/generate` with logprobs, `/update_weights_from_disk`, dedicated shared path, CUDA capacity | Switch to `torch` and lower throughput expectations |

See [rollout-and-reward.md](rollout-and-reward.md) for update-policy and service details.

## Final evaluation handoff

Post-training weights are raw MiniMind checkpoints. After a run produces a candidate weight, do not evaluate tool-call serving here. Handoff to `inference-serving` with:

- weight prefix (`full_dist`, `dpo`, `ppo_actor`, `grpo`, or `agent`),
- `hidden_size`, `num_hidden_layers`, and `use_moe`,
- tokenizer/model artifact format,
- intended backend (`local` or OpenAI-compatible API), and
- evaluation focus, especially `eval_toolcall`-style cases for `agent` weights.

Agentic weights are expected to improve lightweight tool-use tasks but may degrade factual/general Q&A robustness. Ask the user which capability they want to optimize before treating an Agentic score improvement as overall model improvement.
