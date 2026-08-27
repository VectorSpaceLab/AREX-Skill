# Component Development Troubleshooting

Use this guide to diagnose component authoring, extension bundle, dynamic loading, and component test failures.

## Install and Import Failures

### `ModuleNotFoundError` for `lfx`, `langflow`, or schema imports

Signals:

- `ModuleNotFoundError: No module named 'lfx'`
- `ModuleNotFoundError: No module named 'langflow'`
- `ImportError` from `lfx.schema` or `lfx.io`

Fixes:

- Install the package in the active environment before importing components.
- Use current imports for new components: `lfx.custom.custom_component.component.Component`, `lfx.io`, `lfx.schema.message.Message`, and `lfx.schema.data.Data`.
- Keep compatibility imports only when maintaining old code.
- In a source checkout, run commands through the project's Python environment so editable packages are visible.

### Optional provider dependency missing

Signals:

- A component import fails before tests run because a provider SDK is missing.
- Component index rebuild fails while importing an unrelated provider module.
- A bundle works locally but fails after wheel install because the provider package was not declared.

Fixes:

- Move heavy imports inside the output method or a `_build_client()` helper when possible.
- Declare direct runtime dependencies in the owning package or bundle `pyproject.toml`.
- Put heavy local stacks behind optional extras if the component can operate remotely or in a limited mode.
- Guard credentialed/native tests with skip logic or markers.
- Run the skeleton checker without `--import-module` first; only use import mode in a fully prepared environment.

### `langflow --help` or server import fails because `openai` is missing

The verified Langflow line imports OpenAI through the current CLI import path. Install the core runtime dependencies before expecting `langflow` CLI help or server startup to work. This is a runtime environment issue, not a component skeleton issue.

## Component Schema and Config Errors

### `Output(method=...)` points to a missing method

Signals:

- Static checker reports `Output method '...' is not defined`.
- Runtime raises an attribute error while building output types or executing the component.
- A node appears but fails when its output is selected.

Fixes:

- Rename the method in `Output(method="...")` or add the missing instance method.
- Keep old output methods as wrappers if flows already reference them.
- Prefer explicit return annotations on output methods.

### Input and output names overlap

Signal:

```text
ValueError: Inputs and outputs have overlapping names: {...}
```

Fixes:

- Give each input and output a unique `name`.
- Use a semantic output name such as `message`, `data`, `dataframe`, `tool`, or `result` instead of reusing the input field name.

### Field removed or renamed breaks saved flows

Signals:

- Existing flows lose edges after opening.
- Tweaks no longer affect the intended field.
- Compatibility tests fail for older versions.

Fixes:

- Restore the old field name and mark it deprecated instead of removing it.
- Add a new optional field for the new behavior.
- Document migration instructions if the old behavior cannot be preserved.
- Update `file_names_mapping` tests for released components.

### Non-serializable return value

Signals:

- Frontend node output cannot render.
- JSON serialization errors mention provider objects, clients, file handles, coroutines, or Pydantic serialization.
- Downstream components reject the output type.

Fixes:

- Return `Message`, `Data`, `DataFrame`, `list[Data]`, or the exact integration object expected by a `HandleInput`.
- Convert provider responses into plain dict/list/string values inside `Data(data={...})`.
- Await coroutines before returning.
- Keep clients and sessions on local variables or private attributes, not in display outputs.

### Secret value validation errors

Signals:

- Credential fields fail validation when passed through a non-password input.
- Secrets appear masked where raw provider clients require strings.

Fixes:

- Use `SecretStrInput` or a password-capable input for credentials.
- Read the runtime value from `self.<field_name>` inside component code.
- Do not print or store credential values in `Data`, `Message`, logs, test snapshots, or templates.

## CLI and API Misuse

### `lfx extension validate` cannot find a manifest

Signals:

- `manifest-not-found`
- Validation run against the package parent instead of the package root.

Fixes:

- Point validation at the directory containing `extension.json` or `pyproject.toml` with `[tool.langflow.extension]`.
- If using a wheel package, ensure `extension.json` is included in build targets.

### `version-constraint-unsatisfied`

Signal:

- The manifest `lfx.compat` list does not include the current bundle API version.

Fixes:

- Use `"lfx": {"compat": ["1"]}` for the verified v1 bundle API line.
- Do not guess future compatibility; add new values only after testing with that API contract.

### `path-escape` or `bundle-path-not-found`

