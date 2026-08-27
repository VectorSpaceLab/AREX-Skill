# Artifact and Registry Workflows

## Create and log versioned artifacts

Use this pattern for datasets, checkpoints, model files, exported reports, or any local directory that should become a reproducible W&B input/output.

1. Decide the artifact identity: stable `name`, semantic `type`, optional `description`, compact JSON metadata.
2. Validate all files or directories exist before creating the upload path.
3. Add entries with artifact-relative names that will still make sense after download.
4. Log with `Run.log_artifact(...)`, set aliases/tags, and call `wait()` if another step immediately fetches or links the artifact.

```python
import wandb

with wandb.init(project="artifact-demo", job_type="prepare") as run:
    dataset = wandb.Artifact(
        "imagenet-subset",
        type="dataset",
        description="Preprocessed subset for smoke training",
        metadata={"split": "train", "format": "jpg"},
    )
    dataset.add_dir("data/imagenet-subset", name="images")
    dataset.add_file("data/labels.csv", name="labels.csv")
    logged = run.log_artifact(dataset, aliases=["latest", "curated"])
    logged.wait()
```

For a single path, the convenience form is shorter:

```python
with wandb.init(project="artifact-demo") as run:
    run.log_artifact(
        "checkpoints/model.pkl",
        name="classifier",
        type="model",
        aliases=["latest", "candidate"],
    )
```

Use `add_reference()` when W&B should track external storage metadata but not upload bytes:

```python
artifact = wandb.Artifact("raw-training-data", type="dataset")
artifact.add_reference("s3://example-bucket/datasets/train/", name="raw", checksum=True)
```

## Dry-run local preparation without accidental upload

W&B artifact objects are draft objects until logged. To prepare code safely without uploading:

- Validate names, types, and paths locally before `wandb.init()`.
- Build `wandb.Artifact` and add local files/dirs, but do not call `run.log_artifact()`.
- Use `WANDB_MODE=offline` only when intentionally creating local run data for later `wandb sync`; offline mode can still write run files locally.
- Use the bundled helper `scripts/artifact_manifest_smoke.py` to preview a manifest-like mapping without creating a run or contacting W&B.

Example helper usage from the root skill directory:

```bash
python sub-skills/artifacts-and-registries/scripts/artifact_manifest_smoke.py \
  --name training-data \
  --type dataset \
  --file data/labels.csv:labels.csv \
  --dir data/features:features
```

## Consume and download artifacts

Inside a run, use `Run.use_artifact()` to preserve lineage:

```python
import wandb

with wandb.init(project="artifact-demo", job_type="train") as run:
    dataset = run.use_artifact("training-data:latest", type="dataset")
    input_dir = dataset.download(root="inputs/training-data")
```

Outside a run, use `wandb.Api().artifact()`:

```python
import wandb

artifact = wandb.Api().artifact("team/project/training-data:v3", type="dataset")
path = artifact.download(root="downloads/training-data-v3")
```

When debugging downloads:

- Use `entity/project/name:alias` or `entity/project/name:vN` when defaults may resolve to the wrong project.
- Prefer version pins (`:v0`, `:v7`) for reproducible production jobs; use aliases (`:latest`, `:prod`) for moving channels.
- Pass `path_prefix="subdir/"` to download only a subset.
- Delete the target root first if the download directory must not contain stale files.

## Link artifacts to registries

Linking creates a registry collection pointer without duplicating artifact storage. The source artifact must be logged first, and registry operations require online/authenticated access and server support.

```python
import wandb

with wandb.init(entity="team", project="models", job_type="train") as run:
    model = wandb.Artifact("resnet50", type="model")
    model.add_file("outputs/resnet50.pt", name="model.pt")
    logged = run.log_artifact(model, aliases=["latest"])
    logged.wait()
    run.link_artifact(
        logged,
        "wandb-registry-model/resnet50",
        aliases=["candidate", "benchmark-winner"],
    )
```

Use the fully qualified target when organization/entity resolution is ambiguous:

```python
logged.link("org-entity/wandb-registry-model/resnet50", aliases=["prod"])
```

Registry collection target paths normally look like `wandb-registry-{registry-name}/{collection-name}`. The `Api.create_registry()` and `Api.registry()` methods accept `name="model"` without the `wandb-registry-` prefix.

## Manage registries with Public API

Create a restricted model registry that accepts only model artifacts:

```python
import wandb

api = wandb.Api()
registry = api.create_registry(
    name="model",
    visibility="restricted",
    organization="my-org",
    description="Production model registry",
    artifact_types=["model"],
)
```

Fetch and search registry content:

```python
api = wandb.Api()
registry = api.registry(name="model", organization="my-org")
for collection in registry.collections(filter={"name": {"$regex": "resnet"}}):
    print(collection.name)

for version in registry.versions(filter={"alias": "prod"}):
    print(version.name, version.version, version.aliases)
```

Update registry metadata only after confirming server support and permissions:

```python
registry.description = "Production and candidate model artifacts"
registry.save()
```

## Alias, tag, and version strategy

- Use artifact versions (`v0`, `v1`, `v2`) as immutable pins.
- Use aliases as mutable channels (`latest`, `prod`, `staging`, `candidate`, `best`). Aliases must not contain `/` or `:`.
- Use tags for filtering and grouping (`trained`, `baseline`, `reviewed`). Tags accept alphanumeric words separated by hyphens, underscores, or spaces.
- Do not encode credentials, absolute machine paths, or private storage locations in artifact names, aliases, tags, descriptions, or public metadata.
- Prefer type names that describe the role (`dataset`, `model`, `predictions`, `eval-results`) and remain stable across projects.
