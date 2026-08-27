# Task definition workflow

This reference helps a future agent add or modify a RoboTwin task without relying on credentialed generators. It assumes the user is working in a RoboTwin workspace and wants to edit workspace files, not this skill tree.

## What makes a task complete

A usable RoboTwin task normally has these pieces:

| Piece | Workspace location pattern | Purpose |
| --- | --- | --- |
| Task class | `envs/<task_name>.py` | Defines scene actors, scripted demonstration behavior, success checks, and episode placeholder values. |
| Language template | `description/task_instruction/<task_name>.json` | Holds `full_description`, optional placeholder `schema`, generation `preference`, and hand-written or generated `seen`/`unseen` instruction templates. |
| Object language descriptions | `description/objects_description/<object_folder>/<object_id>.json` | Maps asset identifiers such as `001_bottle/base0` to natural `seen` and `unseen` descriptions. |
| Task config | `env_cfg/task_config/<config_name>.yml` | Controls episode count, language count, randomization, cameras, embodiment, and data fields for collection/evaluation. |
| Optional generated scratch code | `envs_gen/gpt_<task_name>.py` | Output of credential-bound code-generation utilities; never canonical until reviewed. |

Use one exact lowercase snake_case task name across the task file, class, command arguments, instruction JSON name, and any generated-code scaffold. RoboTwin dynamic imports expect `envs.<task_name>` to expose a class named exactly `<task_name>`.

## Task class checklist

A conventional task file imports `Base_Task` and utilities, then defines a class like:

```python
from ._base_task import Base_Task
from .utils import *

class my_task(Base_Task):
    def setup_demo(self, **kwargs):
        super()._init_task_env_(**kwargs)

    def load_actors(self):
        ...

    def play_once(self):
        ...
        self.info["info"] = {"{A}": "plain object or asset/path id", "{a}": str(arm_tag)}
        return self.info

    def check_success(self):
        ...
```

Authoring rules derived from the repository task examples:

1. **`setup_demo()` delegates to `_init_task_env_()`.** Task-specific setup usually belongs in `load_actors()`, `play_once()`, and `check_success()`.
2. **`load_actors()` creates and records scene actors.** Typical helpers include random pose/object creators, SAPIEN boxes/URDFs, articulated object loading, and prohibited-area bookkeeping. Ask `simulation-core` for exact actor helper behavior.
3. **`play_once()` is both the scripted demonstration and language binding source.** It chooses arms (`ArmTag("left")` or `ArmTag("right")`), calls movement helpers, updates `self.info["info"]`, and returns `self.info`.
4. **`check_success()` must assert the task's final state.** It should use actor poses, articulation joint positions, gripper state, target proximity, or other direct simulator signals. Avoid judging only by whether the motion planner ran.
5. **Placeholders are part of the task contract.** If language templates use `{A}`, `{B}`, `{a}`, or `{b}`, `play_once()` must return those keys. Non-arm placeholder mismatches are a common cause of empty generated instructions.
6. **Object placeholder values can be either plain phrases or asset description IDs.** A value such as `red block` is inserted directly; a value such as `001_bottle/base0` is resolved against object-description JSON by the instruction expander.
7. **Do not promote generated code blindly.** If an LLM utility writes `envs_gen/gpt_<task_name>.py`, review every motion call, functional point, arm choice, gripper state, and success criterion before copying any logic into the canonical task file.

## Safe task config scaffolding

The repository includes a tiny shell helper that copies a task-config template. This sub-skill provides a safer Python replacement with dry-run support:

```bash
python <this-sub-skill>/scripts/create_task_config.py \
  --repo-root . \
  --config-name my_demo_clean \
  --from-template demo_clean \
  --episode-num 5 \
  --language-num 20 \
  --dry-run
```

Remove `--dry-run` to write `env_cfg/task_config/my_demo_clean.yml`. Use `--force` only when intentionally replacing an existing config. Use `--set dotted.key=value` for fields not exposed as first-class flags, for example:

```bash
python <this-sub-skill>/scripts/create_task_config.py \
  --repo-root . \
  --config-name visual_randomized \
  --from-template demo_randomized \
  --set domain_randomization.random_head_camera_dis=0.03 \
  --set camera.head_camera_type=Large_D435
```

Important config fields:

- `episode_num`: target number of successful demonstrations.
- `use_seed`: reuse `seed.txt` instead of searching for fresh successful seeds.
- `save_freq`: simulator save interval.
- `embodiment`: one embodiment for symmetric bimanual use, or a three-item mixed-arm form when the simulator workflow supports it.
- `language_num`: number of per-episode language variants requested.
- `eval_instruction`: `seen` or `unseen` split used by evaluation/data consumers.
- `domain_randomization`: background, cluttered table, table height, light, and camera randomization knobs.
- `camera`: head/wrist camera types and whether each stream is collected.
- `data_type`: RGB, depth, pointcloud, endpose, qpos, segmentation, and related outputs.
- `save_path`: base data directory. Collection appends `<task_config>/<task_name>/<embodiment>/`.

## Adding a new task manually

1. Pick a task name such as `place_widget_tray` and create `envs/place_widget_tray.py` with a matching `place_widget_tray` class.
2. Decide which actors and target poses are needed. Use existing task examples as patterns, but route detailed SAPIEN/actor helper questions to `simulation-core`.
3. Write `load_actors()` so every object used by `play_once()` exists, is stable, and has an appropriate prohibited area when clutter/randomized scenes need collision avoidance.
4. Write `play_once()` with explicit arm decisions and motion sequences. Return placeholder values from `self.info["info"]` as soon as they are known.
5. Write `check_success()` using physical state checks that would fail on common wrong outcomes: wrong target, object dropped, gripper still holding when it should release, articulation insufficiently opened/pressed, or arms not clear.
6. Create `description/task_instruction/place_widget_tray.json` with matching placeholders and at least a few hand-authored `seen` and `unseen` templates. Do not require LLM generation for this step.
7. If object placeholders use asset IDs such as `object_folder/base3`, ensure corresponding object-description JSON exists with `seen` and preferably `unseen` arrays. If it does not exist, either author the JSON manually or use a plain phrase placeholder value.
8. Create or copy a task config. Prefer a small episode count and `render_freq: 0` for first scripted checks; only increase randomized settings after the deterministic task succeeds.
9. Run cheap checks first: Python syntax compile on the new file and JSON/YAML parsing. Then run simulator checks only in an environment with assets and rendering/backend prerequisites ready.
10. Hand off collection/output validation to `data-pipeline` after the task and instructions are consistent.

## Validation ladder

Use the cheapest checks that can reveal the current class of errors:

1. **Static file checks:** parse the task JSON, object-description JSON, and task config YAML; compile the task Python file.
2. **Placeholder dry run:** use the bundled instruction-expansion script with a tiny `scene_info.json` fixture and `--dry-run` to prove templates match `play_once()` placeholder keys.
3. **Import smoke:** import only the specific task module if assets are installed. Top-level `envs` imports may load cluttered-object metadata and fail before assets are downloaded.
4. **Render/backend smoke:** route to `simulation-core`; SAPIEN rendering and CUDA/device checks are outside task-authoring scope.
5. **Tiny collection/evaluation:** route to `data-pipeline`; start with a very small `episode_num` and inspect `scene_info`, `instruction`, and HDF5 outputs.
