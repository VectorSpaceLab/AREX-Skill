---
name: optuna
description: "Use this skill for Optuna hyperparameter optimization workflows:
  studies, trials, samplers, pruners, storage, CLI, visualization, artifacts,
  integrations, and advanced APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Optuna Repo Skill

Use this skill when working with Optuna, a Python framework for hyperparameter optimization. It routes tasks across study/trial workflows, search algorithms, pruning, persistent storage, CLI operations, result analysis, visualization, artifacts, integrations, and advanced APIs.

## First Checks

Install or verify Optuna before using workflow-specific guidance:

```bash
python -m pip install optuna
python - <<'PY'
import optuna
print(optuna.__version__)
study = optuna.create_study(direction="minimize")
print(study.study_name)
PY
```

For a source checkout, use an editable install only when repo development or local API inspection is intended:

```bash
python -m pip install -e .
optuna --help
```

Read `references/repo-provenance.md` before deciding whether this generated skill is current for a different Optuna checkout. Use `references/package-overview.md` for package layout, optional extras, and cross-skill routing notes. Use `references/troubleshooting.md` for cross-cutting install/import, optional dependency, CLI, and runtime failures.

## Route by Task

- Use `sub-skills/optimization-workflows/SKILL.md` for objective functions, `create_study`, `Study.optimize`, `Study.ask`, `Study.tell`, callbacks, attributes, fixed/reused parameters, multi-objective basics, and extracting best trials.
- Use `sub-skills/samplers-pruners/SKILL.md` for choosing, configuring, customizing, or debugging samplers and pruners such as TPE, Grid, CMA-ES, NSGA-II, Hyperband, Median, Threshold, Patient, and Wilcoxon.
- Use `sub-skills/cli-and-storage/SKILL.md` for `optuna` CLI commands, `OPTUNA_STORAGE`, SQLite/RDB URLs, `RDBStorage`, `JournalStorage`, `GrpcStorageProxy`, storage upgrades, heartbeat, and stale-trial behavior.
- Use `sub-skills/analysis-visualization/SKILL.md` for `get_param_importances`, trial dataframes, Plotly/Matplotlib visualizations, Pareto fronts, hypervolume history, and optional visualization dependency checks.
- Use `sub-skills/artifacts-integrations/SKILL.md` for `optuna.artifacts`, filesystem/S3/GCS artifact stores, integration callback imports, missing SDKs, credentials, and local artifact roundtrips.
- Use `sub-skills/advanced-apis/SKILL.md` for terminator, search-space helpers, logging, exceptions, experimental warnings, constraints notes, and cautious use of private hypervolume utilities.

## Common Workflow Composition

- Start in `optimization-workflows` to define a correct objective and study lifecycle.
- Add `samplers-pruners` when the task asks for better search behavior, reproducibility, early stopping, constraints, or custom algorithms.
- Add `cli-and-storage` when studies must persist, resume, coordinate workers, or be controlled from shell commands.
- Add `analysis-visualization` after trials exist and the task becomes reporting, ranking, plotting, or export.
- Add `artifacts-integrations` when trials produce files or need framework/cloud integration callbacks.
- Add `advanced-apis` only for specialized Optuna APIs or cross-cutting debugging not owned by the main workflows.

## Safe Bundled Diagnostics

Run these local helpers from an environment where `optuna` is importable:

```bash
python scripts/check_optuna_env.py
python sub-skills/optimization-workflows/scripts/basic_optimization_smoke.py
python sub-skills/cli-and-storage/scripts/storage_smoke.py
python sub-skills/artifacts-integrations/scripts/filesystem_artifact_smoke.py
```

These scripts are self-contained and use temporary files or in-memory studies. They do not require cloud credentials, network access, GPUs, large datasets, or the original repository checkout.

## Optional Dependencies

The base Optuna package supports core studies, trials, in-memory storage, RDB storage dependencies, CLI, and local filesystem artifacts. Some workflows need optional packages:

- `plotly` or `matplotlib` for visualization backends.
- `pandas` for `Study.trials_dataframe`.
- `scikit-learn` for default fANOVA-style importances and `OptunaSearchCV`.
- `cmaes`, `scipy`, or `torch` for selected advanced samplers/pruners.
- `boto3`, `google-cloud-storage`, `redis`, `grpcio`, and framework packages for cloud stores, distributed storage, and integrations.

Treat missing optional packages as routing/troubleshooting signals, not as evidence that base Optuna is broken.
