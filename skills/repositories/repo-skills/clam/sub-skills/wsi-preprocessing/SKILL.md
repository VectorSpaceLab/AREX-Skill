---
name: wsi-preprocessing
description: "Prepare CLAM whole-slide-image masks, coordinate patch bags,
  process lists, segmentation presets, and legacy patching decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# WSI Preprocessing

Use this sub-skill when a user needs CLAM whole-slide-image preprocessing before feature extraction: segment tissue masks, tune a `process_list` CSV, create fast coordinate `.h5` patch files, optionally stitch QC images, or author segmentation preset CSVs.

## Start Here

- Read `references/workflows.md` to choose the one-pass, two-pass mask review, process-list rerun, preset, or legacy workflow and assemble concrete `create_patches_fp.py` commands.
- Read `references/parameters.md` when tuning segmentation, contour filtering, visualization, patching, `process_list`, `--patch_level`, `--preset`, or `--no_auto_skip` behavior.
- Run `scripts/clam_command_builder.py --help` when you want a safe command/output-layout builder that validates preprocessing options without importing CLAM or touching WSI files.
- Run `scripts/build_preset_template.py --help` when you need to print or write a CLAM preset CSV with the expected columns outside the source repository.
- Read `references/troubleshooting.md` when OpenSlide fails, slides are skipped, masks look poor, preset columns are wrong, output files are missing, or legacy patching risks storage blowups.
- Read `references/legacy-pipeline.md` only when the user explicitly needs saved image patches from the old `create_patches.py` pipeline.

## Boundaries

This sub-skill owns WSI segmentation, fast coordinate patch generation, preset authoring, process-list editing, output layout checks, and legacy-pipeline triage. For coordinate `.h5` feature extraction, route to `../feature-extraction/SKILL.md`; for dataset CSVs, splits, training, and evaluation, route to `../training-evaluation/SKILL.md`.
