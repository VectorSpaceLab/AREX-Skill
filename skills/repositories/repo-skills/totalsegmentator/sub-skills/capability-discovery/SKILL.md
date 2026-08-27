---
name: capability-discovery
description: "Discover TotalSegmentator tasks, classes, modalities, license
  flags, and ROI subset names without loading models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Capability Discovery

Use this sub-skill when an agent needs to inspect what TotalSegmentator can segment before planning a run. It owns safe discovery through `totalseg_info`, `totalsegmentator.registry`, and the bundled registry helper.

## Start Here

- Use `totalseg_info --json` for the full machine-readable capability registry: tasks, modality, license flag, and class maps.
- Use `totalseg_info --list-tasks` to show every selectable task with modality, license requirement, and class count.
- Use `totalseg_info --classes -ta <task>` to list valid class names for one task; these names are the valid `--roi_subset` values.
- Use [`scripts/dump_task_registry.py`](scripts/dump_task_registry.py) when a pipeline needs JSON filtering by task, modality, open-license status, or ROI validation.
- Read [`references/registry-reference.md`](references/registry-reference.md) for command/API schemas and common planning recipes.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when task names, class names, license filters, or discovery commands fail.

## Routing Boundaries

- For actual `TotalSegmentator -i ... -o ...` runs or `python_api.totalsegmentator(...)`, route to [`../segmentation-workflows/SKILL.md`](../segmentation-workflows/SKILL.md).
- For run reports, statistics, multilabel outputs, probabilities, or mask combination, route to [`../outputs-and-statistics/SKILL.md`](../outputs-and-statistics/SKILL.md).
- For license setup, model weights, offline caches, devices, installs, or usage telemetry, route to [`../runtime-configuration/SKILL.md`](../runtime-configuration/SKILL.md).
- For DICOM/NIfTI conversion and `crop_to_body`, route to [`../dicom-and-formats/SKILL.md`](../dicom-and-formats/SKILL.md).
- For phase/modality/body-stat/Evans-index helper CLIs, route to [`../auxiliary-analysis/SKILL.md`](../auxiliary-analysis/SKILL.md).

## Safe Discovery Rules

- Prefer registry-based discovery over hard-coded task or class names; the registry is the same source used by CLI validation.
- Treat ROI subset names as exact registry class names for the selected task, not labels from another task and not numeric label ids.
- Check `license_required` before selecting a task; this sub-skill can filter licensed tasks, but license acquisition/setup is owned elsewhere.
- Discovery commands here do not run segmentation, download weights, require a GPU, or load model weights.
