# App workflows

This reference covers the public app workflow for `supervised.AutoML` models. It assumes an `AutoML` instance has already been trained. If the model is not fitted yet, first use `../../training-core/` to train a bounded model and choose a stable `results_path`.

## Choose the right action

| Goal | Method | Side effects | Use when |
| --- | --- | --- | --- |
| Generate files only | `automl.app(...)` | Writes an app workspace. Does not start Mercury, open a browser, or publish. | You need a reviewable app directory, manual hosting, CI artifact generation, or a dry run. |
| Preview locally | `automl.local_app()` | Regenerates the default app workspace, starts a foreground Mercury process, opens a browser, and blocks until stopped. | Mercury is installed and the user wants an interactive local preview. |
| Publish online | `automl.publish_app(...)` | Generates app files, performs browser/token authentication, creates or reuses an app URL, uploads runtime files, and writes publish state. | The user explicitly authorizes network, browser/auth, and platform upload actions. |
| Host yourself | `automl.app(...)` plus manual Mercury/deployment | Writes files; serving is handled outside `mljar-supervised`. | You need full infrastructure control or cannot use the hosted platform. |

## Generate an app workspace

Minimal pattern after training:

```python
from supervised import AutoML

# Assume X and y were prepared and training choices were selected elsewhere.
automl = AutoML(results_path="AutoML_App_Run", mode="Explain", random_state=1)
automl.fit(X, y)

app_dir = automl.app(
    path="AutoML_App_Run/app",   # optional; defaults to results_path/app
    overwrite=False,             # set True only when replacing an existing app dir is intended
    title="My Prediction App",   # optional; defaults to "MLJAR AutoML"
    verbose=True,
)
print(app_dir)
```

Operational notes:

- `path=None` writes to an `app` subdirectory under the fitted model's `results_path`.
- `app()` returns the absolute app workspace path.
- `overwrite=False` protects existing output. If the target exists, generation fails rather than merging files.
- `overwrite=True` removes the existing app workspace and recreates it. Confirm the path first.
- `verbose=False` suppresses the summary and Mercury install hint; it does not change generated files.
- `title=...` is stored in `mljar_app.json` and `config.toml`.

## Inspect generated files

A generated app workspace is self-contained for Mercury serving and publishing. Common files are:

| File | Purpose |
| --- | --- |
| `mljar_app.json` | App manifest: title, task, feature schema, selected notebooks, selected models, runtime archive name, support flags, and Python requirement. |
| `predict_single.ipynb` | Single-row prediction dashboard. Present only when the trained model has at most 15 features. |
| `predict_batch.ipynb` | Batch CSV scoring dashboard. This is always the safe fallback. |
| `app_support.py` | Runtime helper used by the notebooks to load the bundled AutoML artifacts and score inputs. |
| `automl.zip` | Minimal runtime bundle containing `params.json`, selected model folders, and needed root runtime files. It is intentionally not an expanded model directory. |
| `config.toml` | Mercury app configuration and title. |
| `requirements.txt` | App serving dependencies. Includes Mercury and `mljar-supervised`. |
| `runtime.txt` | Python runtime hint for hosted/server environments. |
| `README.md` | Generated app-local instructions and AI-output disclosure text. |

Before serving or publishing, inspect at least:

```python
import json
from pathlib import Path

manifest = json.loads(Path(app_dir, "mljar_app.json").read_text())
print(manifest["model_task"])
print(manifest["supports"])
print([nb["filename"] for nb in manifest["notebooks"]])
```

If `supports.single_sample` is `False`, the app is batch-only; see the wide dataset notes below.

## Local preview

Use `local_app()` only when starting a foreground server is acceptable:

```python
automl.local_app()
```

Behavior to expect:

- The default app workspace is generated with overwrite enabled.
- A free port on `127.0.0.1` is selected.
- Mercury is started in the app workspace.
- A browser is opened to the local URL when possible.
- The call blocks while the Mercury process runs. Press `Ctrl+C` in the terminal to stop it.

If you need more control, generate files first and start Mercury manually:

```bash
cd AutoML_App_Run/app
python -m pip install -r requirements.txt
mercury --working-dir=.
```

The generated app expects Python 3.10+ because the generated requirements use Mercury v3-era syntax support.

## Publish with explicit authorization

Use `publish_app()` only after the user approves network access, browser/auth flow, platform upload, and URL state changes:

```python
url = automl.publish_app(
    url=None,              # reuse remembered URL if present; otherwise create a new URL
    path=None,             # default app workspace; custom paths are allowed
    overwrite=False,       # with path=None the default workspace is overwritten by design
    title="My Prediction App",
    open_browser=True,     # use False for headless/non-interactive sessions
    timeout=300,
    verbose=True,
)
print(url)
```

Expected publish sequence:

1. Generate the app workspace.
2. Start browser-token authentication with the MLJAR platform.
3. Create a new app URL, reuse the remembered URL, or update an explicitly supplied URL.
4. Upload publishable workspace files.
5. Save the last successful URL in `publish_app_state.json` under the AutoML `results_path`.
6. Return the final app URL on success. Handled app/publish failures are printed and return `None`.

Safer non-interactive pattern:

```python
url = automl.publish_app(open_browser=False, timeout=300, verbose=True)
if url is None:
    raise RuntimeError("Publishing failed; inspect the printed error above.")
```

When `open_browser=False` or the browser cannot open, the login helper prints a URL for the user to open manually. Never paste credentials or tokens into scripts or skill files.

## Updating an existing app URL

- To reuse the last successful URL, call `publish_app()` without `url` and keep `publish_app_state.json` in the model `results_path`.
- To update a specific URL, pass `url="https://..."`. The URL must correspond to an app visible to the authenticated account.
- If the remembered URL no longer exists on the platform, the helper creates a new URL and updates the state file.
- If an explicitly supplied URL cannot be found, the helper reports a publish failure and returns `None`.

## Wide dataset behavior

For more than 15 input features, generated apps are batch-only:

- `predict_batch.ipynb` is generated.
- `predict_single.ipynb` is skipped.
- `mljar_app.json` has `supports.single_sample: false` and `default_notebook: "predict_batch.ipynb"`.
- Verbose generation prints that the single prediction UI was skipped and that the app includes batch CSV prediction only.

If a single-row form is required, train an app-specific model with 15 or fewer input features. For training/feature-selection decisions, route to `../../training-core/` and `../../data-preprocessing/`.

## Safe bundled smoke helper

The bundled helper trains a tiny synthetic classifier and generates app files without starting Mercury or publishing:

```bash
python sub-skills/app-deployment/scripts/generate_app_workspace_smoke.py --help
python sub-skills/app-deployment/scripts/generate_app_workspace_smoke.py --features 6
```

Use `--features 18` to produce a wide synthetic example and confirm batch-only manifest behavior. The helper reports the generated workspace files and manifest support flags.
