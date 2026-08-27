# App API reference

Import path:

```python
from supervised import AutoML
```

`mljar-supervised` exposes app deployment through Python methods on fitted `AutoML` objects. There are no package console entry points for these helpers; the only CLI used in the app flow is the generated workspace's `mercury --working-dir=.` command.

## `AutoML.app()`

Signature:

```python
AutoML.app(path=None, overwrite=False, title=None, verbose=True)
```

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `path` | Output directory for the generated Mercury workspace. `None` resolves to an `app` subdirectory under `results_path`. | Prefer an explicit path when writing outside the AutoML results directory. |
| `overwrite` | Whether to delete and recreate an existing app output directory. | Keep `False` for first generation; set `True` only after confirming the target is disposable. |
| `title` | Optional app title. | Appears in `mljar_app.json` and `config.toml`; defaults to `MLJAR AutoML`. |
| `verbose` | Whether to print the app directory, `cd` command, Mercury install hint, and start command. | Use `False` in scripts that emit structured output. |

Return value: absolute path to the generated app workspace.

Readiness checks performed by the implementation:

- The fitted AutoML `results_path` must contain `params.json`.
- If the best model is not loaded in memory, the helper loads it from `results_path`.
- If the output directory exists and `overwrite=False`, generation raises an `AutoMLException` instead of merging files.
- If any workspace write fails, the partially created output directory is removed before the exception is re-raised.

## Workspace file inventory

The app generator writes a Mercury workspace around a minimal AutoML runtime bundle.

| File | Generated when | Notes |
| --- | --- | --- |
| `predict_single.ipynb` | Only when feature count is at most 15. | Single-sample form and feature context plots. |
| `predict_batch.ipynb` | Always for normal app generation. | CSV upload/scoring workflow and prediction download. |
| `app_support.py` | Always. | Loads `automl.zip`, validates app inputs, and calls prediction methods. |
| `mljar_app.json` | Always. | Manifest with schema version, task, feature schema, notebook list, class labels, leaderboard summary, selected model, runtime bundle, support flags, and `python_requires`. |
| `config.toml` | Always. | Mercury title, welcome text, and AI-output disclosure footer. |
| `requirements.txt` | Always. | Includes `mercury`, `mljar-supervised`, `matplotlib`, `pandas`, and `numpy`. |
| `runtime.txt` | Always. | Runtime hint for Python 3.10. |
| `README.md` | Always. | App-local run instructions and disclosure text. |
| `automl.zip` | Always. | Minimal model runtime archive, not the full original training report. |

`automl.zip` contains:

- a minimal `params.json` with `results_path` rewritten to `automl`,
- selected model directories needed for prediction,
- required root runtime files such as `data_info.json`,
- `golden_features.json` only when the selected prediction path needs golden features,
- no report HTML/Markdown, images, logs, or other non-runtime visual artifacts.

For saved artifact interpretation beyond this runtime bundle, route to `../../artifacts-reports/`.

## `mljar_app.json` manifest fields

Important manifest fields for future agents:

| Field | Meaning |
| --- | --- |
| `bundle_type` | Expected to be `automl_prediction_bundle`. |
| `title` | Display title used by Mercury. |
| `model_task` | AutoML task: binary classification, multiclass classification, or regression. |
| `default_notebook` | `predict_single.ipynb` for compact feature sets; `predict_batch.ipynb` for wide datasets. |
| `notebooks` | List of generated notebooks. Do not assume `predict_single.ipynb` exists. |
| `feature_schema` | App input schema with widget kind, required flag, defaults, choices, numeric ranges, and transformations. |
| `class_labels` | Classification labels; empty for regression. |
| `global_feature_importance` | Feature-importance summary when available from the structured report. |
| `leaderboard` | Compact leaderboard data from `report_structured(format="dict")`. |
| `selected_model` | Selected model summary from the structured report. |
| `automl_bundle` | Runtime archive metadata and selected model names. |
| `supports.single_sample` | `False` when the model has more than 15 features. |
| `supports.batch_prediction` | Batch mode support flag. |
| `supports.predict_proba` | `False` for regression, `True` for classification tasks. |
| `python_requires` | Runtime Python requirement for the app workspace. |

