# Troubleshooting Artifacts and Integrations

Use this guide when artifact upload/download or third-party integration imports fail.

## Artifact API Misuse

### `ValueError: storage is required for FrozenTrial.`

Cause: `upload_artifact` or `get_all_artifact_meta` received a `FrozenTrial` without an explicit storage object.

Fix:

```python
frozen = study.best_trial
metas = get_all_artifact_meta(frozen, storage=study._storage)
```

For new uploads, prefer uploading inside the objective with the live `Trial`. Use a `FrozenTrial` only when the workflow really needs to attach or inspect artifacts after the trial has finished.

### `FileExistsError: File already exists: ...`

Cause: `download_artifact` refuses to overwrite an existing destination file.

Fix: choose a fresh output path, remove the old file intentionally, or generate a unique filename from `ArtifactMeta.filename` plus the artifact ID.

### `ArtifactNotFound`

Cause: the artifact ID does not exist in the configured store, the wrong artifact store was reconstructed, or the object was deleted outside Optuna.

Fix:

- Confirm the artifact ID came from `upload_artifact` or `get_all_artifact_meta` for the same study/trial.
- Confirm the same artifact store backend and bucket/base path are being used.
- For filesystem stores, inspect whether files exist under the configured base directory.
- For S3/GCS, confirm object retention, bucket name, credentials, and region/project settings.

### `ValueError: Invalid artifact_id`

Cause: `FileSystemArtifactStore` rejects absolute paths and path traversal such as `../x`.

Fix: pass only the opaque artifact ID returned by `upload_artifact` or listed in `ArtifactMeta.artifact_id`. Do not pass filenames or user-provided paths as artifact IDs.

### MIME Type Is Unexpected

Cause: `upload_artifact` guesses MIME type and encoding from the filename extension.

Fix: pass `mimetype=` and `encoding=` explicitly when downstream consumers require exact headers.

## Store Configuration Problems

### Filesystem Base Directory Missing

Cause: `FileSystemArtifactStore` stores objects under `base_path` but does not create parent directories for the workflow.

Fix:

```python
from pathlib import Path
from optuna.artifacts import FileSystemArtifactStore

base_path = Path("./artifacts")
base_path.mkdir(parents=True, exist_ok=True)
artifact_store = FileSystemArtifactStore(base_path)
```

### Cloud SDK Missing

Symptoms include `ModuleNotFoundError` for `boto3`, `botocore`, or `google.cloud.storage`.

Fix: install the needed SDK only when the workflow actually uses that backend. If the task can run locally, switch to `FileSystemArtifactStore` instead.

### Cloud Credentials Missing or Invalid

Symptoms include SDK credential errors, permission denied responses, or missing bucket/object errors.

Fix:

- Do not hard-code keys in source code.
- Use the SDK's normal credential chain, environment variables, workload identity, or an explicitly configured client supplied by deployment code.
- Verify bucket permissions separately from Optuna.
- Use a local filesystem smoke test to prove Optuna artifact logic before debugging cloud IAM/network issues.

## Integration Import Problems

### `ModuleNotFoundError` from `optuna.integration`

Cause: the target integration is optional and may live in `optuna-integration` plus the third-party framework package.

Fix:

```bash
python -m pip install optuna-integration lightgbm
```

Replace `lightgbm` with the framework actually requested. If the environment should remain minimal, avoid integration callbacks and write a plain Optuna objective.

### Deprecation Warning for `optuna.integration.<module>`

Cause: several integration modules are compatibility shims and warn that direct `optuna_integration.<module>` imports are preferred.

Fix: for new code that depends on integration packages, import from `optuna_integration` after installing the package. For existing code, keep `optuna.integration` only when compatibility with historical imports is required.

### Callback Does Not Prune

Cause: the framework callback may not be connected to the validation metric, the study pruner may need more warmup data, or the objective never reports intermediate values.

Fix:

- Confirm the callback monitors the exact metric name produced by the framework.
- Confirm the study was created with a pruner, such as `MedianPruner` or `HyperbandPruner`.
- In manual loops, call `trial.report(metric, step)` before `trial.should_prune()`.
- Remember that pruning is for single-objective workflows; route multi-objective pruning questions to algorithm/workflow design rather than integration callback setup.

## Local Fallback Decision Tree

When a requested artifact or integration workflow fails because optional dependencies or credentials are absent:

1. Keep the Optuna study logic intact.
2. Replace remote artifact stores with `FileSystemArtifactStore` under a temporary or configured local directory.
3. Replace integration callbacks with manual `trial.report` and `trial.should_prune` if possible.
4. Document the exact packages and credentials needed to re-enable the original backend.
5. Run `scripts/filesystem_artifact_smoke.py` to prove local artifact handling independently of cloud or framework services.
