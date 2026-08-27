---
name: core-training
description: "Choose, instantiate, and troubleshoot TRL stable post-training
  trainers: SFT, DPO, GRPO, Reward, and RLOO."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core TRL Training

Use this sub-skill when the task is to select or wire up stable TRL post-training trainers, build trainer objects, set the main config/model arguments, attach reward functions, or debug trainer-specific setup errors.

## Route by Training Objective

- **SFTTrainer**: supervised fine-tuning on text, prompt-completion, or conversational examples; start here for instruction tuning and formatting/loss masking questions.
- **DPOTrainer**: preference optimization from paired `chosen`/`rejected` answers; use after an SFT-style model exists and no online generation rewards are needed.
- **RewardTrainer**: train a sequence-classification reward model from `chosen`/`rejected` comparisons; use before RLHF-style training when rewards should come from a model.
- **GRPOTrainer**: online RL from generated completions scored by one or more reward functions or reward models; use for grouped generations and reward shaping.
- **RLOOTrainer**: online RL with leave-one-out baselines; use when each prompt should produce multiple completions and rewards are compared within that prompt group.

## Quick References

- Trainer signatures and default highlights: [references/trainer-api-reference.md](references/trainer-api-reference.md)
- End-to-end trainer skeletons: [references/workflows.md](references/workflows.md)
- Setup and runtime failures: [references/troubleshooting.md](references/troubleshooting.md)
- Local signature helper: [scripts/inspect_trainer_config.py](scripts/inspect_trainer_config.py)

## Boundaries

- Route detailed dataset conversion, chat-template normalization, and reward-function data plumbing to `../data-and-rewards/`.
- Route CLI command construction, YAML recipes, and launcher flags to `../cli-and-configs/`.
- Route vLLM, DeepSpeed, FSDP, PEFT scaling, quantization, and memory-distributed execution to `../scaling-and-backends/`.
- Route experimental trainers, tools/environments, and non-stable APIs to `../experimental-and-environments/`.

## First Checks Before Instantiating

1. Pick the trainer from the objective and dataset shape, then verify the required columns in [references/trainer-api-reference.md](references/trainer-api-reference.md).
2. Create the matching config class rather than passing raw `TrainingArguments`, except for simple SFT cases where `SFTTrainer` can upgrade `TrainingArguments`.
3. Pass a model id string for automatic loading, or pass an already loaded model and keep `model_init_kwargs` out of the config.
4. Keep `trust_remote_code=False` unless the target model explicitly needs custom code.
5. Add `peft_config` only when PEFT is installed and the task actually needs adapter training; route scaling details to `../scaling-and-backends/`.
