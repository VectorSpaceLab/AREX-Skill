# Classical Training Workflows

## On-Policy PPO Pattern

Use PPO when the learning policy and collection policy are the same.

```python
import torch
from agilerl.utils.utils import create_population, make_vect_envs
from agilerl.training.train_on_policy import train_on_policy
from agilerl.hpo.tournament import TournamentSelection
from agilerl.hpo.mutation import Mutations

INIT_HP = {
    "POP_SIZE": 6,
    "BATCH_SIZE": 128,
    "LR": 1e-3,
    "LEARN_STEP": 128,
    "GAMMA": 0.99,
    "GAE_LAMBDA": 0.95,
    "ACTION_STD_INIT": 0.6,
    "CLIP_COEF": 0.2,
    "ENT_COEF": 0.01,
    "VF_COEF": 0.5,
    "MAX_GRAD_NORM": 0.5,
    "TARGET_KL": None,
    "UPDATE_EPOCHS": 4,
    "CHANNELS_LAST": False,
}
NET_CONFIG = {"encoder_config": {"hidden_size": [32, 32]}, "head_config": {"hidden_size": [32]}}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
env = make_vect_envs("CartPole-v1", num_envs=4)
pop = create_population(
    algo="PPO",
    observation_space=env.single_observation_space,
    action_space=env.single_action_space,
    net_config=NET_CONFIG,
    INIT_HP=INIT_HP,
    population_size=INIT_HP["POP_SIZE"],
    num_envs=4,
    device=device,
)
```

Then add `TournamentSelection`, `Mutations`, and call `train_on_policy(...)` with `wb=False` for local smoke runs.

## Off-Policy Pattern

Use off-policy algorithms when learning from replayed experiences.

```python
import torch
from agilerl.components.replay_buffer import ReplayBuffer
from agilerl.utils.utils import create_population, make_vect_envs
from agilerl.training.train_off_policy import train_off_policy

INIT_HP = {
    "DOUBLE": True,
    "BATCH_SIZE": 128,
    "LR": 1e-3,
    "GAMMA": 0.99,
    "LEARN_STEP": 1,
    "TAU": 1e-3,
    "POP_SIZE": 4,
}
NET_CONFIG = {"encoder_config": {"hidden_size": [32, 32]}, "head_config": {"hidden_size": [32, 32]}}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
env = make_vect_envs("CartPole-v1", num_envs=4)
pop = create_population(
    algo="DQN",
    observation_space=env.single_observation_space,
    action_space=env.single_action_space,
    net_config=NET_CONFIG,
    INIT_HP=INIT_HP,
    population_size=INIT_HP["POP_SIZE"],
    num_envs=4,
    device=device,
)
memory = ReplayBuffer(max_size=10000, device=device)
```

Call `train_off_policy(...)` only after memory, tournament, and mutation objects are configured.

## Recurrent Variants

- Use recurrent demo/config patterns when observations are partially observable or sequence state is required.
- Include LSTM fields in `net_config` and verify hidden-state shapes before training.
- Recurrent PPO and off-policy variants are more sensitive to sequence length, batch shape, and environment reset behavior.

## Full Training Checklist

- Wrap top-level vector-env code in `if __name__ == "__main__":` when multiprocessing can occur.
- Keep `wb=False` unless W&B is configured.
- Pick a target score and max steps appropriate to the environment.
- Start with small `POP_SIZE`, `num_envs`, and `max_steps` for smoke runs.
- Validate `observation_space` and `action_space` match the algorithm family.
- Use CPU smoke checks before GPU training unless the task explicitly requires CUDA.
