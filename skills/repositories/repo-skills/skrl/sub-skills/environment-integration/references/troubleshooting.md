# Environment troubleshooting

Use this matrix to classify a failure before changing a model or trainer. First reproduce with `verbose=True`, print the original class and spaces, and run the bounded Gymnasium smoke when the issue is supposed to be a standard wrapper issue.

| Symptom | Likely boundary | Check | Recovery |
| --- | --- | --- | --- |
| `Unknown wrapper type` from `wrap_env` | Invalid tag or unsupported framework/environment combination | Compare the tag with the public signature; use `inspect.signature` or the framework table in `standard-environments.md` | Use exactly `gym`, `gymnasium`, `pettingzoo`, `mani-skill`, `playground`, or the Isaac Lab tags. For a custom class, choose an explicit supported tag. |
| `auto` logs a class list and then fails | Proxy/custom class does not expose a recognized base class | Inspect `type(env)`, `type(env.unwrapped)`, and their bases; do not assume the registry id determines the class | Select the explicit wrapper matching the API. If it is an external class, verify the corresponding optional package first. |
| Gymnasium object is passed to `wrapper="gym"` (or reverse) | API-family mismatch | Check which package created the object and whether reset returns `(obs, info)` | Recreate/use `wrapper="gymnasium"` for Gymnasium; use `wrapper="gym"` for Gym. Do not patch the returned tuple in an agent. |
| `ImportError: gym`, `pettingzoo`, `shimmy`, or simulator package | Optional dependency not installed/registered | Import only the package named by the chosen route and inspect the environment registration | Install the matching optional dependency in the user's own environment, or use the installed standard route. No bundled smoke installs packages. |
| `reset`/`step` shape or tuple unpacking error | Old/new API or wrong vectorization convention | Record `len(reset_output)`, `len(step_output)`, `env.num_envs`, and whether it is a `VectorEnv` | Use the correct wrapper. Keep `terminated` and `truncated` separate. For vectors, pass batch actions and expect batch outputs. |
| `ValueError: Unsupported space` or unsupported value type | Space/conversion boundary | Print `observation_space`, `action_space`, nested space types, and returned value dtypes | Use Box, Discrete, MultiDiscrete, Tuple, or Dict as supported; adapt the environment deliberately before skrl. Do not silently flatten a foreign space. |
| Action has wrong shape/dtype | Action was not built from the wrapped space | Compare action shape to the single-agent space and `num_envs`; inspect the framework tensor/array dtype | Build a flattened `(batch, features)` framework value; let `wrap_env` unflatten it. For discrete vectors, use one action column per environment. |
| `state()` is `None` | Environment has no state/state-space API | Check `env.state_space` and original `.state` | Use observation-only model inputs or provide a supported environment state. `None` is expected for Pendulum. |
| `num_envs` is `1` unexpectedly | Original object is not a recognized vector environment or does not expose `num_envs` | Check the original class and vector factory; inspect `single_observation_space` | Construct the vector environment before wrapping and use the matching vector API. Do not multiply a scalar environment's output manually. |
| `env.device` is not the desired accelerator | Original environment/device or framework default differs from the requested run | Print `env.device` and the framework's own device configuration; distinguish wrapper device from simulator device | Configure the selected framework and simulator explicitly. A CPU wrapper smoke does not establish CUDA compatibility. |
| Repeated vector `reset()` returns the same observation | Expected autoreset handling | Check `isinstance(original, gymnasium.vector.VectorEnv)` and call one step | The wrapper caches the first reset for vectorized environments; step updates the cached observation/info. Do not interpret this as a stuck simulator without checking the step result. |
| `render()` fails or returns no image | Headless/vector/external renderer boundary | Check render mode and whether the original is vectorized or headless | Omit render in headless checks; vector wrappers call the vector `call("render")` path. Configure rendering in the source simulator, not in the agent. |
| Isaac Lab loader says no task name / unknown task | Loader CLI/registration boundary | Confirm `task_name` or `--task`, task package registration, and launcher invocation | Supply a registered task. Remember command-line values override function parameters; launch through the simulator's supported app entry point. |
| Isaac Lab fails before wrapper construction | Simulator, asset, launcher, graphics, or GPU prerequisite | Import/probe the simulator in its own documented environment; inspect task/asset/device errors | Stop at the prerequisite failure; do not classify it as a skrl wrapper failure or retry with a different algorithm. |
| ManiSkill says task/backend/registration is missing | ManiSkill registration or simulator backend | Import its registration module before `gym.make`; check task id, `obs_mode`, control mode, backend and assets | Fix ManiSkill's environment first. Then pass the resulting Gymnasium object to `wrapper="mani-skill"`. |
| Playground reports invalid task or missing episode length | Loader config/registry boundary | List the supported registry tasks and inspect required loader arguments | Provide a valid task and episode length (or a task default); then wrap with `playground`. |
| PettingZoo action/observation dictionaries do not align | Wrong API or changing active-agent set | Compare `agents` with `possible_agents`; verify Parallel API and each agent's spaces | Use the parallel API and per-agent dictionaries; hand off to [multi-agent-and-runner](../../multi-agent-and-runner/SKILL.md). |

## Safe diagnostic sequence

1. Run `python sub-skills/environment-integration/scripts/wrap_gymnasium_smoke.py --help`.
2. Run it with the selected installed framework (`torch`, `jax`, or `warp`).
3. For a real object, print its package/class, `unwrapped` class, spaces, and `num_envs` before calling `wrap_env`.
4. Set `verbose=True` and use an explicit tag.
5. Confirm one reset, one step with a space-derived action, and `close()` in a `finally` block.
6. Only after the wrapper passes, route space/model issues to the framework skill or multi-agent runner skill.

Do not use this sequence to start a simulator, install assets, run training, or validate GPU performance. Those are separate integration tasks.
