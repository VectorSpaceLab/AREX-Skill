# Cross-Cutting Troubleshooting

Read this for install/import and optional dependency issues that occur before a workflow-specific sub-skill can run. Once `from supervised import AutoML` works, use the nearest sub-skill troubleshooting reference for training, data, reporting, fairness, or app-specific failures.

## `ModuleNotFoundError: No module named 'supervised'`

**Likely cause**: the distribution `mljar-supervised` is not installed in the active Python environment.

**Recovery**

```bash
python -m pip install mljar-supervised
python - <<'PY'
from supervised import AutoML
print(AutoML)
PY
```

If several Python environments exist, use the exact interpreter that will run the user's notebook, script, service, or job.

## Metadata package name differs from import name

**Symptom**: `pip show supervised` fails, but `import supervised` is expected.

**Recovery**: install/query the distribution name `mljar-supervised` and import `supervised` in Python:

```bash
python -m pip show mljar-supervised
python -c "import supervised; print(supervised.__version__)"
```

## Heavy dependency install or import failures

**Common surfaces**: NumPy/pandas/SciPy/scikit-learn ABI mismatches, XGBoost/LightGBM/CatBoost wheel issues, SHAP/numba/llvmlite import errors, matplotlib backend issues.

**Recovery**

1. Use a clean Python 3.9-3.12 environment when possible.
2. Upgrade packaging tools in that environment: `python -m pip install --upgrade pip setuptools wheel`.
3. Reinstall `mljar-supervised` rather than mixing source and wheel installs.
4. Isolate model-backend failures with a minimal Baseline/Decision Tree smoke: `sub-skills/training-core/scripts/mljar_automl_smoke.py --task binary`.
5. If a specific backend fails, temporarily remove it from `algorithms` and report the backend-specific package/platform error to the user.

## Graphviz or tree visualization failures

**Symptoms**

- Errors mention `dot`, Graphviz, dtreeviz, or failure to render decision-tree plots.
- Model training succeeds but tree visualization files are missing.

**Likely cause**: the Python graphviz/dtreeviz packages and the system Graphviz executable are separate dependencies; the executable may be missing from `PATH`.

**Recovery**

- Use `explain_level=0` for training smoke checks.
- Install Graphviz through the operating-system package manager appropriate for the user's environment.
- Re-run the report/explain workflow only after `dot -V` works.
- Route to `sub-skills/artifacts-reports/references/troubleshooting.md` for explainability artifact expectations.

## Mercury app dependency is missing

**Symptoms**

- `automl.app()` can generate files, but `local_app()` fails.
- Errors mention `mercury` missing or a local app process failing to start.

**Recovery**

- Generate app files first with `automl.app(...)` to verify the trained model and workspace.
- Install Mercury only in the environment intended to serve the app.
- Do not start a local server or browser session unless the user explicitly wants it.
- Route to `sub-skills/app-deployment/references/troubleshooting.md`.

## Hosted publishing requires browser, network, and auth

**Symptoms**

- `publish_app()` prints a login URL, waits for browser authentication, times out, or receives platform API/upload errors.

**Recovery**

- Ask before making network/browser/auth actions.
- In non-interactive sessions, use `open_browser=False` and let the user open the printed URL.
- Do not store platform tokens or credentials in generated code.
- Treat non-JSON HTTP responses as platform errors and preserve the status/body excerpt for diagnosis.

## GPU assumptions

MLJAR Supervised's selected skill scope is CPU-compatible. Do not require CUDA/ROCm/MPS merely because a host GPU is visible. If a user asks for GPU acceleration through a backend library, verify that the selected algorithm and dependency stack actually uses and supports that backend; otherwise keep guidance CPU-focused.

## Check script

Run [`../scripts/check_mljar_supervised_install.py`](../scripts/check_mljar_supervised_install.py) to print import, version, signature, optional dependency, and Graphviz/Mercury availability signals without training a model.
