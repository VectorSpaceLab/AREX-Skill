# Package Map

## Purpose

Read this when choosing which LabML package to install or which subskill owns a
workflow. The repository ships multiple installable distributions rather than a
single monolithic package.

## Distributions

| Distribution | Import name | Primary purpose | Common install command | Notes |
| --- | --- | --- | --- | --- |
| `labml` | `labml` | Experiment tracking, logging, monitoring, config management, and the client CLI. | `pip install labml` | Core client runtime; its source metadata directly requires `gitpython`, `pyyaml`, and `numpy`. |
| `labml-helpers` | `labml_helpers` | Training-loop helpers, metrics, device/optimizer configs, datasets, and remote dataset helpers. | `pip install labml-helpers` | Base metadata directly requires `labml>=0.4.158` and `torch`; use the focused extras below for modules that import additional packages. |
| `labml-remote` | `labml_remote` | SSH/rsync remote-project orchestration and distributed launch helpers. | `pip install labml-remote` | Metadata directly requires `paramiko`, `pyyaml>=5.3.1`, `scp`, and `click`. |
| `labml-app` | `labml_app` | Monitoring web app backend and analysis endpoints. | `pip install labml-app` | Metadata directly requires `labml`, `gunicorn`, `numpy`, `labml-db`, `fastapi`, `uvicorn`, and `pymongo`; a working app also needs MongoDB, settings, and packaged static assets. |

## Focused helper extras

`labml-helpers` exposes extras for the optional modules whose direct imports are
not part of its base `install_requires`:

- `pip install 'labml-helpers[remote-dataset]'` adds the direct imports used by
  `labml_helpers.datasets.remote`: `matplotlib`, `urllib3`, `fastapi`, and
  `uvicorn`.
- `pip install 'labml-helpers[plotting]'` adds the direct `matplotlib` import
  used by the optimizer plotting/example path.

These extras document direct imports observed in this checkout; they are not a
complete transitive dependency closure or a guarantee that a full training,
remote, or server environment is ready.

## Minimal install sets

- **Tracking only:** `labml`.
- **Training helpers:** `labml` + `labml-helpers` + `torch`.
- **Remote dataset helper:** `pip install 'labml-helpers[remote-dataset]'`.
- **Remote execution:** `labml` + `labml-remote`.
- **App backend:** `labml` + `labml-app` plus MongoDB and the app's settings/static assets.
- **Common stack:** install the four distributions, then add only the helper
  extras and framework packages required by the selected workflows.

## Key public entry points

- `labml`: `labml capture`, `labml launch`, `labml monitor`, `labml service`,
  `labml service-run`, `labml app-server`.
- `labml_remote`: `init`, `setup`, `rsync`, `update-packages`, `prepare`,
  `run`, `job-run`, `job-rsync`, `job-list`, `job-tail`, `job-kill`,
  `helper-torch-launch`.
- `labml_app`: the `labml app-server` launcher starts the FastAPI backend.

## Notes

- `labml` reads `.labml.yaml` from the project tree and uses it for data paths,
  experiment paths, and app URL defaults.
- `labml_remote` reads `.remote/configs.yaml` and `.remote/exclude.txt` in the
  current project.
- `labml_app` needs server settings and built static frontend assets for the
  full server runtime; a plain editable source checkout may not be enough.
