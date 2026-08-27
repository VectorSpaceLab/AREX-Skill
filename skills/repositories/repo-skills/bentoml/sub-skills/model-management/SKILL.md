---
name: model-management
description: "Manage BentoML model stores, model references, framework save/load
  helpers, optional dependencies, and model troubleshooting for services and
  builds."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BentoML Model Management

Use this sub-skill when an agent needs to save, inspect, package, load, import/export, or diagnose BentoML models. Keep service endpoint design in `../service-authoring/SKILL.md`; keep Bento build/container packaging mechanics in `../packaging-and-containerization/SKILL.md`; keep BentoCloud deployment in `../cli-and-cloud/SKILL.md`.

## First Decision

1. **Need a model dependency in a Service or Bento build?** Declare `BentoModel("name:version")`, `BentoModel("name:latest")`, or `HuggingFaceModel("org/model")` as a Service class variable so BentoML can include/resolve it during build and deployment.
2. **Need to put files into BentoML's local store?** Use `bentoml.models.create(name)` as a context manager for arbitrary model directories, or a framework helper such as `bentoml.sklearn.save_model()` when that framework helper is appropriate and installed.
3. **Need to inspect or move a stored model?** Use `bentoml models list/get/export/import/delete` or the Python equivalents under `bentoml.models`.
4. **Need to load framework-native objects?** Prefer the matching helper (`bentoml.sklearn.load_model`, `bentoml.pytorch.load_model`, etc.) only when the stored model's `module` matches that helper and its optional dependencies are present.

## Model Store Essentials

- BentoML stores models by tag (`name:version`) and supports `:latest` resolution. `bentoml.models.get(tag)` returns a `bentoml.Model`; `bentoml.models.list(name_or_none)` returns stored model objects.
- `bentoml.models.create(name)` yields a model reference with `path` and `path_of(...)`; write or copy model files inside that directory, then let the context manager flush and save on successful exit.
- Model metadata includes the saved module, labels, options, metadata, context, signatures, BentoML version, Python version, and creation time. Use it to diagnose helper mismatch and serialization/version mismatch.
- Import/export moves BentoML model archives or folders between stores. Use framework save/import APIs for raw framework artifacts; `bentoml.models.import_model()` expects an exported BentoML model archive or folder.
- Store location is controlled by the installed BentoML configuration and environment. If a model appears missing, inspect the active process environment and `bentoml models list --output json` before assuming the tag is wrong.

## Service Loading Pattern

Declare model dependencies at Service class scope, then load the framework object in `__init__` or a method:

```python
import bentoml
from bentoml.models import BentoModel

@bentoml.service
class IrisService:
    model_ref = BentoModel("iris_sklearn:latest")

    def __init__(self):
        import joblib
        self.model = joblib.load(self.model_ref.path_of("model.pkl"))
```

Class-scope declaration is important: BentoML records the model dependency for build, push, and deployment. Creating `BentoModel(...)` only inside `__init__` can produce a Bento that starts without the referenced model and later fails with a model not found error.

For Hugging Face Hub models, use `HuggingFaceModel("org/model")` as a class variable and pass the resolved path to `transformers` loaders in `__init__`. Private or gated Hub models require the appropriate token in the runtime/build environment; do not bake secrets into skill content or service source.

## Commands And APIs

- List models: `bentoml models list` or `bentoml.models.list()`.
- Inspect a model: `bentoml models get MODEL_TAG`, `bentoml models get MODEL_TAG --output json`, `bentoml models get MODEL_TAG --output path`, or `bentoml.models.get("MODEL_TAG")`.
- Export/import: `bentoml models export MODEL_TAG OUT_PATH`, `bentoml models import MODEL_PATH`, `bentoml.models.export_model(tag, path)`, and `bentoml.models.import_model(path)`.
- Delete: `bentoml models delete MODEL_TAG --yes` or `bentoml.models.delete(tag)`. Deletion can fail if a local Bento references the model.
- Cloud transfer: `bentoml models push MODEL_TAG` and `bentoml models pull MODEL_TAG` require BentoCloud auth; keep deployment/cloud workflow in `../cli-and-cloud/SKILL.md`.

## Bundled Helpers

- `scripts/inspect_model_store.py` lists model tags, modules, locations, metadata keys, context, and optional tag details. It is read-only.
- `scripts/check_framework_extra.py` checks whether a framework helper's Python modules are importable and warns about deprecated helper-module usage. It does not install packages or download models.

## References

- Model store operations: `references/model-store.md`.
- Framework helpers and optional dependencies: `references/frameworks.md`.
- Troubleshooting: `references/troubleshooting.md`.
