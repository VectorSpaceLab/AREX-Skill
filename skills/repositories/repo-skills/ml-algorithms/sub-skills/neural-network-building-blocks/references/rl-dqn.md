# DQN workflow notes

## Purpose

Read this before using `mla.rl.dqn.DQN` with Gym environments. The implementation is a compact educational Deep Q-Learning loop, not a modern RL framework.

## API pattern

```python
from mla.rl.dqn import DQN

agent = DQN(n_episodes=500, gamma=0.99, batch_size=32, epsilon=1.0, decay=0.005, min_epsilon=0.1, memory_limit=500)
agent.init_environment("CartPole-v0")
agent.init_model(model_factory)
agent.train(render=False)
agent.play(episodes=5)
```

`model_factory(n_actions, batch_size)` must return an object with:

- `predict(X)` returning Q-values shaped `(batch, n_actions)`.
- `fit(X, y)` to update the Q-function on a batch.

The repository example uses `NeuralNet` with `Dense(32)`, `Activation("relu")`, `Dense(n_actions)`, `loss="mse"`, `Adam()`, and `max_epochs=1`.

## Legacy Gym warning

The current source expects legacy Gym behavior:

- `state = env.reset()` returns only the observation.
- `new_state, reward, done, _ = env.step(action)` returns four values.
- `wrappers.Monitor` exists when `monitor=True`.

Modern Gymnasium and newer Gym versions use different reset/step signatures. If the user has a newer environment, adapt the loop or use a compatibility wrapper before training.

## Runtime and side-effect warnings

- CartPole training can take hundreds or thousands of episodes.
- `render=True` or `play()` can require a display and can block headless automation.
- `monitor=True` writes video/monitor files and should not be used in a smoke check.
- The loop maintains replay memory in Python lists; keep `memory_limit` small for tests.

## Safe checks

Use the bundled neural smoke's `dqn-init` workflow to verify constructor and model-factory wiring without creating a Gym environment or training. If an actual environment is needed, first run a tiny Gym API probe separately and inspect whether reset/step returns legacy or modern tuples.

## Minimal model factory

```python
from mla.neuralnet import NeuralNet
from mla.neuralnet.layers import Dense, Activation
from mla.neuralnet.optimizers import Adam

def model_factory(n_actions, batch_size=32):
    return NeuralNet(
        layers=[Dense(16), Activation("relu"), Dense(n_actions)],
        loss="mse",
        optimizer=Adam(),
        metric="mse",
        batch_size=batch_size,
        max_epochs=1,
        verbose=False,
    )
```

Only call `agent.init_environment()` and `agent.train()` after confirming the active Gym package matches or has been adapted to the expected API.
