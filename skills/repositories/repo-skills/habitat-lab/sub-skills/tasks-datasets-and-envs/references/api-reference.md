# API Reference: Tasks, Datasets, Environments

This reference captures the Habitat-Lab environment and dataset APIs an agent usually needs before writing or debugging task/data workflows.

## Core Object Relationships

- `habitat.get_config(config_path, overrides=None)` composes a Hydra/OmegaConf config and returns a read-only `DictConfig` whose top-level node normally contains `habitat`.
- `habitat.Env(config, dataset=None)` accepts either the full config or `config.habitat`. If `dataset` is `None` and `config.habitat.dataset.type` is set, `Env` calls `habitat.make_dataset(id_dataset=config.dataset.type, config=config.dataset)`.
- `Env` binds three major runtime components: `dataset` episodes, `simulator` from `habitat.sims.make_sim(id_sim=config.simulator.type, ...)`, and task from `habitat.tasks.registration.make_task(config.task.type, ...)`.
- When a dataset is present, `Env` requires a non-empty `episodes` list, builds an episode iterator from `environment.iterator_options`, sets `simulator.scene_dataset` and `simulator.scene` from the current episode, then creates the simulator/task.
- `habitat.RLEnv(config, dataset=None)` wraps `Env` as `gym.Env`. Subclasses must implement `get_reward_range()`, `get_reward(observations)`, `get_done(observations)`, and `get_info(observations)`.
- `habitat.gym.make_gym_from_config(config, dataset=None)` reads `habitat.env_task`, resolves an environment class, creates it through `habitat.utils.env_utils.make_env_fn`, and returns a Gym-compatible env.

## Verified Signatures

- `habitat.Env(config, dataset=None)`
- `habitat.RLEnv(config, dataset=None)`
- `habitat.VectorEnv(make_env_fn, env_fn_args, auto_reset_done=True, multiprocessing_start_method="forkserver", workers_ignore_signals=False)`
- `habitat.ThreadedVectorEnv(make_env_fn, env_fn_args, auto_reset_done=True, multiprocessing_start_method="forkserver", workers_ignore_signals=False)`; inherits `VectorEnv` API but runs workers as threads for easier debugging.
- `habitat.Dataset()` creates an object whose useful state is `episodes`, populated by subclasses or test fixtures.
- `habitat.core.dataset.Episode(...)` is keyword-only and extends `BaseEpisode`; required fields include `episode_id`, `scene_id`, `start_position`, and `start_rotation`. Defaults include `scene_dataset_config="default"`, `additional_obj_config_paths=[]`, and `info=None`.
- `habitat.make_dataset(id_dataset, **kwargs)` looks up a registered dataset class and returns `_dataset(**kwargs)`.

## `Env` Lifecycle

- Use a context manager: `with habitat.Env(config=config, dataset=dataset) as env:` to guarantee `env.close()`.
- `reset()` starts or advances an episode, calls `reconfigure()`, resets task sensors/measures, and returns an observation dictionary.
- `step(action)` requires `reset()` first and accepts an action name, integer, NumPy integer, or `{"action": ..., "action_args": ...}` dictionary. It updates measurements and episode-over state.
- `episode_over` becomes true when the task reports inactive or when `environment.max_episode_steps`/`max_episode_seconds` is exceeded.
- `current_episode`, `episodes`, `sim`, `task`, `observation_space`, `action_space`, `get_metrics()`, `render(mode="rgb")`, and `seed(seed)` are the common inspection hooks.
- Setting `env.episodes` requires an existing dataset and a non-empty episode list; setting `current_episode` or `episodes` requires `reset()` before the next `step()`.

## Dataset and Episode APIs

- `Dataset.scene_ids` returns sorted unique scene IDs from `episodes`.
- `Dataset.get_scene_episodes(scene_id)` filters episodes for a single scene.
- `Dataset.get_episode_iterator(...)` returns an `EpisodeIterator` with options including `cycle`, `shuffle`, `group_by_scene`, `max_scene_repeat_episodes`, `max_scene_repeat_steps`, `num_episode_sample`, `step_repetition_range`, and `seed`.
- `Dataset.filter_episodes(filter_fn)` returns a shallow copy with filtered episodes.
- `Dataset.get_splits(num_splits, episodes_per_split=None, remove_unused_episodes=False, collate_scene_ids=True, sort_by_episode_id=False, allow_uneven_splits=False)` creates split dataset copies without duplicating episodes.
- `Dataset.to_json()` serializes with Habitat's dataset JSON encoder; `from_json(json_str, scenes_dir=None)` is implemented by concrete dataset subclasses.
- Dataset subclasses typically implement `check_config_paths_exist(config)` and often fail fast when `data_path` or `scenes_dir` is missing.

## Task-Specific Episode Shapes

- `NavigationEpisode` extends `Episode` with `goals`, optional `start_room`, and optional `shortest_paths`.
- `NavigationGoal` contains `position` and optional `radius`.
- `ObjectGoalNavEpisode` adds `object_category`; `goals_key` is based on the scene basename and object category.
- `VLNEpisode` adds `reference_path`, `instruction`, and `trajectory_id`; `InstructionSensor` emits `text`, `tokens`, and `trajectory_id`.
- `RearrangeEpisode` adds `ao_states`, `rigid_objs`, `targets`, `markers`, `target_receptacles`, `goal_receptacles`, and `name_to_receptacle`.

## Gym APIs

- Importing `habitat.gym` registers generic Gym IDs `Habitat-v0` and `HabitatRender-v0`, plus pre-registered rearrangement IDs such as `HabitatPick-v0`, `HabitatRenderPick-v0`, `HabitatReachState-v0`, `HabitatTidyHouse-v0`, and related skill/multi-task names.
- `HabGymWrapper(env, save_orig_obs=False)` wraps an `RLEnv` and converts Habitat action/observation spaces into Gym spaces using `config.habitat.gym` fields.
- `gym.obs_keys` filters observation keys; if omitted, all observation keys are included.
- `gym.action_keys` filters action keys; if omitted, all task action keys are included.
- `desired_goal_keys` and `achieved_goal_keys` produce dict-style goal observations when non-empty.
- Continuous Habitat action spaces become `gym.spaces.Box`; discrete task action sets become `gym.spaces.Discrete`.

## VectorEnv APIs

- `VectorEnv` starts one worker process per `env_fn_args` tuple and calls `make_env_fn(*env_fn_args)` in each worker.
- Use `env_fn_args=tuple((config, dataset, rank) for ...)` when your constructor accepts those positional arguments, or `tuple((config,) for ...)` when using `make_gym_from_config`.
- `multiprocessing_start_method` must be one of `forkserver`, `spawn`, or `fork`; `forkserver` is the default and recommended around CUDA. If `fork` is used, start workers before any GPU usage.
- `reset()`, `reset_at(index)`, `step(actions)`, `async_step(actions)`, `wait_step()`, `step_at(index, action)`, `call_at(index, name, args=None)`, `call(names, args_list=None)`, `current_episodes()`, `count_episodes()`, `episode_over()`, `get_metrics()`, `pause_at(index)`, `resume_all()`, `render(mode="rgb_array")`, and `close()` are the main controls.
- With `auto_reset_done=True`, a worker automatically resets after returning a done step result.
- `ThreadedVectorEnv` is API-compatible and useful when multiprocessing hides the original Python exception.
