# Offline And Bandit Workflows

## Offline RL Pattern

Offline RL learns from static data rather than collecting new experience during training.

```python
import h5py
import torch
from agilerl.components.replay_buffer import ReplayBuffer
from agilerl.components.data import Transition
from agilerl.training.train_offline import train_offline

memory = ReplayBuffer(max_size=10000, device="cpu")
with h5py.File("dataset.h5", "r") as dataset:
    for idx in range(dataset["rewards"].shape[0] - 1):
        transition = Transition(
            obs=dataset["observations"][idx],
            action=dataset["actions"][idx],
            reward=dataset["rewards"][idx],
            next_obs=dataset["observations"][idx + 1],
            done=bool(dataset["terminals"][idx]),
        )
        transition = transition.unsqueeze(0)
        transition.batch_size = [1]
        memory.add(transition.to_tensordict())
```

Create the population and HPO objects as in classical off-policy workflows, then call `train_offline(...)`.

## Minari Datasets

AgileRL includes Minari utilities for loading and converting datasets. Treat remote Minari pulls as network operations; prefer local dataset smoke checks first.

## Contextual Bandit Pattern

A contextual bandit has one decision step per row.

```python
from agilerl.wrappers.learning import BanditEnv

env = BanditEnv(features, targets)
context_dim = env.context_dim
arms = env.arms
```

Then create a `NeuralUCB` or `NeuralTS` population with a `Box` observation space and `Discrete(arms)` action space.

## When To Choose Which

- Use offline RL when data contains transitions over time.
- Use contextual bandits when each row is a one-step context with a target/reward arm.
- Use online training when the agent can collect new environment experience.
