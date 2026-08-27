---
name: contributing-to-mteb
description: "Add or review MTEB task, benchmark, model metadata,
  result-submission, and contribution validation changes safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Contributing to MTEB

Use this sub-skill when the user is implementing or reviewing changes intended for MTEB itself: new datasets/tasks, task metadata, descriptive statistics, benchmarks, model implementations, model metadata, citations, result submissions, and pre-PR validation.

## Route First

- For selecting existing tasks, reading metadata semantics, or understanding beta/private/superseded task filtering, use `../tasks-and-benchmarks/SKILL.md`.
- For implementing or validating encoder/search/reranker protocols and `ModelMeta` loader behavior, use `../models-and-encoders/SKILL.md`.
- For smoke-running a new task or benchmark after implementation, use `../evaluation-workflows/SKILL.md`.
- For shell automation around `mteb run`, `available-tasks`, `available-benchmarks`, `create-model-results`, or `leaderboard`, use `../cli-and-automation/SKILL.md` when available.

## Contribution Routes

- **Add a task or dataset:** subclass the correct `AbsTask*`, fill `TaskMetadata`, pin `metadata.dataset["revision"]`, keep `trust_remote_code=False`, calculate descriptive statistics, and smoke-evaluate with a small model.
- **Add a benchmark:** create a `Benchmark` from existing task selections with `mteb.get_tasks(...)`, document its measurement goal, decide whether it belongs on the leaderboard, and validate task quality from metadata and descriptive stats.
- **Add a model:** create a `ModelMeta`, prefer built-in wrappers where possible, keep optional provider imports inside loader scope, set `extra_requirements_groups`, and verify `mteb.get_model(...)` plus `mteb.get_model_meta(...)`.
- **Submit results:** use `mteb.ResultCache` and `cache.submit_results(..., create_pr=False)` for manual review; only use automated PR creation when GitHub tooling and `mteb[github]` are installed.
- **Preflight metadata:** run `scripts/check_task_metadata.py` against a JSON fixture or importable task class before any dataset download or full evaluation.

## References

- `references/contribution-workflows.md` - end-to-end task, benchmark, model, and result-submission workflows with commands and expected signals.
- `references/task-implementation-guide.md` - task class patterns, `TaskMetadata` fields, descriptive statistics, citations, and validation checks.
- `references/troubleshooting.md` - fixes for import/install problems, optional extras, dataset access, CLI/API misuse, cache paths, and filtering surprises.
- `scripts/check_task_metadata.py` - safe local checker for task metadata objects and JSON-like metadata fixtures.

## Quick Validation

- Check import: `python -c "import mteb; print(mteb.__version__)"`.
- Validate metadata fixture: `python scripts/check_task_metadata.py --metadata-json task_metadata.json --require-filled --require-descriptive-stats`.
- Validate an importable task class without loading data: `python scripts/check_task_metadata.py --task-class package.module:TaskClass --require-filled`.
- Smoke-run after implementation with a tiny model and explicit cache: use `mteb.get_model("mteb/baseline-random-encoder")`, `mteb.evaluate(..., cache=mteb.ResultCache(cache_path="mteb-results-cache"), co2_tracker=False)`.
