---
name: segmentation-workflows
description: "Build reproducible TotalSegmentator CLI and Python API
  segmentation workflows for CT and MR inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Segmentation Workflows

Use this sub-skill when an agent needs to run or script `TotalSegmentator` segmentation itself: choosing the task, input/output, device, speed mode, ROI subset, report, and statistics options.

TotalSegmentator is not a medical device and is not intended for clinical usage. Treat outputs as research or workflow artifacts unless the surrounding product has its own approved clinical validation.

## Start Here

1. Select the task and ROI class names before building the command. If the task or class list is unknown, route to `../capability-discovery/SKILL.md` and query `totalseg_info` instead of hard-coding names.
2. Build a reproducible command with `scripts/build_segmentation_command.py` or the flag patterns in `references/workflow-recipes.md`.
3. Prefer `--report <path.json>` for automation so downstream steps can inspect the resolved task, device, classes, and output files without scraping stdout.
4. Add `--quiet` for non-interactive pipelines and `--debug` when diagnosing argument/runtime errors.
5. For CPU-only runs, prefer `--fast` or `--roi_subset` to reduce runtime and memory.

## Local References

- `references/cli-and-api.md` explains the `TotalSegmentator` CLI flags and `python_api.totalsegmentator(...)` call shape.
- `references/workflow-recipes.md` gives ready-to-adapt CLI and Python workflow recipes.
- `references/troubleshooting.md` maps common segmentation failures to fixes or sibling routes.
- `scripts/build_segmentation_command.py` safely prints shell-quoted commands; it never imports TotalSegmentator or runs model inference.

## Route Elsewhere

- Use `../outputs-and-statistics/SKILL.md` for detailed run-report parsing, statistics schemas, multilabel/probability post-processing, and mask combination.
- Use `../runtime-configuration/SKILL.md` for installation, model downloads, offline weights, license setup, usage-stat configuration, and backend/runtime setup.
- Use `../dicom-and-formats/SKILL.md` for DICOM input layout, DICOM SEG/RTSTRUCT dependencies, `crop_to_body`, and format conversion decisions.
- Use `../auxiliary-analysis/SKILL.md` for phase, modality, body-stats, and Evans-index helper CLIs.
- Use `../advanced-training/SKILL.md` for training, evaluation, dataset conversion, or other research workflows beyond ordinary inference.

## Safe Defaults

- Default CT workflow: `TotalSegmentator -i ct.nii.gz -o seg/ -ta total --report seg/run_report.json --quiet`.
- Default MR workflow: `TotalSegmentator -i mr.nii.gz -o seg_mr/ -ta total_mr --report seg_mr/run_report.json --quiet`.
- CPU-constrained workflow: add `--device cpu --fast` and narrow with `--roi_subset <class...>` when clinically/research appropriate.
- Python API workflow: call `totalsegmentator(input, output, task=..., device=..., report=...)`; pass an output path whenever saving masks, reports, statistics, or radiomics is required.
