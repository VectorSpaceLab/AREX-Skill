# Troubleshooting envs and transforms

## Missing optional simulator extras

Symptoms:

- `ModuleNotFoundError` for `gym`, `gymnasium`, `dm_control`, `mujoco`, `vmas`, `pettingzoo`, `open_spiel`, `brax`, `jumanji`, Isaac packages, image/video packages, or rendering libraries.
- Env construction by id fails before any TorchRL TensorDict appears.

Fix:

1. Confirm the task really requires that backend. If not, switch to native `PendulumEnv` or another installed backend for the TorchRL logic.
2. Install the narrow optional dependency family for the selected simulator instead of broad test/dev extras.
3. Run a one-env, no-rendering smoke before pixels, vectorization, collectors, or training.
4. Document backend-specific behavior as optional unless a smoke has passed in the active environment.

## Gym/Gymnasium backend ambiguity

Symptoms:

- An environment works in plain Gymnasium but fails through `GymEnv`.
- Gym and Gymnasium are both installed and an API mismatch appears in `reset` or `step` returns.
- Observation space conversion differs from the expected TensorDict keys.

Fix:

```python
from torchrl.envs.libs.gym import GymEnv, GymWrapper, set_gym_backend

with set_gym_backend("gymnasium"):
    env = GymEnv("CartPole-v1")
```

If id construction remains brittle, construct the backend env directly and use `GymWrapper(backend_env)`. Then inspect `env.observation_spec`, `env.action_spec`, and `env.reset().keys(True, True)`.

## Bad specs or `check_env_specs` failures

Symptoms:

- `AssertionError: Keys mismatch`.
- Fake and real TensorDict shapes or dtypes differ.
- `ParallelEnv` or collectors fail while a single env seems to step.
- A transform changes keys but specs still advertise old keys.

Fix:

1. Run `env.fake_tensordict()` and `env.rollout(3, return_contiguous=False)` side by side.
2. Verify every key emitted by `_reset` and `_step` has a matching spec at the right nesting level.
3. Check dtypes, not only shapes. Boolean done-family specs must emit boolean tensors.
4. If a transform renames, selects, excludes, flattens, or scales keys, inspect transformed specs after wrapping.
5. Run `check_env_specs(env, break_when_any_done="both")` for envs that may stop early.

## Done, terminated, truncated, and time-limit layout

Symptoms:

- Rollout never resets or resets too often.
- `StepCounter` writes `truncated` but losses/collectors read a different done key.
- Multi-agent env has per-agent done keys and root done keys with incompatible shapes.

Fix:

- Treat `done` as the reset signal used by rollouts and collectors.
- Keep `terminated` for task termination and `truncated` for time limits when the backend exposes them.
- With `StepCounter(max_steps=N, update_done=True)`, expect `truncated=True` to also set `done=True` at that level.
- Use `env.done_key` or `env.done_keys`; do not hard-code a flat `"done"` after wrappers, grouping, or transforms.
- For nested done keys, ensure any private reset-control keys live at the same nesting level as their corresponding done entry.

## Transform key mismatch

Symptoms:

- `KeyError` for an observation or action key after adding `TransformedEnv`.
- `ActionScaling` appears to scale the wrong direction.
- Policy sees one key name while the base env requires another.

Fix:

1. Identify direction:
   - forward path: base output to policy-facing TensorDict uses `in_keys` -> `out_keys`;
   - inverse path: policy action to base input uses `out_keys_inv` -> `in_keys_inv`.
2. Print `env.reset().keys(True, True)` and `env.action_spec` after wrapping.
3. Use one `ActionScaling` per action key; compose several for multiple action leaves.
4. Clone transforms before attaching the same logical transform to a second env.
5. Run `check_env_specs` immediately after transform changes.

## Nested keys and multi-agent groups

Symptoms:

- `step_mdp` drops reward/action/done unexpectedly.
- A loss or transform reads `"action"` but the data has `("agents", "action")`.
- Specs seem flat when full specs are nested.

Fix:

```python
next_root = step_mdp(
    transition,
    reward_keys=env.reward_keys,
    done_keys=env.done_keys,
    action_keys=env.action_keys,
    exclude_reward=False,
)
```

Use `keys(True, True)` to inspect nested keys. For full composite specs, inspect `env.input_spec` and `env.output_spec` rather than only the leaf convenience spec. For losses and modules, pass the env-resolved key attributes through `set_keys()` or constructor arguments.

## Vectorized process start and worker failures

Symptoms:

- `ParallelEnv` hangs or workers exit before first reset.
- Pickling errors mention a local function, lambda, open file, simulator object, or non-picklable closure.
- Code works interactively but fails when launched as a script on another platform.

Fix:

1. Move `make_env` to module top level.
2. Put process-spawning code under `if __name__ == "__main__":`.
3. Debug first with `SerialEnv(num_workers, make_env)`.
4. Run `check_env_specs(make_env())` before `ParallelEnv`.
5. Close envs in `finally` blocks.
6. If a simulator has its own multiprocessing or app launcher, follow that simulator's start-method/import-order rules before TorchRL vectorization.

## Pixel and rendering dependency failures

Symptoms:

- `from_pixels=True` produces no `pixels` key.
- Headless render errors mention EGL, GL, GLFW, OSMesa, camera initialization, or codecs.
- Image transform sees an unexpected dtype or dimension order.

Fix:

1. Verify backend render mode before adding TorchRL image transforms.
2. Set simulator render backend variables before importing the simulator when required by that simulator.
3. Confirm raw `pixels` shape and dtype from `env.reset()`.
4. Add image transforms in a deliberate order, usually tensor conversion before resize/crop for array-like backend output.
5. Install rendering/video extras and system codecs only when the task requires frame capture or video output.

## Dynamic specs and non-contiguous data

Symptoms:

- Contiguous rollout fails for variable-length observations.
- Parallel/vectorized env is much slower than expected.
- A key appears on some steps and disappears on others.

Fix:

- Mark variable dimensions as dynamic in the spec when supported.
- Use `rollout(..., return_contiguous=False)`.
- Keep the set of keys stable across steps; dynamic shape is acceptable, intermittent keys are not.
- Benchmark before using multiprocessing because dynamic data cannot rely on the same efficient contiguous buffers.

## Action chunk confusion

Symptoms:

- `ActionChunkTransform` is attached to an env and expected to execute multiple simulator steps.
- Chunks cross episode boundaries or have surprising shape.

Fix:

- Treat `ActionChunkTransform` as a data transform for time-structured training samples.
- Ensure actions are shaped `[*B, T, action_dim]` and the action dimension immediately follows the time dimension.
- Include a matching `("next", done_key)` entry when chunks must stop at trajectory boundaries.
- Route VLA schema, action-tokenizer, and chunked loss tasks to `llm-vla-and-services`.
