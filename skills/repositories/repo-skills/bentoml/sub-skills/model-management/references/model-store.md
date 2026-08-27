# Model Store Reference

## Save Arbitrary Model Files

Use `bentoml.models.create()` when the model artifact is a directory or collection of files that BentoML should version without a framework-specific helper.

```python
import shutil
import bentoml

with bentoml.models.create("my-model", labels={"stage": "dev"}) as model_ref:
    shutil.copytree("/path/to/local/model", model_ref.path, dirs_exist_ok=True)
    print(model_ref.tag)
```

Rules:

- The context manager saves only on successful exit; exceptions keep partial writes from becoming a valid stored model.
- Use `model_ref.path` for a model root and `model_ref.path_of("relative/file")` for files beneath it.
- Keep labels/metadata small and serializable; they are for discovery and diagnostics, not large artifacts.
- Deprecated advanced arguments such as `module`, `api_version`, `signatures`, `options`, `custom_objects`, `external_modules`, and `context` exist for compatibility, but new arbitrary-directory workflows should not depend on them unless matching an existing stored format.

## Inspect Models

CLI:

```bash
bentoml models list
bentoml models list MODEL_NAME --output json
bentoml models get MODEL_TAG --output yaml
bentoml models get MODEL_TAG --output json
bentoml models get MODEL_TAG --output path
```

Python:

```python
import bentoml

for model in bentoml.models.list():
    print(model.tag, model.info.module, model.path)

model = bentoml.models.get("iris_sklearn:latest")
print(model.info.to_dict())
```

Important fields:

- `tag`: stable identifier in `name:version` form; `:latest` resolves at lookup time.
- `module`: framework helper that saved the model, such as `bentoml.sklearn`, or an empty/custom module for arbitrary files.
- `context`: records framework versions, BentoML version, and Python version available at save time.
- `metadata`, `labels`, `options`, `signatures`: user/helper-provided information that can explain how to load the artifact.

## Use Models In Services

Use `BentoModel` at Service class scope when the model must be included or resolved as a service dependency:

```python
import bentoml
from bentoml.models import BentoModel

@bentoml.service
class MyService:
    model_ref = BentoModel("model-name:latest")

    def __init__(self):
        self.model_path = self.model_ref.path
```

Guidelines:

- Put `BentoModel(...)` and `HuggingFaceModel(...)` declarations on the Service class, not only in `__init__`.
- For raw files, load from `model_ref.path` or `model_ref.path_of("file")` with the framework's own loader.
- If the model is available remotely but not locally, BentoML can resolve/pull it through the configured BentoCloud client. If auth or remote lookup fails, the error should be treated separately from a local tag typo.
- Add model tags to build configuration when building a Bento from a non-class-scope or CLI-only workflow; see `../../packaging-and-containerization/SKILL.md` for build packaging mechanics.

## Move Models Between Stores

CLI:

```bash
bentoml models export MODEL_TAG ./model.bentomodel
bentoml models import ./model.bentomodel
```

Python:

```python
import bentoml

archive_path = bentoml.models.export_model("my-model:latest", "./my-model.bentomodel")
imported = bentoml.models.import_model(archive_path)
```

Supported archive outputs include BentoML's `.bentomodel` format, folders, and common compressed archives. Remote filesystem URLs such as S3 require the relevant filesystem extra package, for example an S3 filesystem package for `s3://...` targets.

## Delete Safely

```bash
bentoml models delete MODEL_TAG --yes
```

Before deleting:

- Check `bentoml models get MODEL_TAG` and local Bentos that reference the model.
- Deleting by name can delete multiple versions after confirmation.
- The CLI prevents deleting a model that is referenced by local Bentos in the active store.

## Diagnose Store Location

When model tags appear inconsistent across shell, tests, builds, and services:

1. Run `bentoml models list --output json` in the same environment as the failing command.
2. Run `bentoml models get TAG --output path` to confirm the resolved physical path.
3. Check environment variables and BentoML configuration used by that process; do not assume another shell, container, or CI worker uses the same store.
4. Use `scripts/inspect_model_store.py --tag TAG` to print the active store view without mutating it.
