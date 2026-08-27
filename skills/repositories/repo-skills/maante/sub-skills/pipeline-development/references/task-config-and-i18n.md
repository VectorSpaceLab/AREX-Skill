# Task Config and i18n

## Purpose

Use this reference when editing `assets/resource/tasks/*.json`, `assets/interface.json`, or interface locale files.

## Task JSON Shape

A task file contains a `task` list and an `option` object:

```json
{
  "task": [
    {
      "name": "MyTask",
      "label": "$task_my_task_label",
      "entry": "MyTaskEntrance",
      "description": "$task_my_task_desc",
      "option": ["MyOption"],
      "controller": ["Win32", "Win32-Front"]
    }
  ],
  "option": {
    "MyOption": {"type": "switch", "cases": []}
  }
}
```

Important rules:

- `name` is the task identifier shown to MaaFramework/MXU.
- `entry` must equal a Pipeline node key loaded by the resource.
- `label` and `description` usually use `$i18n_key` values.
- `option` lists option keys defined in the same file's top-level `option` object.
- `controller` restricts visibility/availability; omit only when the task is truly controller-agnostic.

## Option Types

### switch

Use for yes/no toggles. Cases usually patch `enabled`, `next`, or config attach fields.

```json
"Restock": {
  "type": "switch",
  "default_case": "No",
  "cases": [
    {"name": "Yes", "pipeline_override": {"点击补货": {"enabled": true}}},
    {"name": "No", "pipeline_override": {"点击补货": {"enabled": false}}}
  ]
}
```

### input

Use for text/numeric values. Input names are substituted into `pipeline_override` strings like `{count}`.

```json
"MakeCoffeeLoopTime": {
  "type": "input",
  "inputs": [{"name": "count", "default": "10", "pipeline_type": "int", "verify": "^\\d+$"}],
  "pipeline_override": {"AutoMakeCoffee": {"custom_action_param": {"count": "{count}"}}}
}
```

### select

Use for enumerated choices such as route schemes, thresholds, songs, and backends.

```json
"OnlineMapNavigationAngleBackend": {
  "type": "select",
  "default_case": "auto",
  "cases": [
    {"name": "auto", "pipeline_override": {"OnlineMapNavigationAngleBackendConfig": {"attach": {"angle_backend": "auto"}}}},
    {"name": "directml", "pipeline_override": {"OnlineMapNavigationAngleBackendConfig": {"attach": {"angle_backend": "directml"}}}}
  ]
}
```

## Interface Registration

Add new task files to `assets/interface.json` imports using resource paths such as:

```json
"resource/tasks/MyTask.json"
```

MaaNTE's interface file is JSONC-like and includes comments. Use a JSONC-aware editor or the bundled task catalog helper, not strict `json.load`, when parsing it.

## i18n Rules

MaaNTE uses five interface locale files:

- `zh_cn.json`
- `zh_tw.json`
- `en_us.json`
- `ja_jp.json`
- `ko_kr.json`

When adding or changing a task label/description key:

1. Add the key to all five locale files.
2. Keep task labels concise and descriptions specific to user-visible behavior.
3. Reuse global switch labels when appropriate: `$option_switch_case_yes`, `$option_switch_case_no`.
4. Do not leave raw `$missing_key` labels in UI-facing task files.

For OCR `expected`, the repository has a sync workflow/tool that can expand Chinese source strings into other languages. Regex or partial-match entries should be marked with the repository's i18n skip convention when they must not be auto-translated.

## Controller Restrictions

Use task-level `controller` restrictions when a workflow depends on foreground input, window focus, or unsupported background behavior. Examples from the snapshot:

- `PinkPawHeist`, `BagelSpam`, `Furniture`, `FountainCheckin`, `SoundDodge`, and character ability sync require `Win32-Front`.
- `ClaimRewards` and `WithdrawMoney` allow `Win32` and `Win32-Front`.
- Some tasks omit restrictions but their Python implementation may still have Windows-only internals; do not assume Linux/headless runtime.

## Validation Checklist

- Task file is imported by `assets/interface.json`.
- `entry` node exists in loaded Pipeline resources.
- Every task option key exists in top-level `option`.
- Every option case name matches the intended `default_case`.
- `pipeline_override` field shape matches the target node style.
- New label/description keys exist in all five locales.
- Controller restrictions are intentional and documented.
- JSON formatting follows repo conventions; run Prettier for JSON/YAML when available.
