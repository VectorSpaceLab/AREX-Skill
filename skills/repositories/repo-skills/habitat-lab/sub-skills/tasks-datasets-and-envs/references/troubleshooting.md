# Troubleshooting: Env, Dataset, Gym, VectorEnv

Start with the safest failing layer: config load, then dataset construction, then single `Env`, then Gym, then `VectorEnv`.

## Config Does Not Load

Symptoms:

- `No file found for config ...`
- Hydra composition errors or missing config group errors.
- Override errors for unknown keys or malformed values.

Actions:

- Use package-relative configs such as `benchmark/nav/pointnav/pointnav_habitat_test.yaml`, not source-checkout paths.
- Run `scripts/habitat_config_smoke.py --config ...` without `--make-dataset` to isolate Hydra/config issues.
- Check override syntax: use `habitat.dataset.split=val`, and use Hydra `+group@path=value` syntax only when adding config groups.
- If the task is about installing or registering config search paths, route to `setup-and-configuration` or `extension-patterns`.

## Missing Scene or Dataset Paths

Symptoms:

- Dataset construction says `data_path` or `scenes_dir` is not downloaded locally.
- `Env` fails before reset because the dataset has zero episodes.
- Simulator fails opening `.glb`, `.basis.glb`, `.scene_instance.json`, or scene dataset config files.

Actions:

- Inspect `habitat.dataset.data_path.format(split=habitat.dataset.split)` and `habitat.dataset.scenes_dir`.
- Compare the task family to [data formats](data-formats.md) and verify both episode files and scene assets are present.
- For rearrangement, verify object assets, scene dataset configs, robot/articulated-agent files, and physics configs as well as episode `.json.gz` files.
- If data is unavailable, skip simulator/runtime checks and report a config/dataset-only result.
- Do not download data unless the user explicitly asks and setup policy allows it.

## Habitat-Sim, Graphics, or GPU Failures

Symptoms:

- Import errors for `habitat_sim`.
- EGL/OpenGL/OSMesa/display errors.
- Segfaults or context creation failures during `Env` construction or render.
- CUDA device errors, especially in vectorized workers.

Actions:

- Confirm whether the requested workflow truly needs simulator startup or rendering. Many config/data questions can stop at `get_config()` or `make_dataset()`.
- Use lower-risk configs and disable rendering-specific work where possible.
- Avoid `HabitatRender...` Gym IDs unless rendering is required and supported.
- Keep VectorEnv workers on `forkserver`/`spawn` around CUDA; avoid initializing CUDA before forking.
- Route installation/backend repair to `setup-and-configuration`.

## Dataset Is Empty or Wrong Split Loads

Symptoms:

- `dataset should have non-empty episodes list`.
- Episode count is zero.
- Expected validation/test episodes but train paths are used.

Actions:

- Check `habitat.dataset.split` and whether `data_path` contains `{split}`.
- Inspect `content_scenes`; `['*']` loads all scenes, while a specific list can filter every episode out if names do not match.
- Use `Dataset.scene_ids`, `num_episodes`, and `get_scene_episodes(scene_id)` before constructing `Env`.
- For vectorized workflows, ensure there are enough scenes or episodes to split among workers, or intentionally let each worker use all scenes.

## Invalid Action Space or Step Errors

Symptoms:

- `Cannot call step before calling reset`.
- `Episode over, call reset before calling step`.
- `Invalid action ... for action space ...`.
- Action dictionary has missing/incorrect `action_args`.

Actions:

- Always call `reset()` before `step()` and call `reset()` again after `episode_over` is true.
- Inspect `env.action_space` for Habitat actions and `gym_env.action_space` plus `gym_env.original_action_space` for Gym-wrapped envs.
- Use string/int actions only for discrete Habitat task actions; use `{"action": name, "action_args": {...}}` for parameterized actions.
- For Gym `Box` actions, pass a NumPy array with matching dtype/shape.
- If you changed `current_episode` or `episodes`, call `reset()` before stepping again.

## Observation Space or Gym Wrapper Mismatch

Symptoms:

- Key errors for missing observations.
- Unexpected dict vs array observations.
- Goal-conditioned Gym observations are missing `desired_goal` or `achieved_goal`.

Actions:

- Compare configured `habitat.gym.obs_keys`, `desired_goal_keys`, and `achieved_goal_keys` to the underlying Habitat `observation_space`.
- If a key is absent, check task lab sensors and simulator sensor config groups.
- Remember that `HabGymWrapper` collapses to a raw observation when only one observation group exists, and returns a dict when goal keys are configured.
- Avoid render Gym IDs unless a third-person render sensor and graphics backend are available.

## VectorEnv Hangs or Hides Worker Errors

Symptoms:

- Parent process hangs waiting for worker results.
- Broken pipe, EOF, or pickling errors with little context.
- Multiprocessing start method failures.

Actions:

- Reproduce with one plain `Env` or one Gym env first.
- Replace `VectorEnv` with `ThreadedVectorEnv` in custom scripts.
- In Habitat-Baselines env factory workflows, set `HABITAT_ENV_DEBUG=1` so the factory uses `ThreadedVectorEnv`.
- Ensure `env_fn_args` shape matches `make_env_fn` positional parameters.
- Keep `make_env_fn` importable/picklable and avoid lambdas or local closures when using multiprocessing.
- Use `workers_ignore_signals=False` while debugging so worker termination is easier to observe.

## Simulator Backend Fails During Rearrangement

Symptoms:

- Missing object template, articulated object, receptacle, PDDL, robot URDF, or motion data errors.
- Physics config or scene dataset config file failures.
- Rearrangement task starts but observations/measures are missing.

Actions:

- Verify the composed rearrangement config includes simulator, articulated-agent, task action, lab sensor, measurement, and dataset defaults.
- Check `habitat.simulator.scene_dataset`, `additional_object_paths`, agent URDF/motion fields, and episode `additional_obj_config_paths`.
- Use config/dataset-only checks if ReplicaCAD/HSSD/Hab3 assets are unavailable.
- Route custom task/PDDL/action/sensor authoring to `extension-patterns`; this sub-skill only covers consuming and diagnosing existing configs.

## Shortest Path and Top-Down Map Failures

Symptoms:

- `ShortestPathFollower` returns `None` unexpectedly.
- Top-down map metric is missing from `env.get_metrics()`.
- Navmesh/pathfinder errors.

Actions:

- Confirm the scene has a valid navmesh and the simulator was constructed successfully.
- Add the `top_down_map` measurement before creating the environment.
- Use the episode goal radius when present; otherwise use `config.habitat.simulator.forward_step_size` as a fallback radius.
- For VLN reference-path logic, iterate `current_episode.reference_path` first and then navigate to the final goal; this requires valid scene assets and VLN episodes.
