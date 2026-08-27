# Core Model / Algorithm / Agent API reference

PARL structures an RL application around three layers:

- **Model**: the neural network forward part, such as a policy network, Q-value function, critic, or target network.
- **Algorithm**: the training mechanism that owns one or more models, optimizers, losses, target-network synchronization, and `predict` / `learn` / optional `sample` methods.
- **Agent**: the environment-facing data bridge that converts observations/actions/rewards, calls the algorithm, exposes `predict` / `sample` / `learn`, and saves or restores model parameters.

Keep these responsibilities separate. If a task needs full DQN/DDPG/PPO/SAC recipe selection, route to `../../algorithm-recipes/`; this reference covers the framework primitives only.

## Backend alias classes

After backend selection, the public aliases resolve to one backend implementation:

| Public alias | Torch backend | Paddle 2.x backend | legacy Fluid backend |
| --- | --- | --- | --- |
| `parl.Model` | `torch.nn.Module` + PARL weight helpers | `paddle.nn.Layer` + PARL weight helpers | static-graph PARL model with `model_id` and `parl.layers` tracking |
| `parl.Algorithm` | Owns a Torch `parl.Model`; `learn` and `predict` are abstract user methods | Owns a Paddle `parl.Model`; `learn`, `predict`, and `sample` are abstract user methods | Owns Fluid models/programs; static graph style |
| `parl.Agent` | Owns a `parl.Algorithm`; includes `save`, `restore`, `train`, `eval` | Owns a `parl.Algorithm`; includes `save`, `restore`, `save_inference_model`, `train`, `eval` | Builds and executes Fluid programs; includes directory-based `save` / `restore` |

## Model implementation patterns

### Torch model

```python
import parl
import torch
import torch.nn as nn

class QModel(parl.Model):
    def __init__(self, obs_dim, act_dim):
        super().__init__()
        self.fc = nn.Linear(obs_dim, act_dim)

    def forward(self, obs):
        return self.fc(obs)

    def value(self, obs):
        return self.forward(obs)
```

Torch `parl.Model` instances support ordinary `torch.nn.Module` behavior. PARL adds:

- `sync_weights_to(target_model, decay=0.0)`
- `get_weights()` returning a dict of NumPy arrays from `state_dict()`
- `set_weights(weights)` loading a dict of NumPy arrays back into the state dict

### Paddle 2.x model

```python
import parl
import paddle
import paddle.nn as nn

class PolicyModel(parl.Model):
    def __init__(self, obs_dim, act_dim):
        super().__init__()
        self.fc = nn.Linear(obs_dim, act_dim)

    def forward(self, obs):
        return self.fc(obs)

    def policy(self, obs):
        return paddle.nn.functional.softmax(self.forward(obs), axis=-1)
```

Paddle `parl.Model` instances are `paddle.nn.Layer` subclasses. Their weight helpers use a dict keyed by the model's state-dict names and assert that key sets and shapes match during `set_weights`.

### legacy Fluid model

```python
import parl

class StaticPolicy(parl.Model):
    def __init__(self):
        super().__init__()
        self.fc = parl.layers.fc(size=2, act="softmax")

    def policy(self, obs):
        return self.fc(obs)
```

Fluid models require `parl.layers` for parameter tracking. `get_weights()` returns a list in model-parameter order, not a state-dict mapping. Fluid agents must implement `build_program()` and use Fluid programs for `predict`, `sample`, and `learn`.

## Algorithm implementation pattern

A custom algorithm inherits `parl.Algorithm`, stores one or more models, and implements prediction and learning methods.

```python
import copy
import parl
import torch

class TinyDQNLike(parl.Algorithm):
    def __init__(self, model, gamma=0.99, lr=1e-3):
        super().__init__(model)
        self.target_model = copy.deepcopy(model)
        self.gamma = gamma
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    def predict(self, obs):
        return self.model.value(obs)

    def learn(self, obs, target_q):
        pred_q = self.model.value(obs)
        loss = torch.nn.functional.mse_loss(pred_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return float(loss.detach().cpu())

    def sync_target(self):
        self.model.sync_weights_to(self.target_model)
```

Important details:

