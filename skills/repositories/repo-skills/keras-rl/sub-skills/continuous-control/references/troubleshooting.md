# continuous-control troubleshooting

## Actor output shape errors

Symptoms:

- `assert action.shape == (self.nb_actions,)` during action selection.
- Continuous environment rejects actions because shape is scalar, nested, or wrong length.
- Actor compile succeeds but later `select_action` fails.

Fixes:

- End DDPG actor and NAF `mu_model` with `Dense(nb_actions)`.
- Use a single actor/mu output tensor, not multiple Keras outputs.
- For `window_length=1`, feed models with input shape `(1,) + observation_shape`, not just `observation_shape`.
- If the environment has bounded actions, shape and bounds are separate problems: use `Dense(nb_actions)` for shape, then activation/scaling/clipping for bounds.

## DDPG critic input wiring mistakes

Symptoms:

- `Critic ... does not have designated action input ...`.
- `Critic ... does not have enough inputs`.
- Compile fails when combining actor and critic.

Fixes:

- Reuse the exact `Input(shape=(nb_actions,), ...)` object that was used in the critic `Model`; do not create a second identical-looking action input for `critic_action_input`.
- The critic must include action input plus observation input(s), and must output one Q tensor.
- Keep critic input order stable. DDPG stores the action input index and inserts action batches at that index during training.
- For multi-input observations, actor inputs must match the critic's non-action inputs in count and order; use a shared preprocessing plan.

## DDPG optimizer-list mistakes

Symptoms:

- `ValueError` about the number of optimizers.
- Actor/critic training graph compile fails unexpectedly after passing a list.

Fixes:

- Pass one optimizer object or string for both networks, or exactly two optimizers as `[actor_optimizer, critic_optimizer]`.
- Do not pass three optimizers or an empty list.
- Prefer separate optimizer instances when using a list, for example one lower actor learning rate and one higher critic learning rate.
- Use legacy Keras optimizer keyword names such as `lr` when working in an old Keras stack.

## NAF `L_model` / `NAFLayer` output sizing

Symptoms:

- Runtime errors from `NAFLayer` about input element counts.
- Combined NAF model compile fails only after `agent.compile(...)`.
- Shape mismatch for action, mu, or L tensors.

Fixes:

- For `covariance_mode='full'`, set `L_model` final units to `(nb_actions * nb_actions + nb_actions) // 2`.
- For `covariance_mode='diag'`, set `L_model` final units to `nb_actions`.
- `V_model` final units must be `1`.
- `mu_model` final units must be `nb_actions`.
- `L_model` should accept `[action_input] + observation_inputs`; its action input shape is `(nb_actions,)`.

## NAF covariance modes

Symptoms:

- Unsupported covariance mode errors.
- Full covariance works for one action but becomes slow or shape-prone for larger action spaces.

Fixes:

- Use only `full` or `diag`.
- Start with `diag` for cheap wiring/debugging checks.
- Use `full` for low-dimensional control when the lower-triangular parameterization is desired.
- Keep the `L_model` output size synchronized with the selected mode.

## Random-process sizing

Symptoms:

- `assert noise.shape == action.shape` during action selection.
- Noise sample is scalar or wrong-length vector.
- DDPG/NAF compile succeeds but the first training or action call fails.

Fixes:

- Set `size=nb_actions` for `OrnsteinUhlenbeckProcess` and `GaussianWhiteNoiseProcess`.
- Verify `np.asarray(random_process.sample()).shape == (nb_actions,)` before training.
- Call `random_process.reset_states()` after diagnostic sampling if you want a clean starting state.
- For multidimensional action spaces, keep `nb_actions` equal to the flattened one-dimensional action count expected by keras-rl.

## Legacy Keras backend compatibility

Symptoms:

- Import or compile failures involving symbolic tensor length, `len(model.output)`, backend-specific tensor ops, or optimizer API changes.
- Code written for modern `tf.keras` behaves differently from standalone Keras 2.x.

Fixes:

- Treat this package as legacy standalone Keras 2.x code.
- Prefer a legacy Keras backend and set/check it before importing Keras.
- Check Keras, backend, NumPy, h5py, and Gym compatibility as a group; do not mix arbitrarily modern packages into an old keras-rl stack.
- If TensorFlow-backed import or model validation fails on symbolic tensor length, try a legacy-compatible backend or pin compatible package versions rather than rewriting agent internals in-place.

## Gym Pendulum version differences

Symptoms:

- `gym.make('Pendulum-v0')` fails.
- `env.seed(...)` is missing.
- `env.reset()` returns a tuple but the agent expects an observation.
- Action bounds differ from actor output range.

Fixes:

- Try the environment ID supported by the installed Gym version, commonly `Pendulum-v1` in newer stacks.
- Use `env.reset(seed=...)` for newer Gym APIs; use `env.seed(...)` only when present.
- Unpack `(observation, info)` from newer `reset()` and `(observation, reward, terminated, truncated, info)` from newer `step()` if you write wrappers.
- Keep smoke tests independent of Gym by using the bundled compile helper.

## MuJoCo dependency, license, and hardware exclusions

Symptoms:

- Import errors for MuJoCo bindings or Gym MuJoCo environments.
- Missing native libraries, compiler errors, license/activation issues, or very long runs.
- Training appears stalled because the horizon is much longer than Pendulum examples.

Fixes:

- Do not use MuJoCo as a default smoke or verification target.
- First verify DDPG actor/critic wiring with a synthetic or Pendulum-style compile check.
- Treat simulator installation, license/terms, rendering, hardware acceleration, and benchmark duration as a separate, explicit task.
- Use action clipping/scaling processors for MuJoCo-style bounded actions.

## h5py and weight-file issues

Symptoms:

- `ImportError` or binary compatibility errors involving `h5py`.
- DDPG weights appear to save to unexpected filenames.
- Loading weights fails after moving or renaming only one file.

Fixes:

- Use an h5py version compatible with the chosen legacy Keras stack.
- DDPG `save_weights(filepath)` writes separate actor and critic files by inserting `_actor` and `_critic` before the extension; keep both files together.
- DDPG `load_weights(filepath)` expects the corresponding actor and critic files to exist.
- NAF saves/loads the combined model weights through a single filepath.
- Do not make weight persistence part of compile-only smoke checks; test it only when file I/O is explicitly in scope.
