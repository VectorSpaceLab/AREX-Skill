# Discrete-control troubleshooting

Use this matrix to diagnose build, compile, and light-smoke failures for DQN-family, SARSA, CEM, memory, policy, Atari, and backend compatibility issues.

## Model output shape mismatch

Symptoms:

- `DQN expects a model that has one dimension for each action`
- `Model ... has more than one output`
- Q-value assertion failures such as expected `(batch, nb_actions)` or `(nb_actions,)`
- Silent SARSA/CEM build followed by shape errors during the first action or batch

Fixes:

1. Make the model single-output.
2. End with `Dense(nb_actions)` and a linear activation for DQN/SARSA.
3. For CEM, use `Dense(nb_actions)`; softmax is common but shape is the critical requirement.
4. If using `SequentialMemory(window_length=W)`, the model input must include `W`, for example `Flatten(input_shape=(W,) + observation_shape)`.
5. Recheck that `nb_actions` came from a discrete action space, not an observation dimension.

Dueling DQN still needs the original final Dense width to equal `nb_actions`; the agent validates the supplied model before replacing the head internally.

## Compile-before-fit/test errors

Symptoms:

- Missing `trainable_model`, `target_model`, `metrics_names`, or `compiled` state.
- DQN target-network methods fail after loading or before training.
- `fit`/`test` starts and fails before meaningful environment interaction.

Fixes:

- DQN/SARSA: call `agent.compile(optimizer, metrics=[])` before lifecycle methods.
- CEM: call `cem.compile()` with **no optimizer argument**.
- Keep lifecycle, callback, and logging debugging in the core-extension-and-logging sub-skill; this sub-skill only confirms discrete agent construction and compile surfaces.

## `target_model_update` hard vs soft semantics

Symptoms:

- Target network appears to update too often or not as expected.
- A soft-update coefficient is accidentally treated as a step interval.

Semantics:

| Value | Meaning |
| --- | --- |
| `target_model_update >= 1` | Hard update: cast to integer and copy online weights to target every N steps. |
| `0 < target_model_update < 1` | Soft update: target receives `tau * online + (1 - tau) * target` every train update. |
| `0` | Effectively no soft movement after initial clone; avoid unless deliberately freezing the target. |
| `< 0` | Invalid; constructor raises a value error. |

Use hard periods such as `10000` for Atari-style DQN and soft coefficients such as `1e-2` for small CartPole-style experiments.

## TensorFlow symbolic Tensor `len(model.output)` incompatibility

Symptoms:

- Type errors mentioning `len` on a symbolic tensor.
- Errors around `model.output`, `_keras_shape`, or symbolic Tensor truth/length checks while constructing `DQNAgent`.

Cause:

keras-rl uses legacy Keras 2.x assumptions and inspects model outputs in ways that some TensorFlow-backed symbolic tensor stacks reject.

Fixes:

1. Prefer a Keras 2.x-compatible backend stack for keras-rl.
2. Set the backend before importing Keras in a fresh process.
3. If TensorFlow-backed construction fails, try a compatible legacy backend or apply a local compatibility patch before using DQN-family agents.
4. Run `scripts/build_discrete_agents_smoke.py --agent dqn --backend-note` before long training.

## Missing `wandb` when importing callbacks

Symptoms:

- `ImportError: No module named wandb` after importing `rl.callbacks` or using logging callbacks.
- A discrete agent build succeeds until callback/logging code is imported.

Cause:

The callbacks module imports `wandb` at module import time.

Fixes:

- Do not import `rl.callbacks` for plain DQN/SARSA/CEM build and compile checks.
- Install the optional W&B dependency only if using `WandbLogger`.
- Route `FileLogger`, `WandbLogger`, callback setup, and log visualization questions to the core-extension-and-logging sub-skill.

## Memory selection mistakes

Symptoms:

- DQN constructor missing `memory`.
- CEM training never records usable episode parameters.
- SARSA code tries to pass replay memory.
- Replay sampling warnings or assertions about not enough entries.

Fixes:

| Agent | Correct memory choice | Notes |
| --- | --- | --- |
| DQN / Double DQN / Dueling DQN | `SequentialMemory(limit=..., window_length=...)` | Needs replay transitions; warm up above `batch_size` and `window_length`. |
| SARSA | none | On-policy one-step updates; no replay memory parameter. |
| CEM | `EpisodeParameterMemory(limit=..., window_length=...)` | Stores parameter vectors and total episode rewards. |

If sampling warns about insufficient entries, increase `nb_steps_warmup`, decrease `batch_size`, increase training steps, or lower `window_length` for the smoke case.

## `delta_clip` and Huber-loss issues

Symptoms:

- Loss behaves like unclipped squared error when clipping was expected.
- Assertion that clip value must be positive.

Fixes:

- Use `delta_clip=1.` for clipped Huber loss.
- Use `delta_clip=np.inf` for unclipped squared behavior.
- Do not set `delta_clip <= 0`.

## Dueling DQN head errors

Symptoms:

- Assertion that `dueling_type` must be one of `avg`, `max`, `naive`.
- Shape errors after enabling dueling.

Fixes:

- Set `dueling_type='avg'` first.
- Keep a real hidden penultimate layer before the final `Dense(nb_actions)` layer.
- Do not hand-build a multi-output dueling model and also ask the agent to enable its internal dueling head unless you fully control the shape contract.

## CEM compile and elite-fraction errors

Symptoms:

- `compile()` complains about unexpected optimizer or metrics arguments.
- CEM updates are ineffective or elite batch is empty.

Fixes:

- Call `cem.compile()` with no arguments.
- Ensure `int(batch_size * elite_frac) >= 1`.
- Use `EpisodeParameterMemory` and make episodes terminate so total rewards can be recorded.
- For compile-only smokes, do not expect learning; just confirm construction and compile.

## Atari extras, ROMs, and skipped heavy workflows

Symptoms:

- Missing Pillow, Atari environments, ALE/ROM packages, display/rendering, or huge memory use.
- Environment id not found or ROM licensing errors.

Fixes:

- Treat this generated sub-skill's Atari material as reference-only.
- Install optional Atari dependencies and ROMs intentionally in the consuming environment; do not auto-download ROMs in a smoke check.
- Use lightweight vector smoke checks before attempting pixel training.
- Keep full Atari training out of routine verification unless the task explicitly budgets for it.

## Gym API version differences

Symptoms:

- `reset()` returns `(observation, info)` and keras-rl expects only `observation`.
- `step()` returns five values `(observation, reward, terminated, truncated, info)` and keras-rl expects four.
- `env.seed(...)` is missing.

Fixes:

- Use a legacy Gym-compatible environment or add a wrapper that converts:
  - `reset()` to return only the observation.
  - `step()` to return `(observation, reward, terminated or truncated, info)`.
  - seeding to call `reset(seed=...)` when `env.seed` is unavailable.
- For build-only checks, use the bundled smoke helper's tiny in-process environment instead of depending on Gym.

## Backend and optimizer keyword mismatch

Symptoms:

- `Adam(lr=...)` or `Adam(learning_rate=...)` keyword errors.
- Keras import succeeds but keras-rl agent compile fails in backend utilities.

Fixes:

- First confirm that the environment is meant to run legacy Keras 2.x code.
- Try the alternate optimizer keyword only as a compatibility bridge; if many Keras APIs are missing or renamed, use a more compatible backend stack.
- Set the backend in the environment before importing Keras; changing it after import is too late.
