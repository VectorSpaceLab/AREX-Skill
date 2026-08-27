---
name: dashboard
description: "Route Plexe's dashboard and workdir inspection workflow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# dashboard

Use this sub-skill for Plexe's Streamlit dashboard and saved-run inspection workflow.
It is the right route when the user wants to browse experiment history, checkpoints,
search trees, evaluation reports, or packaged model files.

## Typical triggers

- "Open the Plexe dashboard"
- "What does this workdir contain?"
- "Why isn't my saved run showing up?"
- "Inspect the checkpoints or model package for this experiment"
- "How does Plexe discover experiments in `workdir/`?"

## What belongs here

- `python -m plexe.viz --work-dir ...`
- `plexe.viz.main`
- `plexe.utils.dashboard.app`
- experiment discovery and metadata extraction
- checkpoint and report loading
- dashboard tabs and model package presentation
- workdir structure assumptions for saved runs

## What stays out

- Training, retraining, Spark setup, and packaging decisions belong in
  [model-building](../model-building/SKILL.md).
- Repository maintenance and release automation stay outside this skill.

## Read these references first when needed

- [`references/dashboard-workflow.md`](references/dashboard-workflow.md) for the launch command,
  environment variables, experiment discovery, tabs, and workdir layout.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing workdirs,
  empty dashboards, malformed checkpoints, and dependency problems.
- [`../../scripts/inspect_workdir.py`](../../scripts/inspect_workdir.py) when you need a
  quick read-only summary without opening the Streamlit UI.

## How to work this route

1. Confirm the workdir path and whether the user wants the dashboard or a text summary.
2. Check that the run has checkpoints and a packaged model before blaming the UI.
3. Use the dashboard reference to map a question to the correct tab or file.
4. Use the troubleshooting reference when the workdir is empty, corrupt, or incomplete.

## What the dashboard expects

- Saved experiment directories grouped by dataset name and timestamp.
- `checkpoints/*.json` files for phase progress and search state.
- `.build/reports/*.yaml` files for generated reports.
- `model/` and `model.tar.gz` for packaged model inspection.
- `model/model.yaml` plus `schemas/` and `src/` files for the package tab.

If those files are missing, the dashboard may still open but will show warnings or empty panes.

## Common questions this route answers

- Which phase did the run reach?
- Why is a run marked failed, paused, or running?
- What did the best search node look like?
- Did the package get written and what files does it contain?
- Which saved runs exist for a given dataset?

## Decision points

- If the path exists but no experiments appear, check the depth and naming convention first.
- If the run exists but a tab is empty, inspect whether the corresponding checkpoint or report file was written.
- If the package tab is missing fields, confirm the final packaging phase completed.
- If you only need a text summary, use the bundled workdir inspector instead of opening Streamlit.

## Bundle ownership

This sub-skill owns the dashboard workflow reference and its troubleshooting notes.
The root skill should only route here, not duplicate the tab-by-tab behavior.
