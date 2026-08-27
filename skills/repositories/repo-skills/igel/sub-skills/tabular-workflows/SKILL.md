---
name: tabular-workflows
description: "Use Igel's classic tabular CLI and Python workflows for init, fit,
  evaluate, predict, experiment, export, model and metric catalogs,
  preprocessing, cross-validation, hyperparameter search, clustering, and
  multi-output classic ML."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tabular Workflows

Use this sub-skill when the task is about Igel's classic tabular/classic-ML path: creating an `igel.yaml` or JSON config, fitting a model, evaluating a saved model, generating predictions, running the CLI `experiment` shortcut, exporting a fitted sklearn model to ONNX, listing supported models/metrics, or using `Igel(**kwargs)` from Python.

Start here:

- [references/workflows.md](references/workflows.md) for copyable `init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `models`, `metrics`, `version`, `info`, and Python API recipes.
- [references/configuration.md](references/configuration.md) for YAML/JSON config syntax, target-list rules, model arguments, preprocessing, splits, CV, multi-output, clustering, and hyperparameter search.
- [references/data-formats.md](references/data-formats.md) for CSV/TXT/XLSX/JSON/HTML reading behavior, `read_data_options`, feature/target column expectations, and preprocessing data caveats.
- [references/model-catalog.md](references/model-catalog.md) for exact classic model names, model-type routing, CV-estimator notes, and metrics surfaced by `igel metrics`.
- [references/api-reference.md](references/api-reference.md) for the verified `Igel(**cli_args)` call surface, core helper signatures, output artifacts, and programmatic caveats.
- [references/troubleshooting.md](references/troubleshooting.md) for legacy dependency/import failures, malformed configs, missing targets, unsupported algorithms, artifact-path issues, and ONNX export shape limitations.
- [scripts/run_tabular_cycle.py](scripts/run_tabular_cycle.py) for a safe dry-run-first wrapper around fit/evaluate/predict/export payloads and a tiny optional fit/export demo.

Route boundaries:

1. Stay here for classic `igel` CLI commands: `init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `models`, `metrics`, `version`, and `info`.
2. Route FastAPI serving, `/predict` HTTP payloads, Python REST clients, Docker, and GUI questions to [deployment](../deployment/SKILL.md).
3. Route AutoKeras, image/text/structured Auto-ML, `IgelCNN`, and missing `auto-train` questions to [auto-ml](../auto-ml/SKILL.md).
4. Route uncertain repo-wide questions back to the [root router](../../SKILL.md) instead of guessing between classic tabular, deployment, and Auto-ML.
5. Do not tell future agents to open the original examples or docs; the reusable syntax, examples, and caveats needed for this route are distilled into the bundled references above.

Operational defaults:

- Prefer `.yaml` or `.json` config files. Avoid `.yml` with this version unless a newer installed package proves the extension dispatch changed.
- Run fit/evaluate/predict from a stable working directory so the `model_results/` artifacts remain together.
- Treat hyperparameter search, cross-validation, and ONNX export as explicit user-approved steps because they can add runtime cost or dependency/shape constraints.
