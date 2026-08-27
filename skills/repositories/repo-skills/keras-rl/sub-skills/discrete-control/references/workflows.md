# Discrete-control workflows

These workflows are build/compile-focused. They intentionally avoid default long training, visualization, external downloads, ROM setup, and source-checkout assumptions.

## Decision guide

| If the task says... | Prefer... | Why |
| --- | --- | --- |
| "DQN", "CartPole DQN", replay, target network | `DQNAgent` + `SequentialMemory` | Standard value-based off-policy discrete control. |
| "Double DQN" | `DQNAgent(enable_double_dqn=True)` | Reduces max-action overestimation by decoupling selection/evaluation. |
| "Dueling DQN" | `DQNAgent(enable_dueling_network=True, dueling_type='avg')` | Learns state value and action advantage before combining into Q values. |
| "SARSA", on-policy, no replay | `SARSAAgent` | Updates from the action actually selected by the behavior policy. |
| "CEM", cross entropy method, episode parameter memory | `CEMAgent` + `EpisodeParameterMemory` | Searches over model parameters using elite episode returns. |
| "Atari processor", frame stacking, reward clipping | DQN concepts here, processor lifecycle elsewhere | This sub-skill provides reference-only Atari preprocessing notes, not a full runner. |

## Shared model pattern for low-dimensional discrete tasks

For CartPole-like vector observations and `window_length=1`, use a model whose input shape includes the memory window and whose final output width equals `nb_actions`.

```python
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten

model = Sequential()
model.add(Flatten(input_shape=(1,) + observation_shape))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(nb_actions))
model.add(Activation('linear'))
```

For `window_length > 1`, change the first dimension in `input_shape` to match the memory window. If the environment returns images or multi-modal observations, keep the same final `Dense(nb_actions)` contract but route processor implementation details to the core-extension-and-logging sub-skill.

## DQN build and compile

```python
from keras.optimizers import Adam
from rl.agents.dqn import DQNAgent
from rl.memory import SequentialMemory
from rl.policy import BoltzmannQPolicy

memory = SequentialMemory(limit=50000, window_length=1)
policy = BoltzmannQPolicy()

dqn = DQNAgent(
    model=model,
    nb_actions=nb_actions,
    memory=memory,
    policy=policy,
    nb_steps_warmup=10,
    target_model_update=1e-2,
)
dqn.compile(Adam(lr=1e-3), metrics=['mae'])
```

Operational notes:

- `target_model_update=1e-2` is a soft target update coefficient, not an update period.
- Use an integer such as `10000` for hard target updates every N steps.
- Increase `nb_steps_warmup` for larger replay windows, large batch sizes, or pixel observations.
- For a strict build smoke, stop after `compile()` and inspect `dqn.compiled`, `dqn.model.output_shape`, and the existence of `dqn.target_model`.

## Double DQN

Double DQN is the same construction with one explicit flag:

```python
double_dqn = DQNAgent(
    model=model,
    nb_actions=nb_actions,
    memory=memory,
    policy=policy,
    enable_double_dqn=True,
    nb_steps_warmup=10,
    target_model_update=1e-2,
)
double_dqn.compile(Adam(lr=1e-3), metrics=['mae'])
```

Use this when overestimation bias matters. The model shape and memory requirements are unchanged.

## Dueling DQN

```python
dueling_dqn = DQNAgent(
    model=model,
    nb_actions=nb_actions,
    memory=memory,
    policy=policy,
    enable_dueling_network=True,
    dueling_type='avg',
    nb_steps_warmup=10,
    target_model_update=1e-2,
)
dueling_dqn.compile(Adam(lr=1e-3), metrics=['mae'])
```

Dueling-specific cautions:

- Allowed `dueling_type` values are `avg`, `max`, and `naive`; start with `avg`.
- The agent takes the second-to-last layer of the supplied model and creates a value/advantage head internally.
- Even though the final head is replaced, the supplied model is still validated first, so the original final layer must output exactly `nb_actions` units.

## SARSA build and compile

```python
from keras.optimizers import Adam
from rl.agents.sarsa import SARSAAgent
from rl.policy import BoltzmannQPolicy

policy = BoltzmannQPolicy()
sarsa = SARSAAgent(
    model=model,
    nb_actions=nb_actions,
    policy=policy,
    nb_steps_warmup=10,
)
sarsa.compile(Adam(lr=1e-3), metrics=['mae'])
```

SARSA notes:

- Do not create or pass replay memory.
- The model still predicts Q values for all actions.
- Use the same final `Dense(nb_actions)` and linear activation pattern as DQN.
- Because SARSA updates from the next action selected by its current policy, changing `policy` changes learning behavior directly.

## CEM build and compile

CEM uses an episode-level parameter memory and compile has no optimizer argument.

```python
from rl.agents.cem import CEMAgent
from rl.memory import EpisodeParameterMemory

cem_model = Sequential()
cem_model.add(Flatten(input_shape=(1,) + observation_shape))
cem_model.add(Dense(nb_actions))
cem_model.add(Activation('softmax'))

memory = EpisodeParameterMemory(limit=1000, window_length=1)
cem = CEMAgent(
    model=cem_model,
    nb_actions=nb_actions,
    memory=memory,
    batch_size=50,
    nb_steps_warmup=2000,
    train_interval=50,
    elite_frac=0.05,
)
cem.compile()
```

CEM notes:

- Use `EpisodeParameterMemory`, not `SequentialMemory`.
- Keep `batch_size * elite_frac >= 1`.
- `noise_ampl` and `noise_decay_const` add a minimum standard deviation schedule for noisy CEM variants.
- CEM chooses model weights at episode boundaries; very short smoke training may not prove learning.

## Policy and memory recipes

| Recipe | Use |
| --- | --- |
| `BoltzmannQPolicy()` | Good default for low-dimensional examples where smooth Q-based exploration is useful. |
| `EpsGreedyQPolicy(eps=.1)` | Simple exploration and easy deterministic testing by later setting `eps = 0`. |
| `LinearAnnealedPolicy(EpsGreedyQPolicy(), attr='eps', value_max=1., value_min=.1, value_test=.05, nb_steps=...)` | Atari-style long training where exploration decays over many steps. |
| `SequentialMemory(limit=..., window_length=1)` | DQN replay for vector observations. |
| `SequentialMemory(limit=..., window_length=4)` | Frame-stacked Atari-style DQN; pair with image preprocessing and a compatible convolutional model. |
| `EpisodeParameterMemory(limit=..., window_length=1)` | CEM only. |

## Safe smoke helper

Run the bundled helper before expensive training:

```bash
python scripts/build_discrete_agents_smoke.py --agent all --backend-note
```

Examples:

```bash
python scripts/build_discrete_agents_smoke.py --agent dqn
python scripts/build_discrete_agents_smoke.py --agent double-dqn --policy eps-greedy
python scripts/build_discrete_agents_smoke.py --agent dueling-dqn --dueling-type max
python scripts/build_discrete_agents_smoke.py --agent cem
```

The helper defaults to compile/build only. If a tiny lifecycle probe is needed after compile, pass a very small `--train-steps` value; lifecycle interpretation and callback behavior belong to the core-extension-and-logging sub-skill.
