# Package Overview

Read this for cross-cutting MLJAR Supervised package assumptions before entering a workflow-specific sub-skill.

## Identity and installation

- Public distribution: `mljar-supervised`.
- Python import package: `supervised`.
- Main public entry point: `from supervised import AutoML`.
- Supported Python versions in package metadata: Python 3.9 and newer.
- The package has substantial scientific/ML dependencies, including NumPy, pandas, SciPy, scikit-learn, XGBoost, LightGBM, CatBoost, matplotlib, SHAP, dtreeviz, Optuna integration, and plotting/report packages.

Typical install:

```bash
python -m pip install mljar-supervised
python - <<'PY'
from supervised import AutoML
print(AutoML)
PY
```

For repository-development or local editable work, install from the checkout in a private environment with `python -m pip install -e .`; do not tell ordinary package users to depend on a source checkout.

## Capability summary

MLJAR Supervised automates supervised learning for tabular data. Its core `AutoML` object can:

- infer or accept binary classification, multiclass classification, or regression tasks;
- train multiple model families and select/ensemble candidates;
- perform automatic preprocessing for common missing, categorical, text, datetime, scaling, and target transformations;
- tune with bounded built-in modes or Optuna;
- generate Markdown/HTML reports, structured report payloads, feature importance, learning curves, and explainability artifacts;
- save runs to `results_path` and reload full AutoML runs;
- optimize for fairness with sensitive features and task-specific fairness metrics;
- generate Mercury prediction app workspaces and optionally serve or publish them.

## Main modes

| Mode | Best fit | Caution |
| --- | --- | --- |
| `Explain` | Quick exploration and understanding with simple reports/explanations. | Still can produce plots/SHAP depending on `explain_level`; use `explain_level=0` for smoke checks. |
| `Perform` | Production-style tabular modeling with stronger validation and efficient pipelines. | Needs a realistic time budget. |
| `Compete` | Competition-style maximum performance, broader algorithm search, stacking. | Can be expensive; validate the user's runtime budget first. |
| `Optuna` | Hyperparameter optimization when performance matters and time is available. | `optuna_time_budget` is per algorithm and can multiply by data variants. |

## Optional system/runtime dependencies

| Surface | Optional dependency or condition | How to handle |
| --- | --- | --- |
| Decision-tree visualizations | Graphviz `dot` executable plus Python graphviz/dtreeviz stack | If tree plots fail but training/reporting works, document Graphviz installation rather than treating the model as broken. |
| SHAP outputs | SHAP and compatible compiled dependencies | Use `explain_level=0` or `1` for fast checks; use `2` only when SHAP explanations are required. |
| Local app preview | Mercury package/executable and a foreground server process | Generate files with `app()` first; start `local_app()` only with user approval. |
| Hosted app publish | Browser or printed login URL, network, platform auth, upload permissions | Never publish or authenticate without explicit user authorization. |
| Heavy ML backends | XGBoost, LightGBM, CatBoost wheels compatible with Python/platform | Isolate backend failures by first running a Baseline/Decision Tree smoke. |

## Safe smoke strategy

For a fast check of user environment and package behavior, prefer synthetic in-memory data and a disposable output directory:

```python
from supervised import AutoML
from sklearn.datasets import make_classification

X, y = make_classification(n_samples=80, n_features=6, n_informative=3, random_state=42)
automl = AutoML(
    mode="Explain",
    algorithms=["Baseline", "Decision Tree"],
    explain_level=0,
    train_ensemble=False,
    stack_models=False,
    golden_features=False,
    features_selection=False,
    total_time_limit=30,
    results_path="automl_smoke",
    verbose=0,
)
automl.fit(X, y)
print(automl.predict(X[:5]))
```

Use the bundled scripts for repeatable checks instead of copying long examples into a task response.
