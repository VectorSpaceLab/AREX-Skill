---
name: rl-and-rewards
description: "Guides agents configuring Axolotl GRPO, EBFT, custom reward
  functions, vLLM training servers, NeMo Gym, Hatchery, and async online RL
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RL and Rewards

Use this sub-skill when the task involves Axolotl online RL or reward-driven training: GRPO, GDPO-style reward aggregation, custom reward functions, `axolotl vllm-serve` for training, EBFT feature-matching rewards, NeMo Gym environment rewards, Hatchery-style remote RL flows, or async rollout debugging.

## Route By Task

- For GRPO configs, vLLM serving, async prefetch, replay, re-roll, and importance sampling, read [references/grpo.md](references/grpo.md).
- For EBFT structured or strided feature-matching runs, read [references/ebft.md](references/ebft.md).
- For reward function signatures, deterministic checks, multiple rewards, rollout functions, NeMo Gym rewards, and Hatchery reward hooks, read [references/reward-functions.md](references/reward-functions.md).
- For symptom-driven fixes around rewards, vLLM, async rollouts, EBFT mode selection, and resource constraints, read [references/troubleshooting.md](references/troubleshooting.md).
- Before training, validate a local reward function with [scripts/validate_reward_function.py](scripts/validate_reward_function.py): `python scripts/validate_reward_function.py rewards.py:accuracy_reward`.

## Quick Workflow

1. Classify the method first: `rl: grpo` for programmatic verifiers or environment rewards, `rl: ebft` for feature matching against ground-truth completions, and route DPO/KTO/ORPO/SimPO preference data to `preference-tuning`.
2. For GRPO, define the YAML, reward module, and vLLM plan together; `trl.reward_funcs`, `trl.num_generations`, `trl.max_completion_length`, `trl.use_vllm`, and `vllm.host`/`vllm.port` must agree.
3. For EBFT, choose `ebft.mode` before copying settings: structured mode uses prompt plus `ground_truth` and usually vLLM, while strided mode uses tokenized document anchors and does not require vLLM.
4. Run local deterministic reward checks before `axolotl train`; then use `axolotl preprocess config.yaml --debug` only for data/tokenization visibility and `axolotl train config.yaml` only after the user accepts runtime cost.
5. For server-backed RL, start or verify the generation/environment services before training; `axolotl vllm-serve config.yaml` must serve the same base model as the training config.

## Boundaries

- This sub-skill owns GRPO/GDPO online RL, reward functions, vLLM serving relationships, async rollout features, EBFT structured/strided setup, NeMo Gym reward routing, Hatchery reward hooks, and safe local reward validation.
- Route static DPO, KTO, ORPO, SimPO, reward-model, and process-reward-model preference workflows to `preference-tuning`.
- Route generic dataset format mapping, `chat_template`, schema discovery, and YAML-only validation to `data-and-configs`.
- Route cluster launch, DeepSpeed/FSDP tuning, GPU placement, and throughput engineering to `distributed-and-performance`.
- Route model architecture quirks, tokenizer templates, LoRA/QLoRA target modules, and adapter loading to `model-loading-and-adapters`.
- Route CLI mechanics, fetch/docs commands, inference, and merge-lora operations to `cli-and-operations`.

## Evidence Notes

This guidance is distilled from Axolotl GRPO, EBFT, vLLM serving, RLHF, schema, integration, example, and unit-test evidence. It does not claim live training, vLLM, GPU, model-loading, or environment-service verification.
