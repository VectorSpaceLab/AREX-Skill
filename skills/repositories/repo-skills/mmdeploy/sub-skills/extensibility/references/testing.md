# Testing extensibility changes

Use focused tests before running broad conversion or regression workflows. Native tests are evidence and verification candidates; they are not required at runtime outside a repository checkout.

## Core test utilities

### `WrapFunction`

Wrap a plain function as a `torch.nn.Module` so it can be exported or passed to backend validation utilities.

Use when testing:
- a standalone PyTorch function rewrite;
- an op symbolic rewrite;
- a custom-op export path.

### `WrapModel`

Wrap one method of a model as the module `forward`.

Use when testing:
- model-method rewrites;
- codebase task processor helper methods;
- rewrites that require a real module instance.

### `get_model_outputs`

Runs the original model method directly and returns the PyTorch output. Use it as the baseline for a rewrite comparison.

### `get_rewrite_outputs`

Runs the model under `RewriterContext`, exports to the configured IR, and optionally runs the backend.

Return shape:
- `(outputs, True)` means outputs came from the backend runtime;
- `(outputs, False)` means backend runtime was unavailable and outputs came from the rewritten Python path.

Test both branches when backend availability is optional.

### `backend_checker` and `check_backend`

- `backend_checker(backend, require_plugin=False)` returns a pytest skip marker.
- `check_backend(backend, require_plugin=False)` calls `pytest.skip(...)` when the backend is not available.
- Use `require_plugin=True` for custom-op tests that need compiled backend plugins.

## Test patterns

### Function rewrite

Assertions:
- original behavior outside `RewriterContext`;
- rewritten behavior inside matching backend context;
- original behavior inside non-matching backend context;
- restoration after context exit.

### Module rewrite

Assertions:
- `patch_model(model, cfg, backend=...)` replaces the intended module type;
- wrong backend does not replace it;
- wrapper constructor accepts only intended kwargs;
- mutation is intentional and limited to the model instance under test.

### Symbolic rewrite

Assertions:
- exported ONNX graph has expected domain and op type for the default backend;
- backend-specific registration changes only the intended node;
- symbolic unregisters after context exit;
- PyTorch built-in symbolics use `is_pytorch=True` and argument descriptors when needed.

### Custom op

Assertions:
- `backend.check_env()` skips when backend/plugin is absent;
- `run_and_validate` compares backend output to PyTorch or expected output;
- input/output names match exported graph names;
- dynamic axes are passed when dimensions vary;
- precision tolerance is justified, not used as a blanket workaround.

## Useful pytest selections

Run only the smallest relevant tests.

```bash
pytest tests/test_core/test_function_rewriter.py -q
pytest tests/test_core/test_module_rewriter.py -q
pytest tests/test_core/test_symbolic_register.py -q
pytest tests/test_core/test_mark.py -q
pytest tests/test_pytorch/test_pytorch_ops.py -q
pytest tests/test_mmcv/test_mmcv_ops.py -q
pytest tests/test_ops/test_ops.py::test_roi_align -q
pytest tests/test_ops/test_ops.py::test_grid_sample -q
pytest tests/test_ops/test_ops.py::test_modulated_deform_conv -q
```

Selection guidance:
- use `test_function_rewriter` for backend-specific function selection and recovery;
- use `test_module_rewriter` for `patch_model` behavior;
- use `test_symbolic_register` for default versus backend-specific symbolic nodes;
- use `test_mark` for partition marker metadata;
- use op-specific tests only when the relevant backend/plugin exists.

## Minimal expected checks for new contributions

Before considering a change complete:

1. add one unit test that fails before the change;
2. assert both selected backend and wrong-backend behavior when the feature is backend-specific;
3. assert recovery or skip behavior;
4. include an import/registration check if the feature depends on decorators or managers;
5. keep test tensors tiny and deterministic.

## Two hard verification cases to preserve

### Backend-specific symbolic rewrite

Scenario: a contributor writes a default symbolic but TensorRT needs a different op.

Expected guidance:
- use `SYMBOLIC_REWRITER.register_symbolic(..., backend='tensorrt')` for the TensorRT variant;
- keep the default symbolic available for other backends;
- export a tiny model twice and assert the ONNX node domain/op type differs only in the TensorRT context;
- do not solve the TensorRT case by branching on backend inside one default symbolic unless registration cannot express it.

### Backend wrapper invisible to `check_env`

Scenario: a contributor adds a wrapper class but environment checks never report the backend.

Expected guidance:
- confirm backend enum value exists or is extended by manager registration;
- confirm backend manager uses the same name as `backend_config.type`;
- confirm backend package `__init__` imports the manager;
- confirm `is_available()` can succeed without importing optional heavy modules too early;
- confirm wrapper registration and manager `build_wrapper()` use the same backend name.
