# Sacred Cross-Cutting Troubleshooting

## When to read

Read this before drilling into a sub-skill-specific troubleshooting file when Sacred fails at install/import time, an optional observer/backend is missing, or a workflow is blocked before the experiment-specific code runs.

## Install and import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'sacred'` | Sacred is not installed in the active Python. | Run `python -m pip install sacred`, then run `python -c "import sacred; print(sacred.__version__)"`. |
| `ModuleNotFoundError: No module named 'pkg_resources'` while importing Sacred | Modern setuptools releases may omit the `pkg_resources` module that Sacred 0.8.x imports. | Install `setuptools<81` in the same environment, then rerun the import check. |
| `pip check` reports conflicts after adding optional observer packages | Optional observer dependencies may pull incompatible versions. | Start from the base Sacred install, add only the optional package needed for the selected observer, and rerun the relevant probe. |
| Import succeeds from a repository checkout but fails elsewhere | The current directory or `PYTHONPATH` is masking a missing install. | Run checks from a neutral directory with the same Python that will execute the experiment. |

## Choosing what to verify

Use base Sacred verification for experiment/config/CLI/local file observer workflows. Do not install broad development or documentation requirements just to use Sacred as a library.

Use optional verification only when the workflow needs it:

- MongoDB: verify `pymongo`, connection URL, authentication, and database reachability.
- SQL: verify `sqlalchemy`, database URL parsing, and driver/service availability.
- TinyDB: verify `tinydb`, `tinydb-serialization`, and `hashfs`.
- S3/GCS: verify cloud SDK packages, bucket existence, permissions, and credentials.
- Slack/Telegram/Neptune: verify secret handling and service access without printing tokens.
- TensorFlow `stflow`: verify a compatible TensorFlow import and summary writer API.

## First safe checks

```bash
python -m pip check
python -m pip show sacred
python - <<'PY'
import sacred
from sacred import Experiment, Ingredient
from sacred.observers import FileStorageObserver
print(sacred.__version__, Experiment.__name__, Ingredient.__name__, FileStorageObserver.__name__)
PY
```

Then run the bundled helper that matches the failing surface:

- Root import/API smoke: `scripts/sacred_env_check.py`
- Experiment and captured functions: `sub-skills/experiment-core/scripts/sacred_experiment_smoke.py`
- Config and CLI routing: `sub-skills/configuration-and-cli/scripts/sacred_config_cli_probe.py`
- Local file observer and metrics: `sub-skills/observers-and-logging/scripts/sacred_file_observer_probe.py`
- Seeds and capture behavior: `sub-skills/reproducibility-and-capture/scripts/sacred_reproducibility_probe.py`

## Stop conditions

Stop and ask for environment details instead of guessing when:

- an optional observer needs credentials or a live service;
- the user requires TensorFlow capture and the installed TensorFlow version is unknown;
- a run must be reproduced from a particular commit but the current working tree is dirty;
- a production experiment would write to external storage, send notifications, or queue work for workers;
- a traceback points into user training/data code rather than Sacred's experiment wrapper.
