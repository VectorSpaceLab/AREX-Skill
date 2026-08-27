---
name: validation
description: "Evaluates exported MMDeploy models, profiles latency, runs
  regression matrices, and generates backend coverage tables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Validation

Use this sub-skill when a task asks to evaluate an exported MMDeploy backend model, measure inference speed, run a regression matrix, build a supported-backend table, or interpret validation/profiling reports.

## Route by task

- **Metric-aware backend evaluation:** read [evaluation](references/evaluation.md), then use [scripts/test.py](scripts/test.py) when the user needs dataset metrics, visualized outputs, speed-test logging during evaluation, backend model-file selection, or `--cfg-options` overrides.
- **Latency-only profiling:** read [profiling](references/profiling.md), then use [scripts/profiler.py](scripts/profiler.py) when the user asks for warmup/iteration-controlled latency or custom batch-size/shape timing without evaluator metrics.
- **Maintainer regression matrix:** read [regression](references/regression.md), then use [scripts/regression_test.py](scripts/regression_test.py) for codebase/backend/model filters, conversion-only versus precision modes, checkpoint caching, and merged report workbooks.
- **Supported model/backend table:** read [supported model tables](references/supported-model-tables.md), then use [scripts/generate_md_table.py](scripts/generate_md_table.py) to turn regression matrix YAML into Markdown support tables.
- **Unexpected failure, skip, or slow run:** read [troubleshooting](references/troubleshooting.md) before classifying a problem as a model defect.

## Guardrails

- Use `test.py` for validation/evaluation and optional speed logs; use `profiler.py` for latency-only measurements. Do not treat profiler output as metric evidence.
- Regression runs can download checkpoints, call conversion workflows, and exercise heavyweight backends. Always narrow `--codebase`, `--backends`, and `--models` unless the user explicitly requests a full matrix.
- Backend installation/build problems belong to the backend workflow. In this validation sub-skill, record whether a backend is unavailable, skipped, failed, or blocked, and route installation remediation elsewhere.
- Graph rewrite or optimizer implementation changes belong to the extensibility workflow. Use validation here only to observe downstream metric/latency/report impact.
