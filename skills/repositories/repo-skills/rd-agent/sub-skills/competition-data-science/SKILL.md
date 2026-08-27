---
name: competition-data-science
description: "Prepare datasets and operate RD-Agent data-science/Kaggle
  workflows with reproducible debug, validation, submission, and grading
  artifacts."
metadata:
  disco-role: operating
  parent-skill: rd-agent
license: MIT
disable-model-invocation: true
---

# RD-Agent competition and data science

Use this sub-skill for `rdagent data_science`, Kaggle-style tasks, custom datasets, data preparation, generated modeling code, local evaluation, and submission artifacts.

## Input contract

A custom task should be organized around a task directory and a `source_data` root. The repository's example documents the following shape:

```text
source_data/<task>/prepare.py
<task>/<task>/description.md
<task>/<task>/sample.py        # optional debug sampler
<task>/eval/grade.py           # optional test grader
<task>/eval/valid.py           # optional submission validator
```

The task description should state the objective, data fields, split/use restrictions, modeling constraints, metric, and submission format. Run [check_dataset_layout.py](scripts/check_dataset_layout.py) before asking an agent to write modeling code.

## Safe workflow

1. Inspect `rdagent data_science --help` and the scenario config.
2. Run `prepare.py` or the dataset preparation step in a disposable output location; verify row counts, columns, labels, and train/test separation.
3. Create a tiny debug sample using the task's `sample.py` when present. The default sampler in `rdagent.scenarios.data_science.debug.data` is a fallback, not a guarantee of semantic correctness.
4. Launch the smallest agent loop that exercises code generation and evaluation.
5. Validate the generated submission with `valid.py` when available, then grade with `grade.py` or the configured evaluator.
6. Preserve the description, resolved paths, generated source, submission, validation output, metric, and seed.

## Competition hygiene

- Do not use test labels, competition metadata, or future information in feature engineering.
- Check that local validation matches the competition's target and that a generated submission has the exact required columns/order.
- Treat external Kaggle credentials and downloads as prerequisites; do not include them in a reusable skill or test fixture.
- A successful code-generation iteration is not a score. Report the evaluator command and the data split that produced the score.
- For time-series or patient data, preserve group/entity boundaries and temporal ordering while sampling.

Read [dataset-contract.md](references/dataset-contract.md) for required files and artifact semantics. For Qlib-backed finance tasks use [quant-finance](../quant-finance/SKILL.md) instead.
