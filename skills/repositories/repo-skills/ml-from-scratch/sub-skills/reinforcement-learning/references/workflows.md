# DeepQNetwork workflows

This reference covers the ML-From-Scratch DQN workflow for Gym CartPole. For neural-network layer details, route to [`../../deep-learning/SKILL.md`](../../deep-learning/SKILL.md); keep this sub-skill focused on DQN orchestration and compatibility.

## 1. Compatibility baseline

Expected working baseline:

- Python 3.11-compatible package install
- CPU backend; no GPU is required
- `gym==0.25.x` plus NumPy `<2` is the safest DQN pairing
- Gym deprecation warnings are expected and do not by themselves mean the workflow failed
- Avoid `play`/render in headless verification; use the bundled smoke script instead

Run the bundled smoke from this sub-skill directory when you need a fast check:

```bash
python scripts/run_dqn_smoke.py --epochs 1 --max-steps 8 --batch-size 4
```

The smoke patches only its own process for known Gym/NumPy checker issues, wraps reset/step outputs into the old API that `DeepQNetwork.train` expects, keeps `epsilon=1.0`, and never calls render.

## 2. DQN lifecycle

Core API surface:

```python
from mlfromscratch.reinforcement_learning import DeepQNetwork

# CartPole-v1 defaults to n_states=4 and n_actions=2.
dqn = DeepQNetwork(
    env_name="CartPole-v1",
    epsilon=1,
    gamma=0.9,
    decay_rate=0.005,
    min_epsilon=0.1,
)

dqn.set_model(model_builder)
dqn.train(n_epochs=500, batch_size=32)
# Only with an available display/render backend:
# dqn.play(n_epochs=10)
```

Important internal behavior:

- `DeepQNetwork.__init__` creates a Gym environment immediately.
- `dqn.n_states` comes from `env.observation_space.shape[0]`.
- `dqn.n_actions` comes from `env.action_space.n`.
- Replay memory is an in-memory list capped at `memory_size=300`.
- Each training step stores `(state, action, reward, new_state, done)`, samples a replay batch, builds `X` with shape `(batch, n_states)`, builds `y` with shape `(batch, n_actions)`, and calls `model.train_on_batch(X, y)`.
- Epsilon is updated after each episode as `min_epsilon + (1.0 - min_epsilon) * exp(-decay_rate * epoch)`.

## 3. Model-builder callback pattern

`set_model` expects a callback, not an already-built model. The callback receives the environment-derived dimensions and must return an ML-From-Scratch `NeuralNetwork` with output width equal to `n_outputs`.

```python
from mlfromscratch.deep_learning import NeuralNetwork
from mlfromscratch.deep_learning.layers import Dense, Activation
from mlfromscratch.deep_learning.loss_functions import SquareLoss
from mlfromscratch.deep_learning.optimizers import Adam


def model_builder(n_inputs, n_outputs):
    model = NeuralNetwork(optimizer=Adam(), loss=SquareLoss)
    model.add(Dense(64, input_shape=(n_inputs,)))
    model.add(Activation("relu"))
    model.add(Dense(n_outputs))
    return model


dqn.set_model(model_builder)
```

Shape contract:

- First dense layer: `input_shape=(n_inputs,)`; for CartPole this is usually `(4,)`.
- Final dense layer: `Dense(n_outputs)`; for CartPole this is usually `2` action-values.
- Loss: pass `SquareLoss` as a class, because `NeuralNetwork` instantiates the loss internally.
- Optimizer: pass an optimizer instance such as `Adam()`.

## 4. Smoke-scale training recipe

Use smoke settings to prove imports, Gym compatibility, model construction, replay-batch construction, and one bounded training episode:

```python
import random
import numpy as np

random.seed(13)
np.random.seed(13)

dqn = DeepQNetwork(env_name="CartPole-v1", epsilon=1.0, gamma=0.9, decay_rate=0.005, min_epsilon=0.1)
dqn.set_model(model_builder)

# Prefer a compatibility wrapper that limits episode length and normalizes Gym APIs.
dqn.train(n_epochs=1, batch_size=4)
```

Why `epsilon=1.0` for smoke:

- It keeps action selection random during the episode, avoiding the package's unbatched `model.predict(state)` action-selection path.
- It verifies replay and batch training without claiming policy quality.
- The post-episode epsilon update may still change `dqn.epsilon`; that is expected.

## 5. Longer educational runs

For exploratory training:

1. Confirm the one-epoch smoke passes first.
2. Use `gym==0.25.x` and NumPy `<2`, or wrap new Gym reset/step outputs before training.
3. Keep model output width equal to `dqn.n_actions`.
4. Expect stochastic reward curves; seed Python, NumPy, and the Gym action space when comparing runs.
5. Treat printed rewards as educational progress, not a benchmark-grade evaluation.

## 6. Play/render loop

`dqn.play(n_epochs)` calls `env.render()` and can fail on machines without a display. It also uses the greedy model prediction path, so state batching matters when adapting it for modern environments. In headless agent verification, avoid `play`; use `scripts/run_dqn_smoke.py` instead.
