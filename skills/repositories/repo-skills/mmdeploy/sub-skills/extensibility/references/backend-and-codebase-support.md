# Backend and codebase support

Use this guide when the task is to add a backend, make a backend wrapper visible, or add a new codebase/task processor.

## Backend support flow

### 1) Decide whether the backend is first-class or third-party

- **First-class backend**: add it to the repository source tree and constants directly.
- **Third-party backend**: register it through the backend manager registry so the enum can be extended at runtime.

### 2) Add or extend the backend enum

For first-class support, add a backend value to `Backend` in the constants module.

For third-party support, the backend manager registry can extend the enum automatically when the manager is registered.

Use this rule:
- the enum value must match `backend_config.type` exactly;
- backend managers, wrappers, and config files should use the same name consistently.

### 3) Add a backend package

Create a backend package with an `__init__.py` that exposes `is_available` and imports the manager when the backend is usable.

The package should answer:
- is the backend library installed?
- if custom ops are required, are the custom-op artifacts present?
- what version should be reported?

### 4) Implement the backend manager

The manager must derive from `BaseBackendManager` and provide at least:

- `build_wrapper(...)` for creating the runtime wrapper;
- `is_available(with_custom_ops=False)`;
- `get_version()`;
- `check_env(...)` when the backend needs a richer environment report;
- `to_backend(...)` when ONNX-to-backend conversion is required.

Manager responsibilities:
- map backend files to the wrapper constructor;
- hide conversion details behind one call;
- keep `check_env` read-only and deterministic.

### 5) Implement the backend wrapper

The wrapper must derive from `BaseWrapper`.

Required behavior:
- `__init__(..., output_names)` must pass output names to the base class;
- `forward(inputs: Dict[str, Tensor])` must accept a named tensor dictionary;
- the wrapper should return a dictionary keyed by output name;
- a low-level engine execute method is preferred when the backend has a separate inference call.

Good wrapper practice:
- normalize device handling in one place;
- preserve output ordering with `_output_names`;
- keep conversion of backend outputs back to `torch.Tensor` explicit.

### 6) Add an API package

Expose backend conversion helpers from `mmdeploy/apis/<backend>/__init__.py` when the backend is available.

The API package should:
- import the backend manager registration side effects;
- export the conversion function(s) needed by higher-level tooling;
- avoid importing unavailable backend libraries eagerly.

## Codebase support flow

### 1) Add the codebase package

Create a codebase package under `mmdeploy/codebase/<name>/deploy/` and register the codebase class with the codebase registry.

The codebase class should implement:
- `register_deploy_modules()` for deploy-time rewrites and support modules;
- `register_all_modules()` for importing the upstream package and then registering deploy modules.

### 2) Add a task registry and task processors

Each supported task needs a task registry and one or more task processor classes derived from `BaseTask`.

Task processors typically implement:
- `build_backend_model()`;
- `create_input()`;
- `get_partition_cfg()`;
- `get_preprocess()`;
- `get_postprocess()`;
- `get_model_name()`.

### 3) Wire the task processor lookup

The deployment flow resolves the codebase from `deploy_cfg`, imports the codebase, looks up the task class, and then builds the task processor.

Keep the lookup stable:
- `codebase_config.type` must map to the codebase name;
- `codebase_config.task` must map to the task enum value;
- any upstream codebase dependencies must be importable before `register_all_modules()` runs.

## Supported enum extension flow

### Backend enum

Use the backend enum when the new backend is part of the supported deployment surface.

- Add the enum value when the backend is first-class.
- Use backend-manager registration to extend the enum for third-party backends.
- Keep `backend_config.type`, backend manager registration, and wrapper registration aligned.

### Codebase enum

- Add a codebase enum value for a new codebase.
- Update codebase registration and import flow so the codebase is discoverable.
- Ensure dependent libraries are checked before import.

### Task enum

- Task values are consumed by codebase task registries and deployment configs.
- Add the task enum value when introducing a new task family.
- Update any task registry and split/partition logic that depends on the new value.

## What to verify

- The backend package imports without eager failure when the backend is absent.
- `get_backend_manager(name)` returns the manager after the package is imported.
- `check_env()` reports a sensible availability string.
- The wrapper can be built from the backend files returned by `to_backend()`.
- `build_task_processor()` resolves the right codebase and task class.
- `codebase_config.type` and `backend_config.type` are consistent with the registered enums.

## Common extension mistakes

- manager registered but the package `__init__` never imports it;
- backend enum and `backend_config.type` disagree;
- wrapper returns positional outputs instead of a named dict;
- codebase task lookup fails because the upstream codebase was never imported;
- third-party backend uses a new enum name but no manager registration ran;
- conversion code assumes backend files are always `.onnx` only.
