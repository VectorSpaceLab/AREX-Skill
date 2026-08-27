---
name: reasoning-agent-workflows
description: "Enables future agents to operate RLinf reasoning, agentic RL,
  coding online RL, rollout backend, SFT, reward, and service workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RLinf reasoning and agent workflow router

Use this sub-skill when a task involves RLinf text reasoning, VLM reasoning, agentic RL, coding online RL, SearchR1/rStar2/WideSeek-R1 style tool workflows, AgentLightning, rollout backends, SFT/VLM SFT, or reward/service integration.

## Route first

- Install, Ray startup, node groups, generic placement syntax, and cluster health belong to the `setup-and-cluster` sub-skill.
- Embodied simulator, robot, action-space, and VLA environment details belong to `embodied-workflows`.
- Metrics, checkpoints, standalone evaluation operations, profiling, CI selection, and runtime log triage belong to `operations-evaluation-debugging`.
- Registering a new model, environment, reward, algorithm, runner, worker, or tool parser belongs to `extension-development`.

## Operating loop

1. Classify the workflow: math/VQA reasoning RL, PPO with critic, multi-turn agentic RL, coding online RL, AgentLightning, SFT/VLM SFT, or reward-model training.
2. Inspect the user-supplied YAML with [`scripts/inspect_agentic_config.py`](scripts/inspect_agentic_config.py) before launching any expensive run.
3. Verify prerequisites: model/tokenizer paths, dataset format, required service endpoints, judge/search/code-execution credentials, and rollout backend memory budget.
4. Build or edit only the user’s target config/launcher. Use the bundled references below rather than asking future agents to open source examples or docs.
5. Escalate to setup/operations/extension sub-skills for out-of-scope cluster, evaluation, or source-code-extension work.

## Bundled references

- [`references/reasoning-agent-recipes.md`](references/reasoning-agent-recipes.md) — recipe concepts for math/VQA GRPO/PPO, coding online RL, AgentLightning, SearchR1, rStar2, and WideSeek-R1.
- [`references/rollout-backends-and-data.md`](references/rollout-backends-and-data.md) — SGLang/vLLM backend choices, actor/rollout/inference/reward data flow, dataset schemas, and service prerequisites.
- [`references/sft-offline-reward.md`](references/sft-offline-reward.md) — SFT/VLM SFT, offline code validation, LoRA, reward-model training, and reward registry intersections.
- [`references/troubleshooting.md`](references/troubleshooting.md) — reasoning/agentic-specific failure triage for sequence lengths, logprobs, services, backend OOMs, data loading, and AgentLightning.

## Safe helper

- [`scripts/inspect_agentic_config.py`](scripts/inspect_agentic_config.py) reads one or more YAML files and reports task type, actor/rollout backends, length budget, algorithm settings, external services, and risky missing fields. It is static and non-mutating.

Evidence basis: distilled from RLinf v0.4.0 public configuration examples, English guides, runner/worker source, reasoning/VLM dataset loaders, reward registry, agent tool loops, rollout workers, and e2e configuration families.