## `AutoML.local_app()`

Signature:

```python
AutoML.local_app()
```

Behavior:

1. Calls app generation for the default app workspace with `overwrite=True` and `verbose=False`.
2. Looks for a `mercury` executable on `PATH`.
3. Selects a free local port on `127.0.0.1`.
4. Starts Mercury in the generated app directory with browser auto-open disabled at the Mercury process level.
5. Waits until the local URL responds, then opens the browser.
6. Prints the local URL and blocks until the Mercury process exits or the user interrupts with `Ctrl+C`.

Return value: the local app URL after the process is stopped or exits cleanly.

State set on the `AutoML` object while running:

- `_local_app_process`
- `_local_app_url`

Failure behavior:

- If Mercury is missing from `PATH`, raises `AutoMLException` with an install hint.
- If the server exits during startup, the exception includes the process return code and the tail of `.local_app.log`.
- If startup times out, the exception includes the attempted URL and last connection error.

## `AutoML.publish_app()`

Signature:

```python
AutoML.publish_app(
    url=None,
    path=None,
    overwrite=False,
    title=None,
    open_browser=True,
    timeout=300,
    verbose=True,
)
```

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `url` | Existing app URL to update. If omitted, the helper reuses remembered state or creates a new URL. | Pass only URLs the authenticated user controls. |
| `path` | App workspace path to generate before upload. | `None` uses the default app workspace. |
| `overwrite` | Whether a custom `path` may be replaced. | With `path=None`, the default workspace is overwritten by design. For custom paths, set `True` only when safe. |
| `title` | App title for generated workspace and newly created platform app. | Use a descriptive, non-sensitive title. |
| `open_browser` | Whether to open the login URL in the browser. | Use `False` in headless/non-interactive runs; the login URL is printed. |
| `timeout` | Seconds to wait for browser-token authentication. | Default is 300 seconds. Short timeouts are useful for tests. |
| `verbose` | Print progress, URLs, uploaded filenames, and failure messages. | Keep `True` for interactive troubleshooting. |

Publish sequence:

1. Load previous state from `publish_app_state.json` under `results_path`, if present.
2. Generate the app workspace. `path=None` implies overwrite of the default workspace.
3. Start browser-token sign-in against the configured MLJAR platform endpoint.
4. Reuse an explicit `url`, reuse remembered state, or create a new platform app URL.
5. Upload required publish files.
6. Save `{"last_published_url": app_url}` to `publish_app_state.json`.
7. Print the final URL and return it.

Failure behavior:

- Handled `AutoMLException` failures are printed as `Publish app failed: ...` and the method returns `None`.
- Upload/create-site failures include file names or target URL context when available.
- Non-JSON HTTP response bodies are preserved as raw text in lower-level API errors, which helps diagnose opaque storage errors.
- Browser/auth session failures can be interactive and time-bound. Do not run without user authorization.

## Publishable files

The publisher expects the generated workspace to provide these upload files:

- `predict_single.ipynb`
- `predict_batch.ipynb`
- `app_support.py`
- `mljar_app.json`
- `config.toml`
- `requirements.txt`
- `runtime.txt`
- `automl.zip`

Because wide datasets intentionally skip `predict_single.ipynb`, inspect `mljar_app.json` and the workspace files before publishing a batch-only app. If the publisher reports a missing `predict_single.ipynb`, either train a compact app-specific model with 15 or fewer features or manually host the batch-only workspace until publisher behavior is confirmed for the installed package version.

## Platform configuration knobs

The publisher reads two optional environment variables at import time:

- `MLJAR_PLATFORM_BASE_URL` for the platform API base URL.
- `MLJAR_PLATFORM_DEFAULT_DOMAIN` for generated app subdomains.

Use these only when the user intentionally targets a non-default platform setup. Do not put tokens or passwords in environment variables for this flow; browser-token authentication is handled interactively.