Signals:

- Manifest validation rejects `bundles[].path`.
- The bundle works in an editable checkout but not after packaging.

Fixes:

- Make `bundles[].path` relative to the manifest directory.
- Do not use absolute paths or `..`.
- Ensure the directory exists and is included in the wheel/sdist.

### Component missing after upgrade

Signals:

- `component-not-found`
- `component-not-found-with-hint`
- `component-name-ambiguous`

Fixes:

- Install the bundle named by the hint.
- Prefer canonical extension IDs shaped like `ext:<bundle>:<Class>@official` when disambiguating.
- Add or update migration metadata when moving a built-in component into a bundle.
- Preserve class and `name` identifiers for released components.

## Backend, Runtime, and Service Boundaries

### Graph context errors

Signal:

```text
ValueError: Graph not found. Please build the graph first.
```

Fixes:

- Do not access `self.ctx`, vertex neighbors, or graph services during `__init__` or class definition.
- Access graph context only inside runtime methods after the graph is built.
- In isolated tests, use component test base helpers or mock the vertex/graph intentionally.

### Network, credential, or provider failures

Signals:

- Provider SDK returns 401/403, timeout, DNS, SSL, quota, or model-not-found errors.
- Tests fail only when external services are unavailable.

Fixes:

- Validate input shape and credentials before making network calls.
- Catch provider-specific request errors and return a clear `Data` or `Message` error when that is the component's expected UX.
- Skip native tests without required API keys instead of embedding credentials.
- Keep static tests and parsing checks independent of network access.

### Hardware or model backend unavailable

Signals:

- Torch, transformers, OCR, GPU, CUDA, or model runtime warnings appear during import or tests.
- Importing a component starts downloading models.

Fixes:

- Keep model execution out of import time.
- Gate local model/OCR/Torch paths behind optional extras and explicit user configuration.
- Provide a lightweight remote-mode or mock path for unit tests when possible.
- Treat PyTorch/transformer execution as out of scope unless the environment explicitly installed those dependencies.

## Dynamic Loading and Index Failures

### New component does not appear in the palette

Fixes:

- Start the server with `LFX_DEV=1` for full dynamic loading while developing.
- For selective reload, set `LFX_DEV=<module>` with the lower-case module/category name.
- Ensure the component module is importable and exported by the category package or dynamic import map.
- For extension bundles, validate the manifest and confirm the package is installed/discovered with `lfx extension list`.

### Component index rebuild fails

Signals:

- Failure while importing components.
- Index hash or version mismatch warnings.
- Missing optional dependency from a provider component.

Fixes:

- Run static skeleton checks on changed components first.
- Install declared runtime dependencies for the component set being indexed.
- Fix import-time side effects and undeclared dependencies instead of editing `component_index.json` by hand.
- Re-run with `LFX_DEV=1` after the import issue is fixed.

## Test Failures

### Required fixture missing in component tests

Signals:

- `NotImplementedError` from `component_class` or `file_names_mapping`.
- Base class validation fails before custom tests run.

Fixes:

- Implement `component_class`, `default_kwargs`, and `file_names_mapping` fixtures in every component test class.
- Use `ComponentTestBaseWithoutClient` unless the component requires a FastAPI client.
- Use `ComponentTestBaseWithClient` only for tests that need backend client fixtures.

### Version compatibility test fails

Signals:

- Supported version missing from `file_names_mapping`.
- Historical module/file name cannot build.

Fixes:

- Add the released version mapping with the historical module and file name.
- Use the test sentinel for versions where the component truly did not exist.
- Do not paper over a class/name rename by changing only the test; preserve or migrate the component identity.

### Async test or output method behaves inconsistently

Fixes:

- Mark async pytest methods correctly for the repository's async test setup.
- Await component output methods when calling them directly.
- Avoid shared mutable class-level state except `inputs` and `outputs`, which the base class copies per instance.
- Do not reuse `Output` instances manually across component classes.

## Quick Diagnostic Order

1. `python -m py_compile path/to/component.py`
2. `python scripts/check_component_skeleton.py path/to/component.py`
3. `python scripts/check_component_skeleton.py path/to/component.py --import-module` when dependencies are installed.
4. `lfx extension validate path/to/extension/root` for bundles.
5. `make build_component_index` for built-in component index changes.
6. `python -m pytest path/to/component_test.py -q` for focused native behavior.
