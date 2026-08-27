# LLM Fine-Tuning Workflows

## Reasoning RL

Use GRPO-family algorithms for reasoning tasks with verifiable rewards. Typical ingredients:

- A model/tokenizer compatible with Transformers/PEFT/vLLM choices.
- A prompt dataset or environment that yields reasoning prompts.
- A reward function or environment that can score completions.
- Optional rollout backend such as vLLM for generation.
- Training config for batch sizes, generation count, KL/loss settings, and checkpointing.

## Preference Optimization

Use DPO or preference-oriented trainers when data contains chosen/rejected responses or preference pairs. Validate dataset columns and tokenizer formatting before training.

## Multi-Turn Training

Use AgileRL LLM environments/wrappers for multi-turn interactions. Validate:

- Conversation state shape.
- Chat template behavior.
- Termination conditions.
- Reward assignment per turn or trajectory.
- Rollout backend memory needs.

## SFT

Use SFT for supervised fine-tuning when target responses are known. It may be a prerequisite before RL post-training.

## HPO With LLMs

AgileRL supports evolutionary HPO concepts for LLM workflows, but do not assume architecture mutation is available for `LLMAlgorithm` objects. Focus mutation on supported training hyperparameters and keep model architecture fixed unless documentation and hardware explicitly support otherwise.

## Dry-Run Pattern

1. Check optional packages with `scripts/inspect_llm_dependencies.py`.
2. Validate dataset columns and a tiny tokenizer batch.
3. Validate reward function on one prompt/completion pair.
4. Validate config parsing and checkpoint paths.
5. Only then run model loading, vLLM, DeepSpeed, or training.
