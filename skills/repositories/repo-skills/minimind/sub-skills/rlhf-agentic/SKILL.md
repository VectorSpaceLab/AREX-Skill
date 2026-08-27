---
name: rlhf-agentic
description: "Guides future agents choosing MiniMind distillation, DPO, PPO,
  GRPO/CISPO, and Agentic RL post-training workflows with data validation,
  rollout, reward, and evaluation routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MiniMind RLHF, RLAIF, Distillation, and Agentic RL Router

Use this sub-skill when the task is about MiniMind post-training after core SFT: white-box teacher/student distillation, preference optimization, online RLAIF, GRPO/CISPO, or multi-turn Agentic RL with tool-use rewards.

## Fast routing

1. Classify the route before planning a long job:
   - **White-box distillation**: use when a teacher checkpoint should guide a student through `CE + KL` token-distribution matching.
   - **DPO / RLHF**: use when data has static preference pairs, `chosen` versus `rejected`, and no online rollout or reward model is needed.
   - **PPO / RLAIF**: use when the policy should sample responses online and optimize with Actor, Critic, Reference, and Reward Model components.
   - **GRPO or CISPO / RLAIF**: use when each prompt should produce grouped generations and use group-relative advantages without a Critic.
   - **Agentic RL**: use when the policy must perform multi-turn tool calls, observe tool outputs, validate `gt`, and optimize delayed trajectory reward.
2. Read the nearest bundled reference instead of reopening source evidence:
   - [workflows.md](references/workflows.md): route selection, safe configuration plans, command-shape planning, key flags, output weight names, and handoff decisions.
   - [data-formats.md](references/data-formats.md): DPO, RLAIF, and Agentic RL JSONL schemas, message/tool/`gt` constraints, and validation examples.
   - [rollout-and-reward.md](references/rollout-and-reward.md): torch versus optional SGLang rollout behavior, Reward Model use, Agentic tool reward, response masks, and context packing.
   - [troubleshooting.md](references/troubleshooting.md): failure diagnosis for reward models, external checkpoints, SGLang, DDP, invalid JSON/tool calls, OOM, debug flags, and reward hacking.
3. Validate before expensive training:
   - Run [scripts/validate_post_training_jsonl.py](scripts/validate_post_training_jsonl.py) on DPO, RLAIF, or Agentic RL JSONL files.
   - Run [scripts/reward_toolcall_smoke.py](scripts/reward_toolcall_smoke.py) on synthetic or user-supplied Agentic tool-call text to check parser, mock-tool, `gt`, reward, and optional SGLang dry checks.

## Scope boundaries

This sub-skill owns post-training route selection and RL/RLAIF/Agentic planning only. Route tokenizer training, pretraining, SFT, LoRA training, and base checkpoint preparation to `training-basics`. Route API serving, model conversion/export, and final tool-call evaluation operation to `inference-serving` after a post-training weight exists.

Do not use this sub-skill to launch API servers, run interactive evaluation, train tokenizers, or design LoRA/SFT data. Use it to prepare a safe plan, validate data and rewards, and decide what resulting weight should be handed to inference.

## Minimum safe procedure

For every post-training request:

1. Confirm the starting checkpoint family, hidden size, layer count, dense versus MoE setting, and whether the goal is preference alignment, reward-model optimization, group-relative improvement, or Agentic tool use.
2. Validate the JSONL schema with the bundled validator. Refuse to launch a long run if required keys, tool schemas, or `gt` entries are malformed.
3. Check external prerequisites explicitly: starting policy weights, teacher weights for distillation, reward-model directory for PPO/GRPO/Agent, and optional SGLang service if selected.
4. Prefer the torch rollout engine unless the user has already prepared a local SGLang service and a dedicated shared checkpoint path.
5. Keep debug flags available for first runs, especially `debug_mode`, `debug_interval`, and PPO `debug_log_ratio`.
6. After training, hand the produced raw weight prefix (`full_dist`, `dpo`, `ppo_actor`, `grpo`, or `agent`) and architecture settings to `inference-serving` for conversion, serving, or `eval_toolcall`-style validation.

## Verification candidates for later

Do not treat these as already run by this sub-skill draft. Recommended later checks are:

- Import all MiniMind RL training modules in a prepared inspection environment.
- Run the bundled JSONL validator on tiny positive and negative DPO/RLAIF/Agentic fixtures.
- Run the bundled reward/tool-call smoke helper with a stub reward score and at least one malformed `<tool_call>` case.
- When an `agent` weight exists, route to `inference-serving` for a tool-call evaluation run using the agent weight and the MiniMind architecture flags that produced it.
