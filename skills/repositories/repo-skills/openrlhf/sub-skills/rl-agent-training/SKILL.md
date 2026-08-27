---
name: rl-agent-training
description: "Plan and adapt OpenRLHF PPO/Ray/vLLM reinforcement-learning runs,
  including REINFORCE++/baseline, GRPO/RLOO/Dr.GRPO, DAPO-style filtering, async
  and partial rollout, custom rewards, multi-turn agents, VLM agents, and
  OpenAI-compatible agent executors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenRLHF RL Agent Training

Use this sub-skill when the task is to configure, modify, or troubleshoot OpenRLHF RL training through `python -m openrlhf.cli.train_ppo_ray`, especially with Ray, vLLM, PPO-family algorithms, custom reward functions, or agent executors.

## Route first

- For SFT, reward-model, DPO/IPO/KTO, or offline preference training, use the supervised-preference-training sub-skill instead.
- For dataset schemas, chat templates, `--data.input_key`, `--data.label_key`, image keys, or prompt preprocessing, use the data-preparation sub-skill first, then return here for RL flags.
- For package installation, Ray cluster launch, NCCL/CUDA environment, Slurm/container setup, reward-model serving, or checkpoint utility operations, use operations-and-utilities.
- Treat full RL shell scripts as GPU/distributed/expensive examples. Do not run them unless the user explicitly asks and the environment is ready.

## Start here

1. Identify the execution mode: synchronous hybrid engine, async training, async partial rollout, single-turn reward, multi-turn agent, VLM agent, or OpenAI-compatible agent server executor.
2. Choose the algorithm and advantage estimator: PPO uses `gae`; REINFORCE++ uses `reinforce`; RLOO uses `rloo`; REINFORCE++-baseline uses `reinforce_baseline`; GRPO uses `group_norm`; Dr.GRPO uses `dr_grpo`.
3. Check mandatory relationships before writing commands: group estimators need `--rollout.n_samples_per_prompt > 1`; partial rollout needs `--train.async_enable`; VLM training must avoid critic/packing; dynamic filtering needs multi-sample rollout plus a reward source.
4. Use the references in this sub-skill for detailed flags, protocols, and failure handling.

## References

- `references/rl-workflows.md`: workflow choices and representative command fragments for PPO, REINFORCE++/baseline, GRPO/RLOO/Dr.GRPO, DAPO-style filtering, async, partial rollout, VLM, and OpenAI-compatible agent execution.
- `references/agent-functions.md`: contracts for `reward_func.py`, math reward functions, `MultiTurnAgentExecutor`, VLM multi-turn agents, and OpenAI-compatible executor customization.
- `references/cli-reference.md`: important `train_ppo_ray` flag groups and validation rules.
- `references/troubleshooting.md`: rollout, Ray/vLLM placement, NCCL, reward URL, import path, agent protocol, VLM media, KL/advantage, off-policy, and OOM troubleshooting.

## Helper script

Use `scripts/create_reward_or_agent_template.py` to create small standalone starter files:

```bash
python skills/openrlhf/sub-skills/rl-agent-training/scripts/create_reward_or_agent_template.py \
  --kind math-reward \
  --output reward_func.py
```

Supported kinds are `reward`, `math-reward`, `multiturn`, and `vlm-multiturn`. The generated files are templates distilled from OpenRLHF examples and are meant to be edited before training.
