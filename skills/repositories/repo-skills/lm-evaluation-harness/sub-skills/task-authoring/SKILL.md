---
name: task-authoring
description: "Create, validate, and debug lm-evaluation-harness YAML tasks, task
  groups, filters, metrics, Jinja prompts, includes, and external task
  directories."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Task Authoring

Use this sub-skill when an agent needs to add or repair lm-evaluation-harness task definitions. It covers YAML `TaskConfig` and group config authoring, `!function` helpers, few-shot settings, local/custom datasets, filters, metrics, and static validation. Route full evaluation execution to `../evaluation-runs/`, model/backend setup to `../model-backends/`, and result interpretation to `../result-logging/`.

## Start Here

1. Identify whether the user is creating a leaf task, a Python-backed task, a group, or a tag-based collection.
2. Draft the YAML from `references/task-schema.md` and prefer a small local fixture while iterating.
3. Use `scripts/create_task_skeleton.py` for a self-contained external task directory when starting from scratch.
4. Run `scripts/lint_task_yaml.py` before any command that downloads datasets or imports arbitrary `!function` code.
5. Hand off runtime validation with `lm-eval validate --tasks TASK --include_path DIR`; run only after confirming dataset access and any unsafe/custom code implications.

## Safe Workflow

- Static checks first: parse YAML, resolve `include` structure, inspect keys, metrics, filters, template strings, `!function` references, and common YAML quoting mistakes.
- Runtime validation second: `lm-eval validate` confirms task discovery for the installed package; the command advertises broader validation concerns, but version `0.4.13.dev0` primarily checks that requested tasks/groups/tags resolve through `TaskManager`.
- Full evaluation last: only use evaluation commands after routing to the evaluation-runs sub-skill and confirming model/backend cost, dataset download, and cache behavior.

## References

- `references/task-schema.md` — YAML fields, groups/tags, includes, `!function`, local datasets, few-shot config.
- `references/task-workflows.md` — creation, external task package, validation, debugging, and handoff workflows.
- `references/filters-and-metrics.md` — registered filters, metric/output-type compatibility, and pipeline shape rules.
- `references/troubleshooting.md` — common failures for YAML quoting, includes, splits, filters, metrics, and unsafe code.

## Bundled Scripts

- `scripts/create_task_skeleton.py` creates a minimal external task directory with YAML, `utils.py`, and optional tiny JSON fixture.
- `scripts/lint_task_yaml.py` performs safe static checks without importing task functions or downloading datasets.

## Boundaries

- Do not copy or summarize the full upstream task catalog; use only task names/examples needed for the user's task.
- Do not run full evaluations from this sub-skill; produce the task and validation handoff.
- Do not implement model backends or analyze benchmark scores here.
- Treat Python `!function`, Python task classes, local loading scripts, and `unsafe_code: true` as code execution surfaces that require explicit confirmation before runtime execution.
