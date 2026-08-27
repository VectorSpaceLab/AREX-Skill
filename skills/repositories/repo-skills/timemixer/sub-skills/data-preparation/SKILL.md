---
name: data-preparation
description: "Validate and explain TimeMixer dataset layouts, file names,
  splits, date and frequency features, and benchmark-specific data conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TimeMixer Data Preparation

Use this sub-skill for dataset layout questions, file checks, and small validation tasks.

## Use when
- a custom CSV must be checked for `date`, target, and numeric feature columns
- an ETT, M4, PEMS, Solar, anomaly, or UEA dataset needs layout confirmation
- split sizes, windowability, or time-feature conventions need to be explained
- a future agent needs a safe validator instead of a training or download run

## Do not use when
- the task is about command construction for forecasting experiments
- the task is about model tensor shapes, embeddings, or architecture internals
- the task requires dataset downloads, benchmark training, or native example execution

## What this sub-skill covers
- dataset-key to loader mapping
- required file names and column conventions
- split behavior and window-length implications
- date parsing, `freq` handling, and generated time features
- benchmark-specific quirks for custom CSV, M4, PEMS, Solar, anomaly CSV/NPY, and UEA `.ts` files

## Bundled assets
- `references/data-formats.md`
- `references/troubleshooting.md`
- `scripts/validate_timemixer_data.py`

## Quick workflow
1. Read `references/data-formats.md` for the expected layout.
2. Run `python scripts/validate_timemixer_data.py --help` to inspect supported checks.
3. Validate the candidate dataset tree with the bundled script.
4. If the issue is actually about forecast commands or model internals, hand off to the matching sub-skill.

## Routing
- Forecast command assembly and benchmark recipe questions: `forecasting-experiments`
- Model classes, tensor shapes, and architecture behavior: `model-architecture`
- Imputation, anomaly logic, or classification workflow details: `universal-tasks`
