---
name: dataset-pipelines
description: "Route Hierarchical-Localization benchmark and dataset-specific
  pipelines, layouts, prerequisites, and safe dry-run planning without
  accidental downloads or benchmark-scale runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dataset Pipelines

Use this sub-skill when the task is about a dataset-specific hloc workflow, benchmark routing, output-folder planning, or a safe no-run checklist.

## Route here
- Aachen Day-Night v1.0 and v1.1.
- InLoc notebook workflow.
- SfM demo workflow.
- 4Seasons, 7Scenes, CMU, Cambridge, and RobotCar.
- Output-folder conventions, pair-file placement, and dry-run planning.

## Route away
- Low-level feature, retrieval, match-file, or HDF5 details go to `feature-retrieval` or `mapping-localization`.
- Custom extractor or matcher implementation goes to `custom-interop`.
- Full benchmark execution or downloads are never implied by a planning-only request.

## Bundled guidance
- `references/dataset-pipelines.md`
- `references/troubleshooting.md`
- `scripts/list_pipeline_entrypoints.py`

## Safe planning rules
1. Confirm the dataset root, required archives, pair files, and calibration assets before any run.
2. If a required dataset download or benchmark asset is missing, stop at a plan-only response.
3. Use the output roots and per-scene or per-sequence folder conventions from the reference table.
4. Treat 4Seasons as destructive unless you are working on a copy of the dataset.
5. Prefer the bundled entrypoint lister and `--help` command templates when deciding what to run next.
