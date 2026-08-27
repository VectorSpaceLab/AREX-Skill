# Task-authoring troubleshooting

Use this reference for errors encountered while adding tasks, configs, language templates, object descriptions, or generated-code drafts.

## Quick triage

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No such task` during dynamic import | File/class/task name mismatch, missing `envs/<task_name>.py`, or command not run from the RoboTwin workspace. | Ensure file name, class name, instruction JSON name, and command argument all use the same snake_case task name. Run workspace commands from the workspace root. |
| `No valid instructions found` | Template placeholders do not match `play_once()`'s returned `self.info["info"]`. | Compare every non-arm placeholder in `seen`/`unseen` templates against the `info` keys. Arm placeholders may be omitted; non-arm placeholders may not. |
| Object description file error for `object/folder/baseN` | Placeholder value contains `/` or `\\`, so the expander treats it as an object-description ID, but the JSON is missing. | Add `description/objects_description/<object_folder>/<object_id>.json`, correct the asset ID, or use a plain phrase value instead. |
| Hosted API key error such as missing `AZURE_API_KEY` | A credential-bound generation module was imported or run. | Use manual authoring/deterministic expansion, or ask the user to explicitly provide credentials and approve hosted API use. |
| OpenAI-compatible provider authentication failure | `code_gen` provider variables are placeholders or user credentials are absent/invalid. | Do not edit source to paste secrets. Ask for user-approved credential configuration, provider, budget, and privacy constraints before retrying. |
| `instruction_num should be divisible by 12` | The task-instruction generator batches requests in groups of 12. | Use a multiple of 12, or skip the generator and edit `seen`/`unseen` manually. |
| Import failure mentioning `assets/objects/objaverse/list.json` | Assets have not been downloaded/prepared, and top-level `envs` imports load cluttered-object metadata. | Download/prepare assets, or avoid top-level `from envs import *` until assets exist. If only editing language/config files, use static checks that do not import `envs`. |
| XPolicyLab package/path errors | The XPolicyLab submodule is empty or not initialized in the user's checkout. | Ask the user to initialize submodules before policy evaluation or conversion workflows that require XPolicyLab. Task JSON/config authoring can often proceed without it. |
| `ModuleNotFoundError` for RoboTwin modules after `pip install` attempts | RoboTwin is not packaged as a pip-installable library in this checkout. | Run repository scripts from the workspace root or add the workspace root to `PYTHONPATH` for inspection commands. Do not claim a package install succeeded unless verified. |
| YAML parser missing | The active environment lacks PyYAML. | Install PyYAML in the user's approved environment or use a config template/edit path that does not require YAML parsing. |
| Generated code works once but fails under randomization | Arm choice, functional point IDs, object placement tolerances, or prohibited areas are too brittle. | Test with varied seeds; route motion and actor-placement details to `simulation-core`; keep configs minimally randomized until deterministic behavior passes. |
| Instructions saved to the wrong directory | The legacy description utility and current collection flow use different output naming/layout conventions. | Prefer an explicit `--scene-info` and `--output-dir` with the bundled expander. For collection outputs, use the `instruction/episode_0000000.json` style beside the episode data. |

## Placeholder mismatch checklist

1. Extract placeholders from every template: `{A}`, `{B}`, `{a}`, etc.
2. Inspect the task's `play_once()` return path and find `self.info["info"]`.
3. Ensure all non-arm placeholders in every accepted template appear in that info mapping.
4. Ensure object placeholder values are either plain phrases or valid object-description IDs.
5. If a template intentionally omits an arm placeholder, confirm it does not omit any object placeholder.
6. Run the bundled expander with `--dry-run --dedupe --max-num 3` and a small `scene_info.json` fixture.

## Config debugging checklist

1. Confirm the config file name matches the command's `<task_config>` argument.
2. Validate YAML syntax before running simulation.
3. Start with `render_freq: 0`, low `episode_num`, and simple `domain_randomization` until the task is stable.
4. Confirm `embodiment` names match the configured embodiment map and downloaded assets.
5. Keep `language_num` small for first checks, then increase it after templates expand correctly.
6. Route actual collection, HDF5 inspection, and conversion output validation to `data-pipeline`.

## Generated-code safety checklist

1. Treat `envs_gen/gpt_<task_name>.py` as scratch.
2. Review the generated `play_once()` for unsafe imports, unknown APIs, wrong actor names, changed class names, and hidden side effects.
3. Compare generated actor references with actual variables created by `load_actors()`.
4. Verify every `place_actor()` target pose and `functional_point_id` against available actor metadata.
5. Verify gripper state: tasks that require holding should not open early; tasks that require release should open and clear the arm.
6. Re-run instruction expansion after any generated-code adoption because placeholder keys or values may have changed.

## Asset and import pitfalls

RoboTwin task authoring often starts with static edits, but dynamic imports can execute utility code that expects downloaded assets. If assets are incomplete:

- Prefer `python -m py_compile envs/<task_name>.py` over importing `envs`.
- Validate JSON/YAML independently.
- Use the bundled expander with a standalone `--scene-info` fixture.
- Ask `simulation-core` before diagnosing renderer, SAPIEN, CUDA, cuRobo, or planner failures.

## Submodule pitfall

The XPolicyLab submodule can be empty in a shallow or non-recursive checkout. This blocks policy evaluation and some data-conversion workflows, but it should not block manual task class/config/language edits. If the user's request crosses into evaluation, policy serving, LeRobot conversion, or XPolicyLab-format conversion, route to the owning sub-skill and have the user initialize submodules first.
