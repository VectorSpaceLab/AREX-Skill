# Trainer Selection

## Purpose

Use this guide when a user asks which post-training trainer to use or how the trainers differ.

## Quick Choice Table

| Trainer | Import path | Main mutation | Best for | Avoid when |
| --- | --- | --- | --- | --- |
| PPO | `from palm_rlhf_pytorch import RLHFTrainer, ActorCritic` | Actor and critic/value updates | Standard RLHF and the most direct match to the README example | You need a critic-free algorithm or a newer post-training variant |
| GRPO | `from palm_rlhf_pytorch import grpo` then `grpo.RLHFTrainer` | Actor-only training with group-relative reward normalization | Repeated sampling per prompt, critic-free post-training, and SPO/Dr. GRPO/MaxRL-style experiments | You want the classic PPO critic/value pipeline |
| TPO | `from palm_rlhf_pytorch import tpo` then `tpo.RLHFTrainer` | Actor training against target `q` distributions | Distribution-matching style post-training with a replay buffer | You do not want a memmap replay buffer or target-Q logic |
| FlowRL | `from palm_rlhf_pytorch import flowrl` then `flowrl.FlowRLTrainer` | Actor plus partition function | Flow-balance / reward-distribution matching style training | You do not want the extra partition-function model |

## Selection Guidance

- Choose PPO when the user says "RLHF", "reward model + policy", or names `RLHFTrainer` without a newer algorithm.
- Choose GRPO when the user wants critic-free training with multiple reward samples per prompt.
- Choose TPO when the user wants replay-buffer-based target distributions or references target policy optimization.
- Choose FlowRL when the user wants flow balance, reward-distribution matching, or a partition function model.

## What Each Trainer Stores Or Mutates

- **PPO**: actor, critic, reward model, actor optimizer, critic optimizer, and PPO memories.
- **GRPO**: actor, reward model, actor optimizer, and grouped reward advantages.
- **TPO**: actor, reward model, actor optimizer, memmap replay buffer, and target distributions.
- **FlowRL**: actor, reward model, actor optimizer, partition function, and partition-function optimizer.

## Prompt Input Rule

Every trainer requires exactly one of:

- `prompts`
- `prompts_path`
- `prompt_token_ids`

If the user supplies raw text prompts, they also need a tokenizer that returns token-id tensors.

## Tiny Smoke Rule

Use the bundled tiny smoke script for verification, not the original source example script. The tiny smoke path is the safe way to confirm trainer wiring, prompt input shape, and one bounded update step.
