# Task Selection and Capability Discovery

TotalSegmentator has many CT and MR segmentation tasks. Choose tasks and ROI class names from the installed registry instead of copying static lists into prompts or scripts.

## Discovery Commands

Use the lightweight discovery CLI first:

```bash
totalseg_info --list-tasks
totalseg_info --classes -ta total
totalseg_info --json
```

`totalseg_info` reads the package registry and does not need model weights, a GPU, or a segmentation input. It is the safest planning-time entry point for automation.

The main CLI also exposes discovery shortcuts:

```bash
TotalSegmentator --list-tasks
TotalSegmentator --list-classes total
```

Prefer `totalseg_info` in scripts because it is dedicated to discovery and can emit scoped JSON.

## Registry API

For Python planning code:

```python
from totalsegmentator.registry import list_tasks, get_task_classes, task_registry

open_ct_tasks = [
    row["name"]
    for row in list_tasks()
    if row["modality"] == "CT" and not row["license_required"]
]
classes = get_task_classes("total")
```

Useful registry facts verified for TotalSegmentator 2.14.0:

- The registry exposes 47 selectable tasks.
- `total` has 117 classes.
- `total_mr` has 50 classes.
- 15 selectable tasks require a license.
- Task modality is derived from task metadata, not from input files.

## Choosing a Task

1. Start with `total` for general CT segmentation and `total_mr` for general MR segmentation.
2. Use subtask names when the user asks for a narrower anatomy or specialized model.
3. Check `license_required` before promising a run can complete.
4. Use `get_task_classes(task)` or `totalseg_info --classes -ta <task>` before adding `--roi_subset`.
5. Route DICOM modality checks to the DICOM/formats sub-skill when the input is a DICOM folder or zip.

## ROI Subsets

`--roi_subset` values are class names, not task names or free-text anatomy labels:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ -ta total --roi_subset liver spleen --report seg/run_report.json
```

Validation pattern:

```bash
python sub-skills/capability-discovery/scripts/dump_task_registry.py \
  --task total \
  --validate-roi total liver spleen \
  --json
```

If a requested anatomy is not in the selected task, either choose a different task or explain that TotalSegmentator does not expose that class in the installed registry.

## License-Aware Planning

When a task is licensed:

- Do not embed or print license keys.
- Use runtime configuration to check whether a license is saved and whether offline shape validation can pass.
- Expect model-weight download for licensed models to require valid license state.
- Keep open-license fallback tasks separate from licensed-task promises.

## Automation Rule

A robust pipeline should persist the discovery result it used to plan a run, then compare the completed `run_report.json` against that plan. This catches version drift, task changes, class filtering, device fallback, and missing output files without parsing human stdout.
