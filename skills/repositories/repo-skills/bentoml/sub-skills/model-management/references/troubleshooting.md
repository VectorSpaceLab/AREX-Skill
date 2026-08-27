# Model Management Troubleshooting

## `ModelNotFound` Or `NotFound`

Checklist:

1. Confirm the exact tag: `bentoml models list` and `bentoml models list MODEL_NAME --output json`.
2. If using `:latest`, check that at least one version exists under that name in the same active store.
3. Run `bentoml models get TAG --output path` in the same shell/container/process environment as the failing command.
4. If a Service uses `BentoModel` or `HuggingFaceModel`, make sure the declaration is a class variable, not created only inside `__init__`.
5. If the model should come from BentoCloud, distinguish local miss from remote auth/network failure; `BentoModel.resolve()` can report that local lookup failed and remote fetch also failed.
6. If building a Bento, make sure the model is declared as a service dependency or included in the build config `models` section.

Common fix:

```python
from bentoml.models import BentoModel

@bentoml.service
class Service:
    model_ref = BentoModel("my-model:latest")
```

## Missing Optional Framework Extra

Symptoms:

- Importing `bentoml.sklearn`, `bentoml.pytorch`, `bentoml.transformers`, or another helper raises a missing dependency exception.
- Service works locally but container or deployment fails when importing the helper.
- `load_model()` fails before looking up the tag because the framework package is absent.

Actions:

1. Run `scripts/check_framework_extra.py FRAMEWORK` in the target environment.
2. Add the missing framework package to the project's runtime/build dependency declaration; do not install it imperatively from the skill.
3. For GPU frameworks, install a package build compatible with the target CUDA/driver/runtime.
4. If the model was saved as raw files, avoid helper imports and load through `BentoModel(...).path` with a dependency-light loader.

## Serialization Or Import Errors

Symptoms:

- `bentoml.models.import_model()` rejects an artifact directory.
- Framework `load_model()` says the stored module does not match the helper.
- Pickle/joblib/torch/TensorFlow loading fails after the model tag resolves.

Actions:

1. Determine whether the artifact is a BentoML exported model archive/folder or a raw framework artifact.
2. Use `bentoml.models.import_model()` only for exported BentoML model archives/folders.
3. Use framework `save_model()` or `import_model()` APIs for raw framework artifacts when available.
4. Inspect `model.info.module`; use the same helper that saved the model.
5. Check `model.info.context.framework_versions` and Python version if pickle-like loading fails.

## GPU Or Runtime Mismatch

Symptoms:

- PyTorch/TensorFlow/ONNX loads locally but fails in a container or cloud runtime.
- ONNX provider errors mention unavailable execution providers.
- CUDA is unavailable or incompatible at service startup.

Actions:

1. Separate model lookup from framework runtime loading: first verify `bentoml.models.get(TAG)` or `BentoModel(TAG).stored`.
2. Check the framework package, CUDA build, driver, and requested device/provider.
3. For PyTorch, avoid hard-coding `device_id="cuda:0"` unless GPU availability is guaranteed.
4. For ONNX, pass providers that exist in the installed `onnxruntime` package.
5. Put runtime dependency and resource choices in service/build/deployment configuration; see `../../service-authoring/SKILL.md` and `../../packaging-and-containerization/SKILL.md`.

## Store Location Confusion

Symptoms:

- `bentoml models list` differs between terminal, tests, build, and service.
- A tag exists locally but is missing during `bentoml build` or `bentoml serve`.

Actions:

1. Run the same command from the same working directory and environment as the failing process.
2. Print `bentoml models get TAG --output path` to confirm the active store location.
3. Check environment variables and BentoML configuration used by the process.
4. Avoid hard-coded local model-store paths in public skills and generated service code.
5. If tests isolate the store, create/import test models inside the test setup rather than relying on a user's global store.

## Deprecated Framework API Warnings

The framework modules can be routed through a compatibility importer and may warn that `bentoml.<framework>` is deprecated in modern BentoML. Treat this as a migration signal, not necessarily an immediate runtime failure.

Prefer:

- `BentoModel`/`HuggingFaceModel` class-scope declarations for service dependencies.
- Explicit raw file loading from `model_ref.path` when the artifact layout is known.
- Framework helpers only when preserving existing saved model formats or when helper behavior is specifically required.

## Build Config Model Inclusion Case

If a build deploys without a model:

1. Check whether the Service declares `BentoModel`/`HuggingFaceModel` as a class variable.
2. If not, add the model to the build configuration `models` section or refactor to class-scope declaration.
3. Rebuild and inspect the Bento's model metadata rather than only testing local `bentoml serve` against a global store.
