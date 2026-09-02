---
name: response_filtering
description: Use this skill when you need to post-process raw model outputs with regex extraction, take-first, take-k, or majority-vote pipelines.
---

# response_filtering

## When to use
Use this skill for paper-style language model evaluation harness work where reproducibility depends on explicit task contracts, model-request interfaces, response post-processing, metric aggregation, or an end-to-end auditable run. Do not use it to claim real leaderboard performance without a real model and dataset.

## Inputs
- Small JSON-like task, request, response, or metric records depending on the module.
- Optional deterministic fake model/data fixtures for bounded validation.
- A recovery attempt directory when producing experiment evidence.

## Outputs
- Validated Python dictionaries or JSON artifacts with deterministic fields.
- Clear traces that keep raw responses separate from filtered predictions and scores.

## Workflow
1. Read the task/module contract before executing code.
2. Validate required fields and fail loudly on incompatible output types or missing metrics.
3. Preserve raw inputs and produce explicit trace records for downstream modules.
4. Keep this skill self-contained and avoid reading the original lm-evaluation-harness repository during recovery.
5. Run the validation command below after edits.

## Validation
Run `python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests`.

## Limitations
These utilities are compact faithful proxies for the harness mechanisms. They are not a replacement for the full upstream package when full-scale benchmark evaluation is required.
