# ColossalChat / Coati Notes

ColossalChat implements LLM alignment and RLHF-style workflows through the `coati` package and application scripts.

## Main workflow families

- Supervised fine-tuning (SFT).
- Reward model training.
- PPO / reinforcement learning from human feedback.
- Direct Preference Optimization (DPO).
- Simple Preference Optimization (SimPO).
- Odds Ratio Preference Optimization (ORPO).
- Kahneman-Tversky Optimization (KTO).
- Group Relative Policy Optimization (GRPO).
- LoRA, quantization, and inference-after-training support.

## Command anatomy

Application shell scripts usually combine model or pretrained checkpoint path, dataset path and data format, strategy or plugin choice, LoRA/quantization flags, batch sizes, logging/checkpoint output directories, and GPU/process count through `torchrun` or `colossalai run`.

Do not run the scripts unchanged. Replace all model, dataset, output, and GPU settings with user-specific values and confirm dependencies first.

## Dependency cautions

ColossalChat requirements include Transformers, datasets, PEFT/LoRA-style packages, flash-attn in some environments, wandb/tensorboard, and math-verification utilities. These can be expensive or incompatible with other app stacks. Use an isolated app environment.
