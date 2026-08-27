# TotalSegmentator Capability Registry Reference

This reference explains how to discover TotalSegmentator tasks, classes, modalities, license flags, and valid ROI subset names without running a model.

## Evidence-Backed Facts

- Public package: `TotalSegmentator` version `2.14.0`, import module `totalsegmentator`.
- Console discovery entry point: `totalseg_info`.
- Registry module: `totalsegmentator.registry`.
- Current verified registry size: `47` selectable tasks.
- Current verified class counts: task `total` has `117` classes; task `total_mr` has `50` classes.
- Current verified license count: `15` tasks require a license.
- Safe discovery guarantee: `totalsegmentator.registry` and `totalseg_info` use pure registry data and do not require torch, GPU, model weights, or downloads.

Do not paste a frozen copy of the task or class table into downstream code. Query the installed registry at planning time so pipelines follow the installed package version.

## Discovery Commands

### Full JSON Registry

```bash
totalseg_info --json
```

Returns a JSON object with this shape:

```json
{
  "totalsegmentator_version": "2.14.0",
  "tasks": {
    "total": {
      "modality": "CT",
      "license_required": false,
      "classes": {"1": "spleen"}
    }
  }
}
```

The `classes` keys are label indices serialized as strings. The values are the exact class names accepted by `--roi_subset` for that task.

### Task Overview

```bash
totalseg_info --list-tasks
totalseg_info --list-tasks --json
```

Human output is a table with `TASK`, `MODALITY`, `LICENSE`, and `CLASSES`. JSON output is a list of objects:

```json
[
  {"name": "total", "modality": "CT", "license_required": false, "num_classes": 117}
]
```

Use this form to choose CT vs MR tasks or to filter out tasks requiring a license.

### Classes for One Task

```bash
totalseg_info --classes -ta total
totalseg_info --classes -ta total --json
```

Human output is an `index -> class_name` table. JSON output is the class map only:

```json
{"1": "spleen", "2": "kidney_right"}
```

`--classes` requires `--task/-ta`; omitting the task exits with an argument error.

### Main CLI Shortcuts

```bash
TotalSegmentator --list-tasks
TotalSegmentator --list-classes
TotalSegmentator --list-classes total_mr
```

These short-circuit before segmentation input/output is required. They are useful for humans, but `totalseg_info --json` is preferred for automation because it is designed for lightweight discovery and machine-readable output.

## Python Registry API

Use the registry module when a Python pipeline needs to plan tasks before running segmentation.

```python
from totalsegmentator.registry import (
    TASKS,
    get_task_classes,
    list_tasks,
    task_registry,
    task_modality,
    requires_license,
)

rows = list_tasks()
open_mr_tasks = [
    row["name"] for row in rows
    if row["modality"] == "MR" and not row["license_required"]
]
classes = get_task_classes("total")
assert "spleen" in classes.values()
```

Important API contracts:

- `TASKS`: selectable task names in CLI order.
- `list_tasks()`: list of `{name, modality, license_required, num_classes}` objects.
- `get_task_classes(task)`: returns `{label_index: class_name}` and raises `KeyError` for an unknown task.
- `task_registry()`: full JSON-serializable map with package version and per-task class maps.
- `task_modality(task)`: returns `"CT"` or `"MR"`.
- `requires_license(task)`: returns a boolean license flag.

## Bundled JSON Helper

The local helper `scripts/dump_task_registry.py` wraps the public registry API for pipelines that need filtered JSON or ROI validation.

Run from this sub-skill directory or pass the script path from your agent tool:

```bash
python scripts/dump_task_registry.py --help
python scripts/dump_task_registry.py
python scripts/dump_task_registry.py --task total
python scripts/dump_task_registry.py --modality MR --only-open
python scripts/dump_task_registry.py --validate-roi total spleen liver
```

Default/filter output schema:

```json
{
  "totalsegmentator_version": "2.14.0",
  "filters": {"task": null, "only_open": false, "modality": null},
  "num_tasks": 47,
  "tasks": {
    "total": {
      "modality": "CT",
      "license_required": false,
      "num_classes": 117,
      "classes": {"1": "spleen"}
    }
  }
}
```

ROI validation output schema:

```json
{
  "valid": false,
  "task": "total",
  "known_task": true,
  "modality": "CT",
  "license_required": false,
  "requested_classes": ["splen"],
  "valid_classes": [],
  "invalid_classes": [
    {"name": "splen", "suggestions": ["spleen"]}
  ]
}
```

The helper exits `0` for successful dumps and valid ROI requests, and `2` for invalid tasks, filters, or ROI names. It still emits JSON for validation failures so automation can display corrections.

## ROI Subset Validation

`--roi_subset` names must match the selected task's registry class names exactly.

Recommended planning flow:

1. Choose a task with `totalseg_info --list-tasks --json` or `list_tasks()`.
2. Query that task's classes with `totalseg_info --classes -ta <task> --json`.
3. Validate every requested ROI name against the returned class values.
4. Pass only validated class names to `TotalSegmentator --roi_subset ...` or `totalsegmentator(..., roi_subset=[...])`.

Example:

```bash
python scripts/dump_task_registry.py --validate-roi total spleen colon brain
```

If any class is invalid, query the same task's class list and replace the name; do not guess from another task, a previous release, or a README table.

## License and Modality Filtering

Use license/modality filters before constructing a segmentation plan.

Examples:

```bash
python scripts/dump_task_registry.py --only-open
python scripts/dump_task_registry.py --modality CT --only-open
python scripts/dump_task_registry.py --modality MR --only-open
```

Interpretation rules:

- `modality` describes the image family the task is intended for: `CT` or `MR`.
- `license_required: true` means the task needs a TotalSegmentator license before execution.
- This sub-skill only discovers and filters license flags; license setup and config storage are handled by `../runtime-configuration/SKILL.md`.

## Routing Notes

- Discovery and validation end once you have selected task names and ROI class names.
- Running segmentation belongs to `../segmentation-workflows/SKILL.md`.
- Parsing `--report`, `statistics.json`, multilabel labels, probabilities, or combined masks belongs to `../outputs-and-statistics/SKILL.md`.
- DICOM/NIfTI input/output format handling belongs to `../dicom-and-formats/SKILL.md`.
