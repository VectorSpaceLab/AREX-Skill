# Extension and Environment API Reference

This reference maps MetaGPT extension and environment APIs to their responsibilities and safety boundaries. It names repo-relative evidence paths as provenance only; runtime use should rely on installed modules and the bundled recipes.

## AFlow Modules and Concepts

| API / module | Purpose | Notes |
| --- | --- | --- |
| `examples.aflow.optimize.parse_args()` | Argparse surface for AFlow optimizer CLI. | Safe to inspect with `--help`; full `main` path may download data and run optimization. |
| `examples.aflow.optimize.EXPERIMENT_CONFIGS` | Maps dataset names to `dataset`, `question_type`, and operator lists. | Choices: `DROP`, `HotpotQA`, `MATH`, `GSM8K`, `MBPP`, `HumanEval`. |
| `metagpt.ext.aflow.scripts.optimizer.Optimizer` | Main graph optimizer. | Constructor creates optimizer LLM and execution config, then `optimize("Graph")` runs repeated graph rounds. |
| `metagpt.ext.aflow.scripts.optimizer.GraphOptimize` | Pydantic output model for graph modification, graph, and prompt. | Filled by an `ActionNode` during optimization. |
| `metagpt.ext.aflow.scripts.evaluator.Evaluator` | Dataset dispatch and benchmark evaluation. | Add custom benchmarks to `dataset_configs` and dataset type choices. |
| `metagpt.ext.aflow.benchmark.benchmark.BaseBenchmark` | Abstract dataset benchmark base. | Implement `evaluate_problem`, `calculate_score`, and `get_result_columns`. |
| `metagpt.ext.aflow.scripts.optimizer_utils.GraphUtils` | Loads/writes graph files, reads template operators, builds graph optimization prompts. | Requires `workflows/template/operator.json` for selected operators. |
| `metagpt.ext.aflow.scripts.optimizer_utils.DataUtils` | Loads/saves optimization results and selects candidate rounds. | Output lives under the configured optimized path. |
| `metagpt.ext.aflow.scripts.optimizer_utils.ExperienceUtils` | Tracks optimization experience and duplicate modification checks. | Used to avoid repeating graph modifications. |
| `metagpt.ext.aflow.scripts.optimizer_utils.EvaluationUtils` | Executes validation/test graph evaluation. | Can produce many LLM calls. |
| `metagpt.ext.aflow.data.download_data.download(...)` | Downloads datasets and initial rounds. | Network download; exclude from safe helpers unless user authorizes. |

AFlow operator names seen in the example mapping include `Custom`, `AnswerGenerate`, `ScEnsemble`, `Programmer`, `CustomCodeGenerate`, and `Test`.

## SPO Modules and Concepts

| API / module | Purpose | Notes |
| --- | --- | --- |
| `examples.spo.optimize.parse_args()` | Argparse surface for SPO optimizer CLI. | Safe to inspect with `--help`. |
| `examples.spo.optimize.main()` | Initializes SPO LLM clients and runs `PromptOptimizer.optimize()`. | Calls LLMs; do not run as a safe check. |
| `metagpt.ext.spo.components.optimizer.PromptOptimizer` | Main prompt optimizer. | Uses `optimized_path/name/prompts` for rounds and results. |
| `metagpt.ext.spo.utils.llm_client.SPO_LLM` | Singleton LLM client for optimize/evaluate/execute request types. | Initialize with `optimize_kwargs`, `evaluate_kwargs`, and `execute_kwargs`. |
| `metagpt.ext.spo.utils.load` | Loads template metadata by file name. | Template must provide `prompt`, `requirements`, `count`, and `qa`. |
| `metagpt.ext.spo.utils.prompt_utils.PromptUtils` | Creates prompt round directories and writes prompt/answer files. | Writes under the chosen workspace. |
| `metagpt.ext.spo.utils.data_utils.DataUtils` | Loads results, selects best round, formats markdown. | Drives optimization feedback. |
| `metagpt.ext.spo.utils.evaluation_utils.EvaluationUtils` | Executes and evaluates prompts. | LLM-costing. |
| `metagpt.ext.spo.app` | Streamlit UI for template editing and optimization. | Requires Streamlit and browser access. |

SPO template fields:

| Field | Type / meaning |
| --- | --- |
| `prompt` | Initial prompt text for round 1. |
| `requirements` | Desired effects/outcomes used during optimization. |
| `count` | Target prompt word count or `None`. |
| `qa` | List of `{question, answer}` examples used for execution/evaluation. |

## Android Assistant APIs

