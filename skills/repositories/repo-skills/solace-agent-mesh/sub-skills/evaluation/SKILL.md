---
name: evaluation
description: "Draft sam eval suites, test cases, scoring configs, and offline
  preflight checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation

Use this sub-skill to configure and review `sam eval` runs, score test suites, interpret result trees, and validate inputs before live evaluation.

## Covers
- Local and remote evaluation mode selection
- Test suite and test case input shaping
- Scoring and result interpretation
- Offline validation of file references and environment-variable references

## Start here
- [Evaluation workflows](references/evaluation-workflows.md)
- [Data formats](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Offline validator](scripts/validate_eval_inputs.py)

## Excludes
- Runtime task submission or agent execution, which belongs in runtime-operations
- Workflow YAML authoring, which belongs in workflow-authoring
- Project scaffolding or bootstrap flows, which belongs in project-bootstrap

## Notes
- The current live loader expects JSON syntax for `sam eval`; the bundled validator accepts JSON or YAML for preflight only.
- Keep `results_dir_name` explicit so result trees are predictable and easy to compare.
- Use the bundled validator first when a suite looks wrong, missing, or mixed between local and remote modes.
