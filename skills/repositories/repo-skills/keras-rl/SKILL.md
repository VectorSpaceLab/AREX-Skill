---
name: keras-rl
description: "Use legacy keras-rl reinforcement-learning agents, memories,
  policies, processors, callbacks, and safe smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# keras-rl

Use this repo skill when a task involves the legacy `keras-rl` package: Keras 2.x reinforcement-learning agents, Gym-style environments, DQN/Double DQN/Dueling DQN, SARSA, CEM, DDPG, NAF/CDQN, replay memories, exploration policies, processors, callbacks, logging, or lightweight compatibility checks.

## First checks

- Treat `keras-rl` as **legacy standalone Keras 2.x** code. Do not assume modern Keras 3 or pure `tf.keras` compatibility.
- Prefer a Keras-2-compatible backend stack for any real execution. A Theano CPU backend is often the safest compile-only route for this package family; TensorFlow-era imports can succeed while agent construction still fails on legacy symbolic-tensor assumptions.
- Install the package itself with one of:

```bash
pip install keras-rl
pip install "keras-rl[gym]"  # when Gym examples or environments are needed
```

Additional workflow dependencies are separate: `h5py` for weight files, `matplotlib` for log plotting, `wandb` for `WandbLogger`, Atari extras/ROMs for Atari tasks, and MuJoCo system/license dependencies for MuJoCo tasks.

Minimal import check:

```python
import rl
from rl.agents import DQNAgent, DDPGAgent, CEMAgent, SARSAAgent, NAFAgent
from rl.memory import SequentialMemory, EpisodeParameterMemory
from rl.policy import EpsGreedyQPolicy, BoltzmannQPolicy
```

For environment and backend diagnostics, use the checker linked from `core-extension-and-logging` before spending time on training.

## Route by task

### Discrete-action agents

Use [discrete-control](sub-skills/discrete-control/SKILL.md) when the task names or implies:

- DQN, Double DQN, Dueling DQN, SARSA, CEM, CartPole, Atari-style DQN, or a discrete Gym action space.
- `SequentialMemory`, `EpisodeParameterMemory`, `EpsGreedyQPolicy`, `BoltzmannQPolicy`, `LinearAnnealedPolicy`, replay warmup, target networks, or dueling aggregation.
- A need to compile a safe discrete-agent smoke script without long training or rendering.

### Continuous-action agents

Use [continuous-control](sub-skills/continuous-control/SKILL.md) when the task names or implies:

- DDPG, NAF/CDQN, Pendulum, MuJoCo, continuous action spaces, actor/critic wiring, `critic_action_input`, `V_model`, `mu_model`, `L_model`, or covariance modes.
- `OrnsteinUhlenbeckProcess`, `GaussianWhiteNoiseProcess`, continuous replay memory, action-noise sizing, or a compile-only continuous-agent smoke check.

### Core lifecycle, processors, callbacks, and logging

Use [core-extension-and-logging](sub-skills/core-extension-and-logging/SKILL.md) when the task involves:

- `Agent.fit`, `Agent.test`, compile-before-fit errors, callback wiring, `verbose`, `visualize`, `nb_max_episode_steps`, `action_repetition`, or `start_step_policy`.
- Custom `Processor` or `Env` implementations, `MultiInputProcessor`, `WhiteningNormalizerProcessor`, Gym API adapters, or state-batch shape transformations.
- `FileLogger`, `ModelIntervalCheckpoint`, `WandbLogger`, log JSON plotting, environment compatibility checks, `clone_model`, `clone_optimizer`, `huber_loss`, or `WhiteningNormalizer`.

## Cross-cutting references

- Read [Repository Provenance](references/repo-provenance.md) before deciding whether this skill is current for a different checkout or after package code changes.
- Read [Install and compatibility](references/install-and-compatibility.md) when imports, Keras backend setup, Gym optional dependencies, WandB, matplotlib, weight files, Atari, or MuJoCo requirements are uncertain.
- Read [Troubleshooting](references/troubleshooting.md) for package-wide failure triage before drilling into a sub-skill-specific troubleshooting page.

## Safe operating stance

- Prefer compile/build smoke checks before `fit` or `test`. Full training examples can be long-running, display-dependent, or require external simulators.
- Keep Atari and MuJoCo tasks explicitly optional unless the user has already installed the required extras, ROMs/data, system packages, and licenses.
- Do not use original repository examples as runtime dependencies. Use the bundled smoke helpers and references in this skill tree instead.
- For any workflow that spans agent construction and logging/lifecycle, start in the agent-family sub-skill, then cross-check `Agent.fit`/callbacks in `core-extension-and-logging`.
