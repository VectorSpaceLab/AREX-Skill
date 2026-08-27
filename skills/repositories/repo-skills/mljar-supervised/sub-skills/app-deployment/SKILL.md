---
name: app-deployment
description: "Generate, inspect, serve locally, and publish Mercury prediction
  apps from trained MLJAR AutoML models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# App Deployment

Use this sub-skill when a task involves turning an already fitted `supervised.AutoML` model into a Mercury prediction app, inspecting the generated app workspace, previewing it locally, or preparing a guarded publish flow.

## Route here for

- Generating app files with `automl.app(path=..., overwrite=..., title=...)`.
- Inspecting generated files such as `mljar_app.json`, notebooks, `automl.zip`, `config.toml`, `requirements.txt`, and `runtime.txt`.
- Starting a local Mercury preview with `automl.local_app()` when Mercury is installed and the user accepts a foreground server process.
- Publishing with `automl.publish_app(...)` only after the user explicitly authorizes browser, network, and platform-auth actions.
- Diagnosing app workspace, Mercury startup, and publish failures.

## Route elsewhere

- To `../training-core/` when the user still needs to train, configure, evaluate, or retrain an `AutoML` model.
- To `../artifacts-reports/` for interpreting saved model folders, leaderboards, structured reports, explainability outputs, or `results_path` artifacts outside the generated app workspace.
- To `../fairness-workflows/` for fairness metrics, sensitive features, and fairness dashboard/report interpretation.
- Exclude maintainer-only CI docs deployment, package release, and platform credential administration tasks.

## Operating checklist

1. Confirm `supervised` imports and the model was fitted. App generation needs a valid `results_path` containing fitted AutoML artifacts.
2. Choose the deployment action:
   - `app()` for file generation only.
   - `local_app()` for a local Mercury server and browser preview.
   - `publish_app()` for the hosted platform workflow; require explicit authorization.
3. Decide output location and overwrite policy before writing app files. `overwrite=True` deletes an existing app workspace.
4. Inspect the generated `mljar_app.json` manifest before serving or publishing, especially `supports.single_sample`, feature count, and selected notebooks.
5. For local serving, install the generated app dependencies in a Python 3.10+ environment and ensure the `mercury` executable is on `PATH`.
6. For publishing, avoid embedding credentials in code. Use `open_browser=False` in non-interactive sessions and have the user open the printed login URL manually.

## Read next

- [App workflows](references/app-workflows.md) for generation, local preview, manual hosting, and publish recipes.
- [API reference](references/api-reference.md) for method signatures, return values, generated files, and state behavior.
- [Troubleshooting](references/troubleshooting.md) for overwrite, unfitted model, Mercury, server logs, publish/auth/network, URL reuse, and wide dataset issues.
- `scripts/generate_app_workspace_smoke.py` for a safe synthetic helper that trains a tiny model and generates app files without starting Mercury or publishing.
- Root package assumptions: `../../references/package-overview.md`; cross-cutting install/import issues: `../../references/troubleshooting.md`.
