---
name: outputs-and-statistics
description: "Consume TotalSegmentator masks, run reports, statistics,
  radiomics, probabilities, multilabel files, and combined-mask outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TotalSegmentator Outputs and Statistics

Use this sub-skill when a segmentation has already been run and the next task is to validate, summarize, post-process, or combine its outputs. For running a segmentation, route to [segmentation-workflows](../segmentation-workflows/SKILL.md); for task and class discovery, route to [capability-discovery](../capability-discovery/SKILL.md); for DICOM output mechanics, route to [dicom-and-formats](../dicom-and-formats/SKILL.md).

## What This Covers

- Validate `--report` JSON manifests without scraping stdout.
- Read `statistics.json`, `statistics_radiomics.json`, and `--statistics_extra` metrics.
- Understand per-class masks, `--ml` multilabel outputs, label maps, and `--save_probabilities` side outputs.
- Build safe `totalseg_combine_masks` commands for lung, ribs, vertebrae, heart, pelvis, and body masks.
- Diagnose common output/report/statistics failures after a run completes.

## Quick Paths

- Run report schema and validation: [references/reports-and-statistics.md](references/reports-and-statistics.md)
- Output format behavior and post-processing commands: [references/output-formats.md](references/output-formats.md)
- Troubleshooting matrix: [references/troubleshooting.md](references/troubleshooting.md)
- Summarize or enforce a report: `python scripts/inspect_run_report.py --report seg/run_report.json --require-task total --require-class liver`
- Inspect a multilabel label map: `python scripts/inspect_multilabel_header.py seg.nii.gz --require-label spleen`
- Build a combine command: `python scripts/combine_masks_command.py --input seg/ --output lung.nii.gz --mode lung`

## Operating Rules

- Treat `run_report.json` and `statistics.json` as the automation contract; do not parse human progress text.
- Use `report.classes` to interpret class names, especially after `--roi_subset` filters the run.
- Expect `report.output_files` to be populated only when `output` is a directory of NIfTI files; it can be empty for single-file multilabel or DICOM-style outputs.
- Do not rerun segmentation to combine masks; use existing per-class masks or a multilabel NIfTI with `totalseg_combine_masks`.
- If a class or task name is unknown, route to [capability-discovery](../capability-discovery/SKILL.md) and query `totalseg_info` instead of hard-coding names.
