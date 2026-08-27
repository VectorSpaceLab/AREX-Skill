---
name: decontamination-maintenance
description: "Maintain decontamination hygiene, clean-training-data safety,
  request caches, and focused maintainer regression workflows for LM Evaluation
  Harness."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Decontamination Maintenance

Use this sub-skill when an agent needs to inspect or maintain contamination controls, request-cache behavior, or contributor workflows that affect advanced evaluation hygiene.

## Route here for

- Reviewing `should_decontaminate` and `doc_to_decontamination_query` fields in task YAMLs.
- Explaining why Pile clean-training-data generation is not a safe default action and what can be checked statically instead.
- Advising request-cache path selection, stale cache cleanup, and focused tests after cache/decontamination edits.
- Planning maintainer regressions with `scripts/regression.py`, benchmark generation scripts, or GPT-2 test-case regeneration as reference-only workflows.
- Troubleshooting missing ngram artifacts, reproducible ngram bucket generation, unsafe-code task risks, or optional-backend test requirements.

## Route elsewhere

- Normal model/task evaluation commands: use `../evaluation-runs/`.
- Authoring ordinary task YAML fields or prompt templates: use `../task-authoring/`.
- Saving, aggregating, or interpreting result logs: use `../result-logging/`.

## Safe operating rules

- Treat decontamination as a hygiene review unless the user explicitly provides a prepared ngram artifact directory containing `info.json` plus sorted ngram buckets.
- Do not run Pile ngram generation or clean-training-data jobs by default; the upstream workflow depends on huge data downloads, large disk/network use, and multi-day processing.
- Prefer static validation of task YAMLs and focused maintainer tests before any long-running run.
- Keep request-cache operations explicit: `true` reuses/writes, `refresh` rewrites, and `delete` removes matching request caches.
- Pin `PYTHONHASHSEED=0` when generating ngram buckets for reproducibility.

## Bundled helpers

- `scripts/check_decontamination_config.py`: static checker for task YAML decontamination fields; it never imports `lm_eval` or fetches datasets.
- `scripts/cache_path_advisor.py`: explains effective request-cache path and safe cache maintenance choices without deleting files.

## References

- `references/decontamination-workflows.md` covers concepts, config fields, clean-training-data safety, and static review.
- `references/maintenance-workflows.md` covers request caching, focused tests, and maintainer scripts.
- `references/troubleshooting.md` covers reproducibility, missing artifacts, stale caches, unsafe-code tasks, and optional extras.
