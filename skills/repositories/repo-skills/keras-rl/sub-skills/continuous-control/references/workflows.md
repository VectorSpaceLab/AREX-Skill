# continuous-control workflows

Use these workflows to build and lightly verify keras-rl continuous-action agents without relying on long training or optional simulator installations.

## Compatibility preflight

1. Use standalone Keras 2.x-compatible imports (`keras.*`, not modern `tf.keras` rewrites).
2. Prefer a legacy Keras backend and set/check the backend before importing Keras.
3. Confirm the installed package exposes `DDPGAgent`, `NAFAgent` or `ContinuousDQNAgent`, `SequentialMemory`, and the desired random process.
4. For Gym tasks, derive `nb_actions` from a one-dimensional continuous action space. For newer Gym APIs, account for changed reset/seed signatures before training.
5. Start with build/compile smokes. Do not start long training, rendering, or simulator-dependent MuJoCo work until model wiring and backend compatibility are proven.

## DDPG actor/critic recipe

1. Determine:
   - `observation_shape`, for example `(3,)` for a Pendulum-style state.
   - `window_length`, usually `1`.
   - `nb_actions`, for example `1` for Pendulum torque.
2. Build the actor:
   - Input shape: `(window_length,) + observation_shape` for a single observation input.
   - Output: one dense vector with `nb_actions` units.
   - Activation: `linear` for a raw smoke; use `tanh` or custom scaling/clipping when the environment requires bounded actions.
3. Build the critic:
   - Create `critic_action_input = Input(shape=(nb_actions,), name='...')`.
   - Create observation input(s), flatten or encode them, concatenate with the action path, and output a single Q value.
   - Construct `critic = Model(inputs=[critic_action_input, observation_input], outputs=q_value)` or preserve equivalent ordering for multi-input observations.
4. Add collaborators:
   - `memory = SequentialMemory(limit=..., window_length=window_length)`.
   - `random_process = OrnsteinUhlenbeckProcess(theta=.15, mu=0., sigma=.3, size=nb_actions)` or a matching Gaussian process.
5. Construct and compile:
   - `agent = DDPGAgent(nb_actions=nb_actions, actor=actor, critic=critic, critic_action_input=critic_action_input, memory=memory, random_process=random_process, ...)`.
   - `agent.compile([actor_optimizer, critic_optimizer], metrics=['mae'])` when actor and critic should have separate learning rates.

### DDPG sanity checks

- `critic_action_input in critic.inputs` must be true by object identity.
- The critic must have at least two inputs and exactly one output.
- A dry actor prediction should flatten to `(nb_actions,)` for one state window.
- A random-process sample should have shape `(nb_actions,)`.
- The DDPG optimizer list must contain exactly two optimizers if a list/tuple is used.

## NAF / Continuous DQN recipe

1. Determine `observation_shape`, `window_length`, `nb_actions`, and `covariance_mode` (`full` or `diag`).
2. Build `V_model`:
   - Observation input only.
   - Final `Dense(1)` for scalar state value.
3. Build `mu_model`:
   - Observation input only.
   - Final `Dense(nb_actions)` for deterministic continuous action.
4. Build `L_model`:
   - Inputs: action input first, then observation input(s).
   - Hidden layers may concatenate action and observation features.
   - Final units:
     - `full`: `(nb_actions * nb_actions + nb_actions) // 2`.
     - `diag`: `nb_actions`.
5. Add `SequentialMemory` and an optional random process sized to `nb_actions`.
6. Construct and compile:
   - `agent = NAFAgent(nb_actions=nb_actions, V_model=V_model, L_model=L_model, mu_model=mu_model, memory=memory, covariance_mode='full', random_process=random_process, ...)`.
   - `agent.compile(optimizer, metrics=['mae'])`.

### NAF sanity checks

- `V_model.output_shape[-1] == 1`.
- `mu_model.output_shape[-1] == nb_actions`.
- `L_model.output_shape[-1]` matches `covariance_mode`.
- `covariance_mode` is exactly `full` or `diag`.
- Random-process sample shape is `(nb_actions,)` if noise is enabled.

## Safe compile/build smoke

Run the bundled helper from any working directory where keras-rl and its Keras dependencies are importable:

```bash
python <skill-directory>/scripts/build_continuous_agents_smoke.py --agent all --backend theano
```

Common variants:

```bash
# DDPG only, using separate actor/critic optimizers.
python <skill-directory>/scripts/build_continuous_agents_smoke.py --agent ddpg --ddpg-optimizer-list-size 2

# NAF with diagonal covariance for a cheaper shape check.
python <skill-directory>/scripts/build_continuous_agents_smoke.py --agent naf --covariance-mode diag

# Prove the script catches an action-noise sizing mistake.
python <skill-directory>/scripts/build_continuous_agents_smoke.py --agent ddpg --noise-size 2 --nb-actions 1
```

The helper intentionally does not create Gym environments, render windows, train, download assets, save weights, or require MuJoCo. It builds small synthetic Pendulum-like models and compiles the selected agents.

## Pendulum-style Gym task adaptation

For a real Pendulum-like task after compile smoke passes:

1. Create the Gym environment and seed it using the API supported by that Gym version.
2. Check `len(env.action_space.shape) == 1` and use `env.action_space.shape[0]` as `nb_actions`.
3. Use `env.observation_space.shape` for the observation input shape.
4. For older Gym versions, environment IDs may use `Pendulum-v0`; newer versions usually use `Pendulum-v1` and return `(observation, info)` from `reset()`.
5. Keep `nb_max_episode_steps` bounded during tests and avoid rendering in automated runs.
6. If actions must respect `env.action_space.low/high`, add an action-scaling processor or actor output activation; keras-rl does not infer those bounds for you.

## MuJoCo reference-only adaptation

MuJoCo examples follow the same DDPG pattern with larger hidden layers, `tanh` actor output, action clipping in a processor, and much longer training. Treat them as reference-only because they may require:

- MuJoCo binaries or newer simulator packages.
- A valid license or accepted package-specific terms for legacy stacks.
- Native compiler/system libraries and compatible Gym versions.
- Substantial CPU/GPU time and long training horizons.

Do not make MuJoCo a default verification gate. First prove DDPG compile wiring with the bundled smoke helper, then treat simulator setup and training performance as a separate user-approved task.
