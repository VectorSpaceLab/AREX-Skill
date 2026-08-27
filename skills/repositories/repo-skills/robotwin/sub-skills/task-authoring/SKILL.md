---
name: task-authoring
description: "Author RoboTwin tasks, task configs, language templates, and safe
  instruction-expansion workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# RoboTwin task authoring

Use this sub-skill when a user asks to add or modify a RoboTwin task, create a task configuration, edit language instructions, expand per-episode instructions, or understand the repository's LLM/code-generation utilities. If you only have the generated skill tree, use the root [workspace bootstrapper](../../references/workspace-bootstrap.md) first to materialize a pinned public workspace before editing runtime files.

## Route first

1. Work in the user's RoboTwin workspace. Runtime files here describe relative workspace files such as `envs/<task_name>.py`, `description/task_instruction/<task_name>.json`, and `env_cfg/task_config/<config_name>.yml`; do not edit this generated skill tree unless the user is updating the skill itself.
2. Decide whether the request can be deterministic. Prefer manual edits plus the bundled safe scripts below. Do not invoke Azure, OpenAI-compatible, DeepSeek, Moonshot, or other hosted model APIs unless the user explicitly asks and provides credentials.
3. For SAPIEN scene setup, `Base_Task`, actor/action helpers, robot/camera details, or render checks, route to [simulation-core](../simulation-core/SKILL.md). For demonstration collection, HDF5 layout, downloads, and conversion, route to [data-pipeline](../data-pipeline/SKILL.md).

## Main workflows

- **Task class and config authoring:** read [task-definition-workflow.md](references/task-definition-workflow.md), then use [scripts/create_task_config.py](scripts/create_task_config.py) when a safe config scaffold is useful.
- **Language templates and per-episode expansion:** read [language-instructions.md](references/language-instructions.md), then use [scripts/generate_episode_instructions.py](scripts/generate_episode_instructions.py) for deterministic local expansion.
- **Credential-bound generation utilities:** read [credentialed-generation.md](references/credentialed-generation.md) before explaining or running any LLM-backed task/object/code generator.
- **Failure diagnosis:** read [troubleshooting.md](references/troubleshooting.md) before changing assets, imports, generated code, or credential settings.

## Guardrails

- Keep canonical task implementations in `envs/<task_name>.py`; treat `envs_gen/gpt_<task_name>.py` as generated scratch code until manually reviewed and simulation-validated.
- Keep `play_once()` placeholder output synchronized with instruction templates. If `play_once()` returns `{"{A}": ..., "{a}": ...}`, every non-arm placeholder required by a template must be present in that `info` mapping.
- Do not assume RoboTwin is importable as an installed pip package. Many workflows expect commands to run from the RoboTwin workspace with local relative paths.
- Asset setup matters: top-level `envs` imports can fail before `assets/objects/objaverse/list.json` and other assets are present, especially when cluttered-table utilities are imported.
