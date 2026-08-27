# Troubleshooting RD-Agent

## Triage order

1. Capture `python --version`, `python -m pip show rdagent`, `rdagent --help`, and the exact command.
2. Run an import check and the relevant `--help` command before changing configuration.
3. Classify the first meaningful failure as environment, provider/credential, data, generated-code, evaluator, or orchestration.
4. Reproduce with the smallest available fixture and a fresh output directory.
5. Only then retry with a larger dataset, more iterations, or a different backend.

## Common symptoms

### `rdagent` is missing or imports resolve to the wrong checkout

Use `python -m pip show rdagent` and `python -c "import rdagent; print(rdagent.__file__)"` in the same shell that launches the command. Repair the active environment with an editable install from the intended checkout or install the matching published package. Do not fix this by modifying `PYTHONPATH` in a reusable report.

### Help works but a workflow fails immediately

Help only proves CLI registration. Check required provider variables, model names, data roots, Docker/Java/system tools, and scenario-specific config. Preserve the resolved config and the first traceback. If the workflow uses a generated program, run its syntax/import check separately from the evaluator.

### Provider or quota errors

Treat authentication, rate limits, unavailable deployments, and context-window errors as provider failures. Do not change the benchmark metric or claim a model result. Retry only after confirming the provider, endpoint, model, and budget; redact secrets from logs.

### Generated code fails

Keep the generated source and traceback together. First check missing imports, incorrect data columns, shape/dtype mismatches, and writes outside the run directory. Fix the smallest failure and rerun the same fixture; do not silently rewrite the evaluation protocol.

### Evaluation is empty, unstable, or unexpectedly strong

Check the data split, target leakage, metric direction, missing-value handling, random seeds, and whether the evaluator consumed the generated artifact you think it did. For finance, inspect time ordering and transaction-cost assumptions. For competitions, verify that local validation mirrors the submission target.

### `fitz` deprecation warning

The inspected revision can emit a warning that the `fitz` API is deprecated and `pymupdf` should be used. Record it as a warning unless import or execution actually fails. Do not hide unrelated exceptions beneath warning suppression.

### AutoRL-Bench reports an empty Smith registry

The benchmark runner can warn when `SMITH_BENCH_DIR` points to a missing directory. Confirm the benchmark checkout and registry path before treating the empty registry as a benchmark result. If the required benchmark is unavailable, report `BLOCKED_REQUIRED_BACKEND`/dataset evidence rather than passing a CPU import check off as a run.

### UI or server appears hung

Use `--help` first, then bind explicitly to a local interface and disposable port. Check whether the process is waiting for a browser, model service, Docker daemon, or provider. Record the port and stop the process after the smoke test. Do not launch a persistent public listener as part of verification.

## Recovery report template

```text
Command:
Revision/package:
Environment/backend:
First failing stage:
Observed error:
Minimal reproduction:
Evidence saved:
Next action:
Unverified assumptions:
```
