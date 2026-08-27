# Workflows: Configs, Environments, Gym, and VectorEnv

Use these recipes to build Habitat-Lab task/data workflows while avoiding accidental downloads, simulator startup, or graphics-dependent work until the user has assets and runtime support.

## Safe Config Inspection

1. Run the bundled smoke script first when the user only needs config/data diagnostics:
   `python sub-skills/tasks-datasets-and-envs/scripts/habitat_config_smoke.py --config benchmark/nav/pointnav/pointnav_habitat_test.yaml`
2. Add overrides as repeated trailing values after `--override`, for example `--override habitat.dataset.split=val habitat.seed=7`.
3. Use `--make-dataset` only when the user wants to verify the registered dataset class and local episode files. This can fail if data is absent, but it still does not create a simulator.
4. Do not construct `habitat.Env` until scene assets, episode files, simulator backend, and graphics/GPU requirements are expected to be present.

## Config-to-Dataset-to-Env

1. Compose a task config with `habitat.get_config(config_path, overrides=[...])`.
2. Inspect `config.habitat.dataset.type`, `split`, `data_path`, `scenes_dir`, and `content_scenes`. `data_path` commonly contains `{split}`.
3. Build the dataset explicitly when you need to inspect/filter episodes before simulator startup:
   `dataset = habitat.make_dataset(id_dataset=config.habitat.dataset.type, config=config.habitat.dataset)`.
4. Optionally filter/split episodes with `dataset.filter_episodes(...)`, `dataset.get_scene_episodes(...)`, or `dataset.get_splits(...)`.
5. Construct `with habitat.Env(config=config, dataset=dataset) as env:` only after data and Habitat-Sim are ready.
6. Call `env.reset()` before `env.step(...)`. Use `env.action_space`, `env.observation_space`, `env.current_episode`, and `env.get_metrics()` for inspection.

## Editing Config Values

Habitat configs are read-only after `get_config()` patching. To mutate config nodes in code, use `habitat.config.read_write.read_write` or `habitat.read_write`:

```python
config = habitat.get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
with habitat.read_write(config):
    config.habitat.dataset.split = "val"
    config.habitat.environment.max_episode_steps = 50
```

Prefer Hydra overrides for command-line or reproducible scripts:

```python
config = habitat.get_config(
    "benchmark/nav/pointnav/pointnav_habitat_test.yaml",
    overrides=["habitat.dataset.split=val", "habitat.environment.max_episode_steps=50"],
)
```

## Navigation Workflows

- PointNav configs live under `benchmark/nav/pointnav/` and use task config `habitat/task/pointnav` with dataset configs under `habitat/dataset/pointnav/`.
- The small test config is `benchmark/nav/pointnav/pointnav_habitat_test.yaml`; it targets `data/datasets/pointnav/habitat-test-scenes/v1/{split}/{split}.json.gz` and Habitat test scenes.
- ObjectNav configs live under `benchmark/nav/objectnav/` and use `ObjectNav-v1` datasets with semantic scene/category requirements.
- ImageNav and InstanceImageNav configs live under `benchmark/nav/imagenav/` and `benchmark/nav/instance_imagenav/`.
- Use `ShortestPathFollower(env.sim, goal_radius, return_one_hot=False)` only after simulator creation. It needs valid navmesh/scene assets.
- Top-down map examples require adding `top_down_map` measurements before environment creation and require a simulator-backed environment.

## Rearrangement Workflows

- Rearrangement configs live under `benchmark/rearrange/`, with skill tasks under `skills/`, composite PDDL tasks under `multi_task/`, demos under `demo/`, and play configs under `play/`.
- Typical rearrangement configs compose `rearrange_sim`, an articulated agent, task actions/measurements/lab sensors, and `/habitat/dataset/rearrangement: replica_cad` or HSSD/Hab3 variants.
- `RearrangeDataset-v0` checks both episode dataset paths and scenes/assets; missing ReplicaCAD/HSSD assets should be reported as a data/setup skip, not fixed inside this sub-skill.
- Rearrangement Gym configs often set `habitat.gym.obs_keys` to restrict observations for a task such as pick, place, reach, or PDDL multi-task.
- Episode generation, custom PDDL authoring, and registration of new actions/sensors belong to other sub-skills unless the user only asks how to consume the resulting dataset/config.

