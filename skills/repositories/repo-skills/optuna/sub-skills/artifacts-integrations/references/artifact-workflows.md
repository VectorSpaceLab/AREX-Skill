# Artifact Workflows

Optuna artifacts store large files outside study storage while recording artifact metadata on a `Study`, live `Trial`, or `FrozenTrial`. Use artifacts for model checkpoints, generated reports, images, serialized predictions, chemistry structures, or any file that is too large or too binary for `user_attrs`.

## Core API

```python
from optuna.artifacts import FileSystemArtifactStore
from optuna.artifacts import download_artifact
from optuna.artifacts import get_all_artifact_meta
from optuna.artifacts import upload_artifact

artifact_store = FileSystemArtifactStore(base_path="./artifacts")

artifact_id = upload_artifact(
    artifact_store=artifact_store,
    file_path="./trial-report.txt",
    study_or_trial=trial,
    mimetype="text/plain",
)

metas = get_all_artifact_meta(trial)
download_artifact(
    artifact_store=artifact_store,
    artifact_id=artifact_id,
    file_path="./downloaded-trial-report.txt",
)
```

Important signatures:

- `FileSystemArtifactStore(base_path)` stores bytes under a local or network filesystem directory.
- `Boto3ArtifactStore(bucket_name, client=None, *, avoid_buf_copy=False)` stores bytes in S3-compatible object storage and requires `boto3` plus valid credentials/client configuration.
- `GCSArtifactStore(bucket_name, client=None)` stores bytes in Google Cloud Storage and requires `google-cloud-storage` plus valid credentials/client configuration.
- `upload_artifact(*, artifact_store, file_path, study_or_trial, storage=None, mimetype=None, encoding=None) -> str` records metadata and writes file bytes.
- `get_all_artifact_meta(study_or_trial, *, storage=None) -> list[ArtifactMeta]` returns metadata with `artifact_id`, `filename`, `mimetype`, and `encoding`.
- `download_artifact(*, artifact_store, file_path, artifact_id) -> None` writes artifact bytes to a new local path.

## Local Filesystem Roundtrip

Use this pattern for deterministic local tasks and CI checks:

```python
from pathlib import Path
import tempfile

import optuna
from optuna.artifacts import FileSystemArtifactStore, download_artifact, upload_artifact

with tempfile.TemporaryDirectory() as tmpdir:
    root = Path(tmpdir)
    artifact_store = FileSystemArtifactStore(root / "artifacts")
    (root / "artifacts").mkdir()

    def objective(trial: optuna.Trial) -> float:
        value = trial.suggest_float("x", -1.0, 1.0)
        report = root / f"trial-{trial.number}.txt"
        report.write_text(f"x={value}\n", encoding="utf-8")
        artifact_id = upload_artifact(
            artifact_store=artifact_store,
            file_path=str(report),
            study_or_trial=trial,
            mimetype="text/plain",
        )
        trial.set_user_attr("report_artifact_id", artifact_id)
        return value * value

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=1)

    best_id = study.best_trial.user_attrs["report_artifact_id"]
    downloaded = root / "downloaded.txt"
    download_artifact(
        artifact_store=artifact_store,
        artifact_id=best_id,
        file_path=str(downloaded),
    )
```

Rules:

- Create the artifact base directory before using `FileSystemArtifactStore`; the store writes files by artifact ID inside that directory.
- Download to a path that does not already exist; `download_artifact` raises `FileExistsError` if the destination exists.
- The artifact ID is not the original filename. Use metadata or a user attribute when a later workflow needs to find a specific artifact.
- A `FrozenTrial` requires explicit `storage=` for `upload_artifact` and `get_all_artifact_meta` because it does not carry a live storage handle.

## Trial vs Study Artifacts

- Pass a live `Trial` when the artifact belongs to one objective evaluation, such as a checkpoint or per-trial report.
- Pass a `Study` when the artifact describes the whole study, such as an experiment manifest or summary report.
- `get_all_artifact_meta(study)` returns only artifacts uploaded to the study object, not artifacts attached to every trial.
- For a completed trial object from `study.best_trial` or `study.trials[i]`, pass `storage=study._storage` when listing or uploading against that `FrozenTrial`.

## Store Selection

- `FileSystemArtifactStore`: safest default for local development, tests, CI, shared network filesystems, and no-credential environments.
- `Boto3ArtifactStore`: use only when the user has installed `boto3` and configured AWS/S3 credentials, endpoint, bucket policy, and network access.
- `GCSArtifactStore`: use only when the user has installed `google-cloud-storage` and configured Application Default Credentials or an explicit client.
- Do not use artifact stores as a replacement for `RDBStorage` or `JournalStorage`; artifact stores hold file bytes, while Optuna storage holds study/trial state and artifact metadata.

## S3 and GCS Boundaries

Safe construction examples, assuming dependencies and credentials are already available:

```python
from optuna.artifacts import Boto3ArtifactStore

artifact_store = Boto3ArtifactStore(bucket_name="my-bucket")
```

```python
from optuna.artifacts import GCSArtifactStore

artifact_store = GCSArtifactStore(bucket_name="my-bucket")
```

For production S3-compatible endpoints, create and pass an explicitly configured client instead of embedding credentials in code. Keep credentials in environment variables, a cloud identity provider, or the SDK's normal credential chain.

## Metadata and MIME Types

`upload_artifact` guesses MIME type and encoding from the uploaded filename. Override them when the file extension is missing or misleading:

```python
artifact_id = upload_artifact(
    artifact_store=artifact_store,
    file_path="./checkpoint.bin",
    study_or_trial=trial,
    mimetype="application/octet-stream",
    encoding=None,
)
```

Use `get_all_artifact_meta` to reconstruct filenames during bulk download:

```python
for meta in get_all_artifact_meta(study.best_trial, storage=study._storage):
    download_artifact(
        artifact_store=artifact_store,
        artifact_id=meta.artifact_id,
        file_path=f"./downloads/{meta.filename}",
    )
```

## Safe Removal Note

The store classes expose `remove(artifact_id)`, but the public workflow does not provide a high-level artifact deletion API that coordinates metadata cleanup. Avoid deleting artifacts unless the task explicitly owns retention policy and metadata consistency.
