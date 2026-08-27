---
name: debugging-reporting
description: "Diagnose Snakemake workflows with linting, graph outputs,
  summaries, logs, reports, notebooks, generated unit tests, benchmarks, runtime
  profiles, and CI smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Debugging and Reporting

Use this sub-skill when a user needs Snakemake 9.23.1 diagnostics, quality signals, report generation, generated tests, notebooks, benchmarks, failed logs, runtime profiles, or CI smoke validation.

## Route by task

- For lint failures, DAG topology questions, `--summary`, failed job logs, runtime profiles, or benchmark files, use [references/debugging-reference.md](references/debugging-reference.md).
- For HTML/ZIP reports, report captions/categories/labels/metadata/styles, generated unit tests, notebooks, and CI smoke checks, use [references/reporting-testing-reference.md](references/reporting-testing-reference.md).
- For common failure triage, use [references/troubleshooting.md](references/troubleshooting.md).
- For a safe local diagnostics command plan, run `python scripts/workflow_diagnostics.py --snakefile Snakefile --target all --outdir diagnostics` from the workflow directory.

## Boundaries

- Own linting, graph/summary/report/test/notebook/benchmark/log/profile diagnostics and artifact interpretation.
- Route command scaffolding and executor/run semantics to `../execution-cli/SKILL.md`.
- Route Snakefile syntax and rule design fixes to `../workflow-authoring/SKILL.md`.
- Route storage-backed report dependencies, remote logs, and deployment plugins to `../deployment-storage/SKILL.md`.
- Route embedded Python API/plugin calls to `../python-api-plugins/SKILL.md`.

## Snakemake 9.23.1 facts

- `--reason` is not a valid flag; dry-run output already includes job reasons.
- Safe first-pass diagnostics usually start with `--cores 1 --dry-run --printshellcmds` and add graph/lint/report/test flags as needed.
- Reports read provenance/runtime metadata from `.snakemake`; generate full reports after a successful run when possible.