## VLN and EQA Workflows

- VLN config `benchmark/nav/vln_r2r.yaml` composes `habitat/task: vln_r2r`, `habitat/dataset/vln: mp3d_r2r`, RGBD sensors, and MatterPort3D R2R episode data.
- VLN episodes expose `instruction`, `reference_path`, and `trajectory_id`; reference-path followers require simulator assets and are not config-only checks.
- EQA configs live under `benchmark/nav/eqa_*.yaml`, use MatterPort3D EQA data, and require the related MP3D scene assets.
- Skip runtime Env checks for VLN/EQA when MP3D scene access or EQA/VLN episode datasets are not available.

## Gym Wrapper Workflows

1. Ensure `import habitat.gym` happens before `gym.make(...)` so Habitat Gym IDs are registered.
2. Use generic config-backed Gym creation with `gym.make("Habitat-v0", cfg_file_path="benchmark/nav/pointnav/pointnav_habitat_test.yaml", override_options=[...])` when available through Gym's kwargs.
3. Use pre-registered rearrangement IDs such as `HabitatPick-v0` or `HabitatRenderPick-v0` only when their assets and rendering backend are available.
4. If `HabGymWrapper.step()` rejects an action, compare `env.action_space`, `env.original_action_space`, and `config.habitat.gym.action_keys`.
5. If observations are missing or have unexpected shape, inspect `config.habitat.gym.obs_keys`, `desired_goal_keys`, and `achieved_goal_keys`, then compare against the underlying Habitat `observation_space`.

## VectorEnv and Debug Mode

Use `VectorEnv` when multiple independent envs should step in parallel:

```python
configs = [config.copy() for _ in range(num_envs)]
env_fn_args = tuple((cfg,) for cfg in configs)
with habitat.VectorEnv(
    make_env_fn=habitat.gym.make_gym_from_config,
    env_fn_args=env_fn_args,
    multiprocessing_start_method="forkserver",
) as envs:
    observations = envs.reset()
```

When worker errors hang or hide the real exception:

- Reproduce in a single `Env` or `RLEnv` first whenever possible.
- Set `HABITAT_ENV_DEBUG=1` in baseline workflows that honor it; the factory switches to `ThreadedVectorEnv` for slower but clearer errors.
- Manually replace `VectorEnv` with `ThreadedVectorEnv` in custom debug scripts.
- Keep actions on CPU when using multiprocessing; CUDA tensors sent to workers can create CUDA contexts in subprocesses.
- Use `forkserver` or `spawn` after GPU initialization; only use `fork` if workers start before any GPU work.

## Validation Steps

- Config-only: run `habitat_config_smoke.py` without `--make-dataset` and confirm task, dataset, simulator, and environment fields.
- Dataset-only: add `--make-dataset` and expect either a dataset class/episode count or a clear missing-path failure.
- Single-env: construct `Env`, call `reset()`, inspect observation/action spaces, take one valid action, and close.
- Gym: make/import/register the Gym env, call `reset()`, sample or construct an action from `action_space`, and call one `step()`.
- VectorEnv: first pass a one-env vector; then scale up, splitting scenes or episodes so workers do not all load the same heavy scene unless intended.

## Skip Conditions

Skip or downgrade to config/dataset-only checks when any of these are true:

- Required scene assets or episode datasets are missing.
- Habitat-Sim is not installed, imports fail, or no compatible graphics/EGL/OSMesa backend is available.
- The workflow needs GPU rendering but the machine lacks suitable GPU/driver support.
- Rearrangement requires object assets, robot URDFs, motion files, physics configs, or scene dataset configs that are absent.
- VLN/EQA/ObjectNav require MP3D/HM3D/HSSD semantic assets that the user has not provided.
- Running native examples would write videos/images or need interactive graphics; keep them reference-only unless explicitly requested.
