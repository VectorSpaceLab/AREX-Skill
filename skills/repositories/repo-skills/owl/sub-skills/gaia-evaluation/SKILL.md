---
name: gaia-evaluation
description: "Guides OWL's GAIA benchmark data preparation, level and split
  selection, result persistence, final-answer extraction, and answer scoring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OWL GAIA Evaluation

Use this route for `GAIABenchmark`, GAIA validation/test runs, task-level
selection, attached files, result JSON, answer normalization, or accuracy
summaries. A meaningful benchmark run requires GAIA data, model-provider
credentials, network access, and potentially long execution; package import
alone is not benchmark reproduction.

## Before running

- Prepare a private data directory and result path. The loader expects
  `2023/validation` and `2023/test` directories containing `metadata.jsonl` or
  `metadata.parquet` plus referenced task files.
- Read [evaluation-workflow.md](references/evaluation-workflow.md) for the
  exact constructor and `run` arguments, and
  [answer-normalization.md](references/answer-normalization.md) for focused
  scoring fixtures. The accepted split values are
  `valid` and `test`; `train` is intentionally rejected because GAIA has no
  training set in this implementation.
- Configure the model backends through
  [workforce-workflows](../workforce-workflows/SKILL.md), and route attached
  document/image/table behavior to
  [document-processing](../document-processing/SKILL.md).
- Start with a small `subset` or explicit `idx`; use `save_result=True` only
  with a result file you can safely resume and inspect.

## Evaluation contract

`GAIABenchmark.run` prepares each task, creates `OwlGAIARolePlaying`, runs the
society loop, extracts `final_answer` tags, scores against the ground truth,
and returns a summary containing `total`, `correct`, `results`, and `accuracy`.
The scorer has separate numeric, comma/semicolon-list, and normalized-string
paths. Preserve the requested answer format exactly; do not add prose, units,
or markdown when the task expects a scalar or list.

Missing attachments are skipped with a zero-result record by the source
implementation. Treat that as a data-preparation signal and fix the data path;
do not interpret it as evidence that a model answered correctly. Read
[troubleshooting.md](references/troubleshooting.md) for download, resume,
normalization, and cost failures. The reported OWL/GAIA scores in project
materials are historical claims, not a result verified by this skill run.