| API / module | Purpose | Notes |
| --- | --- | --- |
| `examples.android_assistant.run_assistant.app` | Typer app for Android Assistant. | Hardware/service full run; parser help may import environment modules. |
| `startup(task_desc, n_round, stage, mode, app_name, ...)` | Creates `AndroidEnv`, hires `AndroidAssistant`, and runs a `Team`. | Initializes CV models and uses ADB/device actions. |
| `metagpt.environment.android.android_ext_env.AndroidExtEnv` | External Android environment with ADB, screenshot/XML, OCR, and touch/text APIs. | Constructor loads CV models and validates device id if supplied. |
| `metagpt.environment.android.android_env.AndroidEnv` | Combines `AndroidExtEnv` with `Environment`. | Used by Android Assistant team. |
| `metagpt.environment.android.env_space.EnvActionType` | Action enum: `NONE`, `SYSTEM_BACK`, `SYSTEM_TAP`, `USER_INPUT`, `USER_LONGPRESS`, `USER_SWIPE`, `USER_SWIPE_TO`. | Use for structured `step(...)` calls. |
| `metagpt.environment.android.env_space.EnvObsType` | Observation enum: `NONE`, `GET_SCREENSHOT`, `GET_XML`. | Use for screenshot/XML observation. |
| `AndroidExtEnv.get_screenshot(ss_name, local_save_dir)` | ADB screenshot capture and pull. | Requires writable device screenshot path and local directory. |
| `AndroidExtEnv.get_xml(xml_name, local_save_dir)` | `uiautomator dump` and pull. | Requires Android UI automation support. |
| `AndroidExtEnv.system_tap`, `user_input`, `user_swipe`, `user_swipe_to`, `system_back` | ADB write APIs. | Destructive/device-affecting; require explicit approval. |

Android Assistant CLI parameters include `task_desc`, `--n-round`, `--stage`, `--mode`, `--app-name`, `--investment`, `--refine-doc`, `--min-dist`, `--android-screenshot-dir`, `--android-xml-dir`, and `--device-id`.

## Environment Base APIs

| API | Purpose | Important behavior |
| --- | --- | --- |
| `metagpt.environment.base_env.ExtEnv` | Abstract base for external environments with Gymnasium-style spaces and API registries. | Subclasses must implement `reset`, `observe`, and `step`. |
| `metagpt.environment.base_env.Environment` | MetaGPT role-hosting environment. | Adds roles, publishes messages, runs idle roles, archives project state. |
| `mark_as_readable(func)` | Registers an environment read API. | Registered schemas are returned by `get_all_available_apis(mode="read")`. |
| `mark_as_writeable(func)` | Registers an environment write API. | Registered schemas are returned by `get_all_available_apis(mode="write")`. |
| `read_from_api(env_action)` | Dispatches a registered read API by string or `EnvAPIAbstract`. | Raises `KeyError` for unknown API names. |
| `write_thru_api(env_action)` | Dispatches a registered write API or publishes a `Message`. | Supports one `EnvAPIAbstract`; list support is not implemented in the inspected body. |
| `EnvAPIAbstract(api_name, args, kwargs)` | Parameter carrier for read/write API calls. | Prefer `kwargs` for clarity. |
| `EnvAPIRegistry` | Stores API schemas/functions and exposes `get_apis()`. | `get(api_name)` raises `KeyError` when missing. |
| `EnvType` | Enum values `ANDROID`, `GYM`, `WEREWOLF`, `MINECRAFT`, `STANFORDTOWN`. | Use as conceptual routing labels; concrete factory support may be limited. |

## Concrete Environment Modules

| Environment | Main class | Read/write/actions | Safety notes |
| --- | --- | --- | --- |
| Software | `metagpt.environment.software.software_env.SoftwareEnv` | Alias of `Environment`. | Route ordinary software-company work to the sibling sub-skill. |
| MGX | `metagpt.environment.mgx.mgx_env.MGXEnv` | Public/direct chat routing, image attachment, team-leader mediated publishing. | Used by core team workflows. |
| Android | `AndroidEnv` / `AndroidExtEnv` | ADB screenshot/XML/tap/text/swipe APIs. | Requires device/emulator and optional CV models. |
| Stanford Town | `StanfordTownExtEnv`, `StanfordTownEnv` | Tile observation/event mutation APIs and simulation roles. | Requires maze assets/storage and LLM budget for full simulation. |
| Werewolf | `WerewolfExtEnv`, `WerewolfEnv` | Game setup, step instructions, vote/hunt/protect/poison/save APIs. | Full game uses LLM roles and may use experience stores. |
| Minecraft | `MinecraftExtEnv`, `MinecraftEnv` | Mineflayer process, HTTP `/start`/`/step`/`/pause`/`/stop`, checkpoint/vectordb state. | Requires Node/Minecraft service and explicit process approval. |

## Stanford Town Environment APIs

`StanfordTownExtEnv` loads maze metadata, collision maps, sector/arena/game-object/spawn matrices, event tuples, and reverse address-tile indexes from a maze asset path.

Key observation APIs:

| API | Purpose |
| --- | --- |
| `reset()` | Returns full observation with `collision_maze`, `tiles`, and `address_tiles`. |
| `observe(EnvObsParams(obs_type=EnvObsType.NONE))` | Full observation. |
| `observe(... GET_TITLE ...)` | Tile detail dictionary for a coordinate. |
| `observe(... TILE_PATH ...)` | Address path for a tile at a level such as `world`. |
| `observe(... TILE_NBR ...)` | Nearby tiles for a coordinate and vision radius. |
| `get_collision_maze()` | Collision matrix. |
| `get_address_tiles()` | Reverse address index. |
| `access_tile(tile)` | Tile detail dictionary. |
| `get_tile_path(tile, level)` | Address string at requested path level. |
| `get_nearby_tiles(tile, vision_r)` | Neighborhood tile coordinates/details. |

