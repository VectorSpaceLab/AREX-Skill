---
name: pipeline-development
description: "Guides MaaNTE Pipeline JSON, task option JSON, i18n, SceneManager,
  controller restrictions, and registry changes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Pipeline Development

## Use This When

Use this sub-skill when the task involves `assets/resource/base/pipeline/**/*.json`, `assets/resource/tasks/*.json`, `assets/interface.json`, UI i18n files, SceneManager public interfaces, or Pipeline recognition/action flow design.

Typical prompts:

- Add a new MaaNTE task or task option.
- Modify a Pipeline node, ROI, recognition threshold, action, `next`, `on_error`, or `pipeline_override`.
- Debug why a task option does not affect a node.
- Register a task in the interface import list.
- Update labels/descriptions across five locale files.
- Add a scene-navigation interface or avoid direct private SceneManager usage.

## Read First

1. [references/pipeline-patterns.md](references/pipeline-patterns.md) for Pipeline JSON style, recognition/action patterns, flow control, delays, and SceneManager rules.
2. [references/task-config-and-i18n.md](references/task-config-and-i18n.md) for task JSON, options, `pipeline_override`, interface imports, and locale requirements.
3. [references/troubleshooting.md](references/troubleshooting.md) for missing nodes, OCR/template mismatch, controller problems, and SceneManager misroutes.
4. [../../references/maa-framework-patterns.md](../../references/maa-framework-patterns.md) for verified MaaFramework binding and Pipeline semantics used across the repo.
5. Run `scripts/validate_pipeline_json.py` when you need a quick node-structure check, or `../../scripts/inspect_task_catalog.py` when checking task registry or option coverage.

## Operating Rules

- Coordinates, click targets, image templates, and ROI rectangles are based on 1280×720.
- Prefer nested v2 shape for new nodes:

  ```json
  "recognition": {"type": "OCR", "param": {"roi": [0, 0, 100, 40], "expected": ["完整文本"]}},
  "action": {"type": "Click"}
  ```

- Preserve existing local shorthand style when making a narrow edit in an old node, but do not mix incompatible forms inside the same field.
- Every action should follow recognition. A `DirectHit` is acceptable only after another node has proven state or for explicit config/entry placeholders.
- Do not solve missed states by adding broad loops or `max_hit` blindly. Add a state node, popup/loading handler, or clearer `next` branch.
- If a node truly needs no default wait, set `rate_limit`, `pre_delay`, and `post_delay` explicitly to `0`.
- Use `[JumpBack]` for popups, loading, scene transitions, and shared handlers that should return to the parent node.
- Use public SceneManager interface nodes from `Interface/Scene/`; do not route task pipelines directly to private `__ScenePrivate*` nodes.
- OCR `expected` values should use complete text; if a partial/regex string must skip i18n sync, mark that in source comments according to repo convention.

## New Task Checklist

1. Create or update `assets/resource/base/pipeline/<TaskFamily>.json` with a clear entry node.
2. Create or update `assets/resource/tasks/<TaskName>.json` with `task`, `entry`, `option`, and optional `controller` fields.
3. Add the task file to `assets/interface.json` imports.
4. Add or update five interface locale files when labels/descriptions use `$key`.
5. If Python is needed, coordinate with [../custom-actions/SKILL.md](../custom-actions/SKILL.md) for custom action registration.
6. Run safe checks: task catalog inspection, JSON formatting, `git diff --check`, and targeted Pipeline node/manual tests when a live environment exists.

## Common Review Questions

- Does the `entry` node exist and route from all realistic starting states?
- Does every `next` list cover success, loading, popup, wrong-scene, and completion states relevant to the task?
- Are controller restrictions accurate for the required input/screenshot mode?
- Are option names, input names, and `pipeline_override` target nodes exact?
- Are new OCR strings synchronized or intentionally skipped?
- Does the task avoid blind multi-click sequences and hidden implicit delays?
