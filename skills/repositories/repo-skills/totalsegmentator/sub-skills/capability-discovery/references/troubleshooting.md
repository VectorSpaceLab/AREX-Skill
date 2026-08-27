# Capability Discovery Troubleshooting

Use this reference when TotalSegmentator task/class discovery or ROI validation fails before a segmentation run.

## Failure Matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `--classes requires --task/-ta` | `totalseg_info --classes` was called without a task. | Run `totalseg_info --classes -ta total` or choose a task from `totalseg_info --list-tasks`. |
| `unknown task` or `invalid choice` | The task is misspelled, from another package version, or not selectable. | Run `totalseg_info --list-tasks --json` and copy the exact `name` value. |
| ROI validation says a class is invalid | `--roi_subset` names are task-specific and exact-match. | Run `totalseg_info --classes -ta <task> --json`; use class-name values exactly, not label ids. |
| A class exists in one task but not another | Class maps differ by task and modality. | Validate ROI names against the same task that will be passed to `TotalSegmentator -ta` or `totalsegmentator(..., task=...)`. |
| A pipeline accidentally selects licensed tasks | The task registry includes both open and license-required tasks. | Filter `license_required: false` or use `python scripts/dump_task_registry.py --only-open`; route license setup to `../runtime-configuration/SKILL.md`. |
| A task seems CT/MR-incompatible | Task modality was guessed from the name or README prose. | Use `totalseg_info --list-tasks --json` or `task_modality(task)`; at least one MR task does not rely only on an `_mr` suffix. |
| Automation cannot parse `TotalSegmentator --list-tasks` | Main CLI shortcuts are human-readable. | Use `totalseg_info --json`, `totalseg_info --list-tasks --json`, or the bundled JSON helper. |
| Discovery imports feel slow or heavy | Code imported `totalsegmentator.python_api` or the main CLI instead of the registry. | Import only `totalsegmentator.registry` or call `totalseg_info`; do not import segmentation runtime for planning. |
| JSON version is `null` or absent | The registry is being executed from an unpackaged source tree or unusual install state. | Continue using registry data for task/class validation, but record package provenance during integration or environment verification. |
| A README class name disagrees with CLI output | Documentation, installed version, or source checkout may be stale relative to the runtime package. | Trust the installed registry exposed by `totalseg_info` for executable plans. |

## Unknown Task Recovery

1. Run:

   ```bash
   totalseg_info --list-tasks --json
   ```

2. Search the `name` fields for the intended task.
3. If the desired anatomy is not obvious, inspect class maps for candidate tasks:

   ```bash
   totalseg_info --classes -ta total --json
   totalseg_info --classes -ta total_mr --json
   ```

4. If the task is license-required, decide whether to choose an open alternative or route license setup to `../runtime-configuration/SKILL.md`.

## Invalid ROI Recovery

1. Identify the exact task planned for the run.
2. Validate proposed classes:

   ```bash
   python scripts/dump_task_registry.py --validate-roi <task> <class> [<class> ...]
   ```

3. For each invalid class, use the helper's `suggestions` list or inspect the full class map:

   ```bash
   totalseg_info --classes -ta <task> --json
   ```

4. Replace invalid names with exact class-name values. Do not use label indices such as `1` unless a downstream output parser explicitly asks for labels.

## Choosing Open MR Tasks

For a pipeline that must avoid licenses and avoid importing torch:

```bash
python scripts/dump_task_registry.py --modality MR --only-open
```

Read `tasks` keys from the JSON result. If the result is empty in a future version, remove one filter at a time to determine whether modality names or license flags changed.

## When to Escalate to Other Sub-skills

- If discovery succeeds and the next step is a segmentation command, route to `../segmentation-workflows/SKILL.md`.
- If a task requires a license, route license installation/configuration to `../runtime-configuration/SKILL.md`.
- If the issue is a missing output file, run report content, statistics schema, or multilabel label mapping, route to `../outputs-and-statistics/SKILL.md`.
- If the issue is DICOM input detection or output format support, route to `../dicom-and-formats/SKILL.md`.