Key write APIs/actions:

| API / action | Purpose |
| --- | --- |
| `ADD_TILE_EVENT` / `add_event_from_tile(event, tile)` | Add an event tuple to a tile. |
| `RM_TILE_EVENT` / `remove_event_from_tile(event, tile)` | Remove an exact event tuple. |
| `TURN_TILE_EVENT_IDLE` / `turn_event_from_tile_idle(event, tile)` | Mark an event idle. |
| `RM_TITLE_SUB_EVENT` / `remove_subject_events_from_tile(subject, tile)` | Remove events by subject. |

Event tuple shape is `(subject, predicate, object, description)` with optional trailing values often `None`.

## Werewolf Environment APIs

`WerewolfExtEnv` maintains `players_state`, round/step indexes, role groups, night/day action state, witch resource counts, winner, and win reason.

Important APIs:

| API | Purpose |
| --- | --- |
| `init_game_setup(role_uniq_objs, num_villager, num_werewolf, shuffle, add_human, ...)` | Creates players, assigns role profiles, initializes `players_state`, and returns setup plus players. |
| `step(EnvAction(...))` | Applies a werewolf action and returns observation/reward/done info. |
| `curr_step_instruction()` | Returns the current scripted step instruction and increments `step_idx`. |
| `get_players_state(player_names)` | Returns role state for named players. |
| `living_players`, `werewolf_players`, `villager_players` | Derived player lists. |
| `wolf_kill_someone`, `vote_kill_someone`, `witch_poison_someone`, `witch_save_someone`, `guard_protect_someone` | Role-specific write APIs with step/role guards. |
| `progress_step()` | Increments `step_idx`. |

Werewolf `EnvActionType` values are `NONE`, `WOLF_KILL`, `VOTE_KILL`, `WITCH_POISON`, `WITCH_SAVE`, `GUARD_PROTECT`, and `PROGRESS_STEP`.

## Minecraft Environment APIs

`MinecraftExtEnv` starts/stops a Mineflayer subprocess and calls a local HTTP server. `MinecraftEnv` adds shared memory for tasks, generated code, programs, skills, QA cache, chest memory, and completed/failed tasks.

Important fields and APIs:

| API / field | Purpose |
| --- | --- |
| `server_host`, `server_port`, `request_timeout` | HTTP bridge connection settings. |
| `mineflayer` | `SubprocessMonitor` for the Node bridge process. |
| `set_mc_port(mc_port)` | Sets Minecraft port and resume state in `MinecraftEnv`. |
| `check_process()` | Starts/restarts Mineflayer and posts `/start`. |
| `_reset(options={...})` | Resets server state, inventory/equipment/position, and pauses server. |
| `_step(code, programs="")` | Sends executable code to `/step`; requires reset first. |
| `pause()` / `unpause()` / `close()` | Controls the bridge/server process. |
| `append_skill`, `update_task`, `update_code`, `update_program_code`, `update_critique` | Shared state updates for Minecraft agents. |

Do not use `_step` for untrusted code or without explicit user approval.

## CR APIs

| API | Purpose | Notes |
| --- | --- | --- |
| `metagpt.ext.cr.actions.code_review.CodeReview` | LLM-assisted patch review. | Supports Python and Java patch files in the inspected path. |
| `CodeReview.cr_by_points(patch, points)` | Produces raw comments by comparing patch hunks to `Point` standards. | LLM call. |
| `CodeReview.confirm_comments(patch, comments, points)` | Filters comments through another LLM judgment. | LLM call. |
| `CodeReview.run(patch, points, output_file)` | Writes review logs and final comments. | Uses `EditorReporter`. |
| `metagpt.ext.cr.actions.modify_code.ModifyCode` | Generates patch modifications from comments. | LLM-generated diff requires review. |
| `metagpt.ext.cr.utils.schema.Point` | Review standard schema. | Fields include `id`, `text`, `language`, `file_path`, line bounds, examples, and `detail`. |

## SELA APIs

| API / module | Purpose |
| --- | --- |
| `metagpt.ext.sela.run_experiment.get_args(cmd=True)` | Argparse setup and custom-dataset normalization. |
| `--exp_mode` | Chooses `MCTSRunner`, `RandomSearchRunner`, base `Runner`, `GluonRunner`, `AutoSklearnRunner`, or custom/greedy/random modes. |
| `--rollouts`, `--max_depth`, `--role_timeout` | MCTS depth/cost controls. |
| `--from_scratch`, `--load_tree`, `--use_fixed_insights` | Insight/tree behavior. |
| `--custom_dataset_dir` | Switches to MLE-style task id, lower-is-better detection, external eval disabled, and `from_scratch=True`. |
| `data.yaml` | Configures `datasets_dir`, `work_dir`, and `role_dir`. |
| `datasets.yaml` | Dataset prompts/metrics/target columns. |

SELA runner modes can require heavy optional packages such as AutoGluon or AutoSklearn; validate selected mode-specific dependencies before running.
