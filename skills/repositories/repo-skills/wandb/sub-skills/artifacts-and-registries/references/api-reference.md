# Artifact and Registry API Reference

## Artifact construction

`wandb.Artifact(name, type, description=None, metadata=None, incremental=False, use_as=None, storage_region=None)` creates a draft artifact. Populate it before logging.

- `name` may contain letters, numbers, underscores, hyphens, and dots; avoid `/` and keep it at or below 128 characters.
- `type` is a user-defined category such as `dataset`, `model`, `checkpoint`, or `eval-results`; it must not contain `/` or `:` and must not be reserved (`job` or `wandb-*`). Include `model` in the type string when a model-registry flow expects model artifacts.
- `description` is rendered as markdown in the W&B UI.
- `metadata` must be JSON-friendly and should stay concise; W&B validates at most 100 metadata keys.
- A newly created artifact is mutable until it is logged/finalized.

```python
import wandb

artifact = wandb.Artifact(
    name="training-data",
    type="dataset",
    description="Curated training split",
    metadata={"format": "parquet", "rows": 12000},
)
```

## Add files, dirs, and references

`Artifact.add_file(local_path, name=None, is_tmp=False, skip_cache=False, policy="mutable", overwrite=False)` adds one local file.

- `local_path` must exist and be a file at add time.
- `name` is the artifact-relative logical path; do not pass absolute or traversal paths.
- `policy="mutable"` protects against source-file changes during upload by staging a copy.
- `policy="immutable"` avoids that copy but requires the caller not to mutate/delete the file during upload.
- `overwrite=True` replaces an already-added logical path in the same draft artifact.

`Artifact.add_dir(local_path, name=None, skip_cache=False, policy="mutable", merge=False)` recursively adds a local directory.

- `local_path` must exist and be a directory.
- `name` places the directory under an artifact-relative prefix.
- `merge=False` raises if a previous `add_dir` added a changed file at the same logical path; `merge=True` overwrites changed files and adds new files.

`Artifact.add_reference(uri, name=None, checksum=True, max_objects=None)` records an external URI instead of uploading bytes.

- Supported reference schemes include `http(s)`, `s3://`, `gs://`, Azure blob HTTPS URLs, and `file://`.
- For local files that should be tracked as references rather than uploaded, use `file://...`; a bare local path is rejected.
- `checksum=True` records size/digest when the storage handler can inspect metadata; `checksum=False` speeds up creation but weakens integrity checking and may not enumerate directory-like references.
- Optional storage dependencies are needed for cloud metadata/download handling: `wandb[aws]` for S3, `wandb[gcp]` for GCS, and Azure storage/identity packages for Azure blob URLs.

## Logging outputs

`Run.log_artifact(artifact_or_path, name=None, type=None, aliases=None, tags=None) -> Artifact` declares an artifact as a run output.

- Pass a prepared `wandb.Artifact` object for explicit metadata, multiple files, references, aliases, and tags.
- Pass a local file path, local directory path, or `s3://...` path for the convenience form; provide `name` and `type` when the default basename is not enough.
- `aliases` defaults to `['latest']` when omitted; use stable names such as `latest`, `production`, `best`, or `candidate` rather than encoding versions in aliases.
- `tags` are separate labels; valid tags contain alphanumeric words separated by hyphens, underscores, or spaces.
- Call `artifact.wait()` when subsequent code needs the artifact committed before lookup or registry linking.

```python
import wandb

with wandb.init(project="artifact-demo", job_type="prepare-data") as run:
    artifact = wandb.Artifact("training-data", type="dataset")
    artifact.add_dir("data/processed", name="processed")
    logged = run.log_artifact(
        artifact,
        aliases=["latest", "2026-06"],
        tags=["curated", "training"],
    )
    logged.wait()
```

## Artifact consumption

`Run.use_artifact(artifact_or_name, type=None, aliases=None, use_as=None) -> Artifact` declares an artifact as a run input and returns an `Artifact` object. Call `download()` or `file()` on the returned object to materialize files.

Valid names include:

- `name:alias`
- `name:v0`
- `project/name:alias`
- `entity/project/name:v0`

`wandb.Api().artifact(name, type=None) -> Artifact` fetches an artifact outside a run. Use it for automation, notebooks, and CLI-like utilities where run lineage is not required. It accepts `project/artifact:alias` and `entity/project/artifact:version` forms.

`Artifact.download(root=None, allow_missing_references=False, skip_cache=False, path_prefix=None, multipart=None) -> str` downloads files and returns the local root.

- Existing files under `root` are not modified. Delete the target directory first if it must exactly match the artifact.
- `path_prefix` downloads only artifact entries whose logical path starts with the prefix.
- `allow_missing_references=True` lets invalid reference paths be skipped during reference downloads.
- `multipart=None` automatically uses multipart download for large files; set explicitly only when debugging download behavior.

`Artifact.file(root=None) -> str` is for single-file artifacts. Use `Artifact.files()` or `download()` for multi-file artifacts.

```python
import wandb

with wandb.init(project="artifact-demo", job_type="train") as run:
    artifact = run.use_artifact("training-data:latest", type="dataset")
    data_dir = artifact.download(root="data/input")
```

## Registries and linking

A registry is backed by a project named with the `wandb-registry-` prefix, but user-facing API methods generally accept the registry name without the prefix when creating/fetching registries.

`Run.link_artifact(artifact, target_path, aliases=None) -> Artifact` links a logged artifact into a collection. If the artifact is a draft and the run is online, W&B logs it first. Offline linking is not implemented.

`Artifact.link(target_path, aliases=None) -> Artifact` links an already logged artifact directly.

Registry collection target path forms used by tests and implementation include:

- `wandb-registry-model/collection-name`
- `org-entity/wandb-registry-model/collection-name`

Use explicit org/entity prefixes when the default entity is ambiguous. `latest` is automatically applied to the most recent linked artifact; pass additional aliases such as `prod`, `staging`, or `candidate`.

```python
import wandb

with wandb.init(entity="team", project="models", job_type="train") as run:
    artifact = wandb.Artifact("classifier", type="model")
    artifact.add_file("model.pkl")
    logged = run.log_artifact(artifact, aliases=["latest"])
    logged.wait()
    linked = run.link_artifact(
        logged,
        "wandb-registry-model/classifier",
        aliases=["candidate"],
    )
```

`wandb.Api().create_registry(name, visibility, organization=None, description=None, artifact_types=None)` creates a registry when the server supports registry creation. `visibility` is `organization` or `restricted`. `artifact_types` restricts accepted artifact types and cannot remove previously saved allowed types.

`wandb.Api().registry(name, organization=None)` fetches one registry. `wandb.Api().registries(organization=None, filter=None, order=None, per_page=100, start=None)` lazily searches registries and can chain to `.collections()` and `.versions()`.

```python
import wandb

api = wandb.Api()
registry = api.registry(name="model", organization="my-org")
for version in registry.versions(filter={"alias": "prod"}):
    print(version.name, version.version)
```

Registry objects support properties such as `name`, `full_name`, `entity`, `organization`, `description`, `artifact_types`, `allow_all_artifact_types`, `visibility`, `collections()`, `versions()`, member methods, `save()`, and `delete()`. These calls require authentication and server support for registry APIs.
