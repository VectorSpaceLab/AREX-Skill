---
name: data-and-pipelines
description: "Use DVC for core data tracking and pipeline workflows: dvc
  init/add, .dvc files, dvc.yaml stages, dvc.lock, stage/repro/status/diff/dag,
  cache checkout/commit/remove/move/update/freeze/unfreeze, dvcignore, and safe
  dry-run planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DVC Data and Pipelines

Use this sub-skill when a task is about DVC's core data-tracking or pipeline lifecycle in a repository: initializing DVC, tracking data with `.dvc` files, defining stages in `dvc.yaml`, interpreting `dvc.lock`, checking status/diff/dag output, reproducing stages, and safely planning cache or workspace mutations.

## Start Here

1. Confirm the working directory is inside a DVC project before suggesting mutating commands: `dvc root` should resolve the repo root, and `dvc status` should not report an empty project unless the task is setup.
2. For data files or directories that should be versioned as data sources, use `dvc add` and commit both the generated `.dvc` metadata and relevant Git changes.
3. For reproducible commands, use `dvc stage add -n <stage>` to write `dvc.yaml`; run `dvc repro --dry <target>` or the bundled planner before executing expensive stages.
4. Use `dvc status`, `dvc data status`, `dvc diff`, and `dvc dag` to diagnose changes before using commands that alter cache or workspace files.
5. Read the references in this sub-skill for concrete commands, file formats, target syntax, and troubleshooting.

## Core Commands

- Initialize/inspect: `dvc init`, `dvc root`, `dvc version`, `dvc check-ignore --details <paths>`.
- Track data: `dvc add <path>`, `dvc add --glob 'data/*.csv'`, `dvc add --no-commit <path>`, `dvc add --out <dst> <src>`, `dvc add --force <path>`, `dvc add --no-relink <path>`.
- Define stages: `dvc stage add -n <name> -d <dep> -o <out> [-p params.yaml:key] [-M metrics.json] [--plots plots.json] <command...>`.
- List/graph stages: `dvc stage list`, `dvc stage list --all`, `dvc dag`, `dvc dag --outs`, `dvc dag --mermaid`, `dvc dag <target>`.
- Reproduce safely: `dvc repro --dry <target>`, then `dvc repro <target>` when the plan is acceptable; use `--pipeline`, `--downstream`, `--single-item`, or `--all-pipelines` to change scope.
- Inspect data state: `dvc status [targets...]`, `dvc status --json`, `dvc data status --json`, `dvc diff [a_rev] [b_rev] --targets <paths...>`.
- Cache/workspace maintenance: `dvc checkout`, `dvc commit`, `dvc remove`, `dvc move`, `dvc update`, `dvc freeze`, and `dvc unfreeze` after checking the plan and target scope.

## When To Route Elsewhere

- Experiment queueing, `dvc exp run`, experiment comparisons, and experiment result management belong in `../experiments/SKILL.md`.
- Remote setup, `dvc push`, `dvc pull`, `dvc fetch`, garbage collection, remote credentials, and optional storage extras belong in `../remotes-and-cache/SKILL.md`.
- Metrics, params, and plots reporting beyond declaring them as pipeline outputs belongs in `../metrics-params-plots/SKILL.md`.
- Python API streaming, `dvc.api` data access, and filesystem-style reads belong in `../python-api/SKILL.md`.

## Bundled References

- `references/workflows.md` provides command recipes, Repo API equivalents, target syntax, and dry-run planning patterns.
- `references/file-formats.md` explains `.dvc`, `dvc.yaml`, `dvc.lock`, and `.dvcignore` essentials for editing or debugging generated metadata.
- `references/troubleshooting.md` maps common failure modes to safe checks and fixes.
- `scripts/plan_dvc_pipeline.py` prints a deterministic, non-executing stage-add/repro plan from JSON or YAML-ish input.

## Safe Planning Helper

Use the helper when you need a reproducible command plan without touching the repo, importing DVC, or running stage commands:

```bash
python sub-skills/data-and-pipelines/scripts/plan_dvc_pipeline.py --spec pipeline-plan.json --dry-repro train --include-dag
```

The helper prints planned `dvc stage add` commands, suggested metadata files to inspect/commit, validation checks, and `dvc repro --dry` commands. It does not execute DVC and is safe for untrusted repositories.
