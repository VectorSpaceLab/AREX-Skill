# Offline And Bandit API Reference

## Offline Algorithms And Training

- `agilerl.algorithms.cqn.CQN`
- `agilerl.algorithms.ilql.ILQL`
- `agilerl.training.train_offline.train_offline(...)`

## Bandit Algorithms And Training

- `agilerl.algorithms.neural_ucb_bandit.NeuralUCB`
- `agilerl.algorithms.neural_ts_bandit.NeuralTS`
- `agilerl.training.train_bandits.train_bandits(...)`
- `agilerl.wrappers.learning.BanditEnv`

## Replay And Data Components

- `agilerl.components.replay_buffer.ReplayBuffer`
- `agilerl.components.data.Transition`
- `agilerl.components.data.to_tensordict`
- `agilerl.components.sampler.Sampler`
- `agilerl.utils.minari_utils.load_minari_dataset`
- `agilerl.utils.minari_utils.minari_to_agile_buffer`
- `agilerl.utils.minari_utils.minari_to_agile_dataset`

## Validation Targets

- For offline RL, validate transition fields and replay samples.
- For bandits, validate `context_dim`, `arms`, observation `Box`, and action `Discrete` space.
- For both, validate `INIT_HP`, HPO config, and logging flags before full training.
