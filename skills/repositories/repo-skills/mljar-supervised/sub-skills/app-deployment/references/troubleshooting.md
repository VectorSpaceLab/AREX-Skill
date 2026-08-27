# App deployment troubleshooting

Use this guide for failures around `automl.app()`, `automl.local_app()`, and `automl.publish_app()`. For import/install issues that occur before `supervised` imports, use root `../../../references/troubleshooting.md`. For model training choices, use `../../training-core/`.

## `app()` says the output directory already exists

Typical message:

```text
Cannot generate app. Directory '...' already exists.
```

Cause: `app(path=..., overwrite=False)` never merges into an existing workspace.

Fix:

1. Inspect the target path and confirm it is only an old generated app workspace.
2. Choose one:
   - use a new `path`, or
   - set `overwrite=True` to delete and recreate the app workspace.
3. Do not set `overwrite=True` on a directory that contains hand-edited notebooks or unrelated files unless the user explicitly wants them removed.

`publish_app(path=None)` overwrites the default `results_path/app` workspace by design. With a custom `path`, pass `overwrite=True` if replacement is intended.

## Model is not fitted or `results_path` is missing fitted artifacts

Typical message:

```text
This model has not been fitted yet. Please call `fit()` first.
```

Cause: app generation looks for fitted AutoML artifacts, including `params.json`, under the model's `results_path`.

Fix:

- Train first with `automl.fit(X, y)`; route to `../../training-core/` for bounded training setup.
- Reuse the same `AutoML(results_path=...)` that was fitted, or load/restore a saved AutoML run before generating the app.
- Do not point `results_path` at the generated app directory. The app directory is output; the AutoML `results_path` is the trained model artifact directory.

## `app()` generated files but says Mercury is unavailable

Typical verbose output:

```text
Mercury is not available in the current Python environment. Install it with: pip install -r requirements.txt
```

Cause: `app()` checks whether the `mercury` Python package is importable only to print a helpful run hint. Missing Mercury does not prevent file generation.

Fix:

```bash
cd <generated-app-directory>
python -m pip install -r requirements.txt
mercury --working-dir=.
```

Use Python 3.10+ for the app-serving environment because the generated app dependencies expect it.

## `local_app()` fails because Mercury is missing

Typical message:

```text
Mercury is not installed or not available in PATH. Install it with: pip install -r requirements.txt
```

Cause: `local_app()` starts the `mercury` executable, not just the Python package import.

Fix:

1. Generate the workspace with `automl.app()` if it does not already exist.
2. Install generated dependencies in the serving environment:

   ```bash
   cd <generated-app-directory>
   python -m pip install -r requirements.txt
   ```

3. Confirm the executable is available:

   ```bash
   mercury --help
   ```

4. Retry `automl.local_app()` or start manually with `mercury --working-dir=.`.

## Mercury starts then exits or never becomes ready

Possible messages:

```text
Mercury server exited with code N. Last log output:
...
```

or

```text
Mercury server did not start in time. Tried URL http://127.0.0.1:PORT. Last error: ...
```

Fix checklist:

- Inspect `.local_app.log` inside the generated app workspace.
- Confirm the app-serving environment can import `supervised`, `pandas`, `numpy`, `matplotlib`, and `mercury`.
- Use Python 3.10+ for Mercury.
- Start manually from the app directory to see full logs:

  ```bash
  cd <generated-app-directory>
  mercury --working-dir=.
  ```

- Check whether local security software blocks `127.0.0.1` ports.
- If the process exits with syntax errors from Mercury, recreate the serving environment with Python 3.10+.
- If imports from `app_support.py` fail, regenerate the app workspace from a fitted model and avoid hand-editing the generated files.

## `publish_app()` returns `None`

`publish_app()` prints handled failures and returns `None`. Always check the return value:

```python
url = automl.publish_app(open_browser=False, verbose=True)
if url is None:
    raise RuntimeError("Publish failed; inspect the printed message.")
```

Common causes:

- model was not fitted,
- app workspace generation failed,
- browser-token authentication timed out or expired,
- account permissions or platform limits prevented app creation,
- an explicitly supplied URL was not found,
- required publish files were missing,
- upload or storage signing failed,
- network access to the platform or storage endpoint failed.

Do not retry publish loops blindly. Confirm user authorization and inspect the printed message first.

## Browser/auth problems during publish

Symptoms:

- Browser does not open.
- A login URL is printed.
- Login session expires or times out.
- The environment is headless.

Fix:

- In headless sessions, call `publish_app(open_browser=False, timeout=300)` and ask the user to open the printed URL.
- Increase `timeout` if the user needs more time to sign in.
- If the session expired, rerun `publish_app()` after the user is ready.
- Never store or paste platform tokens in scripts. The helper uses browser-token authentication.

## Platform API, network, and upload errors

Examples of handled context:

- `Could not connect to MLJAR platform: ...`
- `Failed to create Mercury app at 'https://...' with title '...': ...`
- `The platform rejected the app creation request. This can happen because of account limits, permissions, or invalid app settings.`
- `Failed to upload 'predict_single.ipynb' for site '...': SignatureDoesNotMatch`

Fix:

1. Confirm network access and any proxy settings outside the generated app files.
2. Confirm the authenticated account can create or update the target app.
3. If the failure names a file, verify it exists in the generated workspace and was not edited or deleted.
4. If an upload error contains a non-JSON body such as XML, preserve it in the support/debug note; the lower-level client keeps non-JSON bodies as raw text for diagnosis.
5. Retry only after the user confirms network/auth state is ready.

## URL reuse and `publish_app_state.json`

Behavior:

- After a successful publish, the helper stores `last_published_url` in `publish_app_state.json` under the AutoML `results_path`.
- A later `publish_app()` without `url` tries to reuse that URL.
- If the remembered URL is missing on the platform, the helper creates a new app URL and updates the state file.
- If the user passes `url=...` and that URL is not found, publishing fails and returns `None`.

Fix:

- To intentionally continue updating the same app, keep the state file and publish with the same account.
- To start a fresh app, remove or archive `publish_app_state.json` before publishing, or train into a new `results_path`.
- To update a specific existing app, pass its full URL and verify the authenticated user can see it.

## Missing required publish files

The publisher uploads a fixed set of workspace files. If it reports a missing file:

1. Regenerate the workspace from the fitted model.
2. Avoid manually deleting or renaming generated files.
3. Inspect `mljar_app.json` and the file list.
4. If the model has more than 15 features, see the batch-only note below because `predict_single.ipynb` may be intentionally absent.

## Wide datasets generate batch-only apps

Documented/test-backed behavior: if the model has more than 15 input features, the generated app skips the single prediction UI.

Signals:

- Verbose generation prints `Single prediction UI was skipped...`.
- `predict_single.ipynb` is absent.
- `predict_batch.ipynb` is present.
- `mljar_app.json` has `default_notebook: "predict_batch.ipynb"` and `supports.single_sample: false`.

Fix:

- Use the batch CSV workflow when many features are required.
- If a single-row form is required, train an app-specific model with at most 15 input features.
- Before publishing a batch-only app, verify the installed package's publisher accepts the generated file set. If it fails because `predict_single.ipynb` is missing, use manual hosting or a compact model until the publisher behavior supports batch-only uploads.

## Generated app predictions look wrong

This sub-skill only covers deployment. For prediction-quality issues:

- Check the original training data, target, metrics, and validation design in `../../training-core/`.
- Check preprocessing and feature names in `../../data-preprocessing/`.
- Check saved model/report details in `../../artifacts-reports/`.
- Regenerate the app after retraining; stale app workspaces do not automatically update when the model changes.
