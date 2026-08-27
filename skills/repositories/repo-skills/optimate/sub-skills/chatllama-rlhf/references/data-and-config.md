# ChatLLaMA Data and Config

## Config sections

The YAML config is organized into four sections:

- `trainer_config`
- `actor_config`
- `critic_config`
- `reward_config`

The `Config` loader reads those sections, injects the active device/debug settings, and then builds the dataclass objects.

## Dataset schemas

- `actor_training_data.json`: list of objects with `user_input` and `completion`.
- `reward_training_data.json`: list of objects with `user_input`, `completion`, and `score`.
- `rlhf_training_data.json`: list of objects with `user_input` and `completion`; the source code may also carry a placeholder `score` field.

## Model and checkpoint layout

The model folder is split by role:

- `models/actor`
- `models/reward`
- `models/critic`
- `models/actor_rl`

Checkpoint state is stored beneath a `checkpoints/` subfolder with separate per-role paths.

## Supported model families

- Actor paths support LLaMA plus many Hugging Face causal language models such as OPT, BLOOM/BLOOMZ, GPT-Neo/GPT-J, GPT-2, CodeGen, and related families.
- Reward and critic paths currently use Hugging Face model families.
- Synthetic reward data generation can use OpenAI-style LLMs or Hugging Face alternatives, depending on the selected route.

## Config cautions

- `deepspeed_enable` and `accelerate_enable` should not both be true for the same stage.
- `critic_config` reuses the reward-model class and is distinguished by the `is_reward` flag.
- `BaseDataset.clean_dataset` trims examples that exceed the model sequence lengths before training.
