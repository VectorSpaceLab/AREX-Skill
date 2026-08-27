# ChatLLaMA API Reference

## Public config entry points

- `Config(path, device=None, debug=False)`
- `ConfigTrainer`
- `ConfigActor`
- `ConfigReward`
- `ConfigCritic` (alias of `ConfigReward`)

## Public training and data entry points

- `BaseDataset.clean_dataset(config)`
- `BaseDataset.sort_conversation(conversations, only_input=False, reverse=True, shuffle=True)`
- `BaseDataset.take_n_samples(conversations, n)`
- `ActorTrainer(config)`
- `RewardTrainer(config)`
- `RLTrainer(config)`
- `download_dataset.py`: `AnthropicRLHF`, `StanfordNLPSHPDataset`
- `generate_rewards.py`: `ScoreGenerator(llm_model, llm_temperature, llm_max_tokens, reward_template)`

## Model and path helpers

- `ModelLoader.get_model_path(config, is_checkpoint=False, current_epoch=None, current_step=None, ...)`
- `ModelLoader.check_model_path(config, is_checkpoint=False, current_epoch=None, current_step=None)`
- `ModelLoader.init_critic_from_reward(config)`
- `ModelLoader.get_training_stats_path(config)`

## Training orchestration

- `main.py` supports `--type ALL|RL|ACTOR|REWARD` and optional `--actor`, `--reward`, and `--local_rank` overrides.
- `change_tokenization` and `check_model_family` are core helpers inside the RLHF trainer path.

## Note

The package's public training flow is config-driven. The `Config` loader expects the four top-level YAML sections that match the source artifacts: trainer, actor, critic, and reward.
