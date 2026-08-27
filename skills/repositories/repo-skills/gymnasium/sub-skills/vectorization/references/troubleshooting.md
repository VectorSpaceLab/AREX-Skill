# Vectorization Troubleshooting

## Action Batch Shape Errors

Symptom: `step` raises because the action shape/type is wrong, or only one sub-env appears to receive an action.

Likely cause: code samples from `single_action_space` instead of the batched `action_space`.

Fix:

```python
# Wrong for a vector step: one action only
action = envs.single_action_space.sample()

# Correct: one action per sub-env, with the exact batched structure
actions = envs.action_space.sample()
observations, rewards, terminations, truncations, infos = envs.step(actions)
```

For a policy, make the policy output a batch compatible with `envs.action_space`. For `Discrete` single actions, Gymnasium commonly exposes a `MultiDiscrete` batched action space.

## Scalar `done` Logic in a Vector Loop

Symptom: `if terminated or truncated:` raises an ambiguous truth-value error or silently handles only one env.

Fix:

```python
done_mask = terminations | truncations
for env_index, done in enumerate(done_mask):
    if done:
        handle_finished_sub_env(env_index)
```

Use vectorized array operations when possible. Do not collapse the masks with `.any()` unless the algorithm really wants a whole-batch condition.

## Autoreset Confusion and Final Observations

Symptom: the observation after a terminal step seems to be a reset observation, terminal observations are missing, or finished envs are stepped again accidentally.

Check:

```python
from gymnasium.vector import AutoresetMode

mode = envs.metadata.get("autoreset_mode")
```

- `NEXT_STEP`: terminal observations are returned on the terminal step; the next step resets finished sub-envs and returns zero reward/false masks for them.
- `SAME_STEP`: terminal observations are stored under `infos["final_obs"]` with `infos["_final_obs"]`; returned observations for finished envs are already reset observations.
- `DISABLED`: call `envs.reset(options={"reset_mask": done_mask})` before stepping finished sub-envs again.

If a wrapper fails with a `SAME_STEP` assertion, switch to `NEXT_STEP` or use a wrapper designed for same-step final-observation handling.

## Info Dictionary Surprises

Symptom: code expects `infos` to be a list of dictionaries, or reads invalid zeros for sub-envs that did not provide a key.

Gymnasium vector infos are dictionaries of arrays plus masks:

```python
if "episode" in infos:
    valid = infos["_episode"]
    episode_data = infos["episode"]
```

For compatibility with older code, wrap the vector env with `gymnasium.wrappers.vector.DictInfoToList`.

## `AsyncVectorEnv` Factory or Pickling Failures

Symptoms include worker startup failures, `AttributeError: Can't pickle local object`, hanging subprocesses, or platform-specific failures under `spawn`.

Fixes:

- First reproduce with `SyncVectorEnv`; if sync fails, the issue is not multiprocessing.
- Move env factory functions to module top level when possible.
- Avoid closing over open files, sockets, large models, loggers, UI handles, or non-picklable objects.
- Pass simple configuration values into a top-level factory through `functools.partial` or a small callable class.
- Try an explicit multiprocessing context in `vector_kwargs`, such as `{"context": "fork"}` on platforms where fork is safe, or use the platform default when unsure.
- Set `daemon=False` only when a sub-environment must create child processes; otherwise keep the default.
- Always call `close()` after exceptions to terminate workers.

If the environment is cheap or hard to pickle, use `SyncVectorEnv` instead of forcing async.

## Shared Memory and Dynamic/Object Observations

Symptom: `AsyncVectorEnv(shared_memory=True)` raises about unsupported custom spaces or dynamic shapes.

Reason: shared memory requires static layouts. Built-in utilities support many static spaces such as `Box`, `Discrete`, `MultiDiscrete`, `MultiBinary`, `Tuple`, `Dict`, `Text`, and `OneOf`; dynamic spaces such as `Graph` and `Sequence`, custom spaces, or object-heavy observations may not fit static shared memory.

Fix:

```python
envs = gym.vector.AsyncVectorEnv(env_fns, shared_memory=False)
```

Then decide whether the slower pipe transfer is acceptable. If not, redesign observations into static `Box`/`Dict` spaces; use `../spaces-data/SKILL.md` for space redesign guidance.

## Observation Space Mismatch

Symptom: constructor assertions mention `observation_mode='same'`, equivalent spaces, common shape, or dtype.

Fixes:

- Use `observation_mode="same"` only when all sub-env observation spaces are equal.
- Use `observation_mode="different"` only for spaces of the same type with compatible shape and dtype but differing bounds or values.
- For advanced custom batching, pass an explicit `(observation_space, single_observation_space)` tuple and prove `reset`/`step` samples match it.
- Keep action spaces identical across sub-envs for built-in sync/async vectorizers.

## Wrong Wrapper Namespace

Symptom: a single-env wrapper rejects a `VectorEnv`, or a vector wrapper rejects a single `Env`.

Fix:

- Use `gymnasium.wrappers.vector.FlattenObservation`, not `gymnasium.wrappers.FlattenObservation`, after vectorization.
- Use `make_vec(..., wrappers=[gymnasium.wrappers.SomeSingleEnvWrapper])` or wrap inside each factory when the wrapper should apply per sub-env.
- Use `../wrappers-recording/SKILL.md` for single-env wrapper behavior and this sub-skill for vector placement.

## Render and Video Limitations

Symptoms include `render()` returning `None`, video wrappers failing, human rendering issues, or missing `moviepy`.

Fixes:

- Create the env with a compatible render mode, usually `render_mode="rgb_array"` for recording.
- Use `gymnasium.wrappers.vector.RecordVideo` for vector envs, not the single-env `RecordVideo` wrapper.
- Install the optional video dependency only when recording is required.
- Expect vector `render()` to return a tuple of per-env frames for many vectorizers.
- Keep `AsyncVectorEnv` rendering conservative; sync mode is easier to debug for video and human rendering.

## `make_vec` Mode Errors

Common causes:

- Invalid mode: use `"sync"`, `"async"`, `"vector_entry_point"`, or a `gymnasium.VectorizeMode` value.
- `vector_entry_point` requested for an env without a vector entry point.
- `sync` or `async` requested for an env spec without a single-env entry point.
- `wrappers` or `vector_kwargs` passed with `"vector_entry_point"`; use sync/async or construct the custom vector env directly.

When in doubt, start with:

```python
envs = gym.make_vec("CartPole-v1", num_envs=2, vectorization_mode="sync")
```

Then add async, wrappers, render modes, and custom kwargs one at a time.