- `parl.Algorithm.__init__(model)` asserts that `model` is a backend-compatible `parl.Model` for Torch/Paddle implementations.
- PARL's base `AlgorithmBase.get_weights()` can recursively collect direct `ModelBase` attributes and first-level lists, tuples, and dicts of models. It does not recurse through nested containers inside containers.
- `AlgorithmBase.set_weights()` expects the same attribute/container structure. Missing keys, different list lengths, or different dict key sets raise assertions.
- For algorithm-specific method requirements, use the target algorithm's model method names. For example, DQN-style algorithms often expect a `value()` method; policy-gradient style code often expects `policy()` or `forward()`.

## Agent implementation pattern

An agent wraps the algorithm and handles environment-facing input/output. In Torch and Paddle dynamic-graph code, the agent typically converts NumPy arrays to tensors, calls `self.alg`, and converts results back as needed.

```python
import numpy as np
import parl
import torch

class TinyAgent(parl.Agent):
    def __init__(self, algorithm):
        super().__init__(algorithm)

    def predict(self, obs):
        obs = torch.as_tensor(obs, dtype=torch.float32)
        with torch.no_grad():
            q = self.alg.predict(obs)
        return int(torch.argmax(q, dim=-1).item())

    def sample(self, obs, epsilon=0.1):
        if np.random.random() < epsilon:
            return int(np.random.randint(0, 2))
        return self.predict(obs)

    def learn(self, obs, target_q):
        obs = torch.as_tensor(obs, dtype=torch.float32)
        target_q = torch.as_tensor(target_q, dtype=torch.float32)
        return self.alg.learn(obs, target_q)
```

Agent rules of thumb:

- Call `super().__init__(algorithm)` so `self.alg` is set and backend assertions run.
- Implement `predict`, `sample`, and `learn` in the subclass; the base methods raise `NotImplementedError`.
- Use `Agent.train()` / `Agent.eval()` when models contain mode-sensitive modules such as dropout or batch normalization.
- Keep exploration policy and data conversion in the agent unless the algorithm specifically owns it.

## Saving and restoring

| Backend | Save behavior | Restore behavior | Common cautions |
| --- | --- | --- | --- |
| Torch | `agent.save(save_path, model=None)` writes a Torch state dict to a file path and creates parent directories if needed. | `agent.restore(save_path, model=None, map_location=None)` loads the file and applies it to the chosen model. | Recreate the same architecture first. Use `map_location="cpu"` or `torch.device("cpu")` when loading GPU-trained weights on CPU. |
| Paddle 2.x | `agent.save(save_path, model=None)` writes a Paddle state dict to the path. | `agent.restore(save_path, model=None)` loads the path and applies state dict. | The target model must have the same state-dict keys and shapes. For inference export, `save_inference_model` requires a working `forward` method plus input shape/dtype lists. |
| legacy Fluid | `agent.save(save_path, program=None)` writes parameter files into a directory, optionally for one program. | `agent.restore(save_path, program=None)` reads from a directory and validates expected program files. | Save path must be a directory, not a file. The agent must have built the same programs before restore. |

When an algorithm owns multiple models, pass the intended model explicitly to `save` / `restore` where the backend API supports it, or save through algorithm-level `get_weights` / `set_weights` for structured model collections.

## Weight synchronization and transfer

Use `model.sync_weights_to(target_model, decay=0.0)` for target-network updates:

```python
action_model.sync_weights_to(target_model)       # hard copy
action_model.sync_weights_to(target_model, 0.95) # soft update
```

Constraints enforced by the implementations:

- Source and target cannot be the same object.
- Source and target must be instances of the backend `parl.Model` class.
- Source and target model class names must match.
- `decay` must be between `0` and `1`.
- Parameter names and shapes must be compatible.

Use `get_weights` / `set_weights` for copying across equivalent models, algorithms, or agents:

```python
weights = agent_a.get_weights()
agent_b.set_weights(weights)
```

For Torch and Paddle dynamic-graph models, model weights are dicts of NumPy arrays. For legacy Fluid models, model weights are ordered lists. Algorithm and Agent wrappers may return nested dict/list structures when multiple models are present.
