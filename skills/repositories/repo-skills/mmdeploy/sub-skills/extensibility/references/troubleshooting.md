# Extensibility troubleshooting

Use this file for developer-extension failures owned by this sub-skill.

## Install and import failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| `ImportError: <codebase> has not been installed` while building a task processor | Upstream OpenMMLab codebase is not installed; dependent library is missing; custom module list was not imported | Install or enable the required upstream package; confirm the codebase dependency list; import custom modules before `import_codebase`; use a tiny unit test that imports only the task processor if full codebase install is not intended | The feature requires an upstream codebase that is unavailable and no synthetic substitute can prove the extension |
| Rewriter warning says target function cannot be found | Wrong function path; upstream version changed; containing module was never imported; target is a derived method with a different path | Import the module containing the target; check the fully qualified path; write a small direct import/eval check; add version guards if the path changed across versions | The upstream API path is unknown or ambiguous and the rewrite could patch the wrong function |
| Decorated rewrite never registers | The file containing the decorator is not imported; codebase `register_deploy_modules` omits it; package `__init__` does not expose it | Add import side effects to the deploy module registration path; verify import before export; run a minimal `RewriterContext` test that proves the rewrite fires | Importing the decorator requires optional packages that are unavailable and there is no safe guard |
| Custom backend package import fails immediately | `__init__` imports heavy backend libraries eagerly; missing optional package; manager registration hidden behind availability code | Keep manager registration import lightweight; guard wrapper/conversion imports behind `is_available()`; make `check_env` report absence instead of crashing | Import requires proprietary SDK files or hardware libraries that cannot be installed in the current environment |

## Optional dependency and backend availability failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| `backend_checker` or `check_backend` skips a test | Backend package is not installed; custom ops/plugin not compiled; `require_plugin=True` and plugin path is missing | Treat skip as expected when backend is optional; install/build the backend only if required; verify `is_available(with_custom_ops=True)` for custom-op tests | The test requires unavailable hardware, SDK, CUDA/TensorRT, or compiled plugins |
| `check_env` reports `None` or `CheckFailed` | Manager `is_available()` cannot import backend; `get_version()` raises; backend manager not discoverable | Call the manager directly in a small probe; make `get_version()` handle missing packages; ensure manager registration runs through package import | Backend SDK/runtime is absent or proprietary and the task cannot be proven without it |
| Backend wrapper added but never discovered | Backend enum mismatch; manager registration name mismatch; package `__init__` does not import manager; `backend_config.type` differs; third-party enum extension did not run | Align enum value, manager name, wrapper registration name, and config type; import `mmdeploy.backend.<backend>`; verify `get_backend_manager(name)` returns the manager | The backend is third-party and its registration code cannot be imported before config parsing |
| Custom op library exists but is not loaded | Plugin path helper points elsewhere; ABI mismatch; package imports wrapper before plugin path exists; backend requires `with_custom_ops=True` | Check plugin path helper; load required base library before custom ops when needed; rebuild custom ops against the active backend/PyTorch/SDK versions; rerun `is_available(with_custom_ops=True)` | ABI/toolchain mismatch cannot be fixed in the current environment |

## Config, data, and API misuse

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| `Backend.get(...)` raises `KeyError` | `backend_config.type` is wrong; backend enum missing; third-party enum extension not registered | Fix the config string; add/extend the enum; import backend manager registration before parsing the config | The backend name is not part of the intended supported surface |
| `Task.get(...)` or task lookup fails | `codebase_config.task` does not match a task enum; task registry lacks a processor; codebase registration did not run | Add the task enum; register the task processor; call codebase `register_all_modules`; verify `build_task_processor` with a tiny config | Required task semantics are unclear or overlap an existing task with incompatible IO |
| `get_partition_config()` returns `None` | No `partition_config`; `apply_marks` missing/false; config object not loaded as expected | Add `partition_config.apply_marks=True`; load the config with the same API used by export; assert the returned partition dict before export | The conversion path must not apply marks for the selected workflow |
| `extract_model` extracts the wrong graph or fails to find markers | Marker names in config do not match ONNX `Mark` node metadata; multiple mark calls need explicit indexes; dynamic axes or name maps are wrong | Inspect exported ONNX node attributes; use exact `mark:type` or `mark[index]:type` strings; align `output_names`, name maps, and dynamic axes | No stable tensor boundary exists for the requested partition |
| CLI/API call has missing `backend_config.type`, `codebase_config.type`, or `codebase_config.task` | Deploy config is incomplete for developer API use | Add the required fields to the minimal config; keep backend and codebase values consistent with enums | The caller only has a partial config and cannot supply the missing routing fields |
| Tensor shapes fail during backend export | Dynamic axes missing; TensorRT shape ranges absent; NCNN batch constraints violated; output names do not match graph | Add `dynamic_axes`; define backend model input shapes; keep NCNN batch constraints explicit; align input/output names with exported graph | Required dynamic shape range is unknown or backend does not support it |

## Rewriter workflow failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| Default symbolic should vary for TensorRT but does not | Only default symbolic registered; backend-specific symbolic missing; wrong backend name; decorator file not imported | Add `SYMBOLIC_REWRITER.register_symbolic(..., backend='tensorrt')`; export tiny graphs for default and TensorRT; assert node domain/op type; verify module import | TensorRT-specific node requires a plugin that is unavailable and cannot be tested even at graph level |
| Function rewrite changes behavior outside context | Rewrite mutated global state outside `RewriterContext`; recovery failed; test reused patched objects | Keep rewrite logic inside `RewriterContext`; assert original behavior after exit; avoid modifying module globals beyond the target rewrite | Recovery cannot be proven with a minimal unit test |
| Module rewrite did not replace target | Target path points to base class but instance type differs; wrapper class not registered; `patch_model` called with wrong backend; recursive traversal disabled | Check `type(module)` and bases; register the exact module type; call `patch_model` with matching backend; keep `recursive=True` unless deliberate | Upstream model structure is unknown or not importable |
| Module rewrite replaces too much | Base class target is too broad; recursive traversal hits unintended children; wrapper class matches a superclass | Narrow the registered module type; add assertions on replaced module paths; use a tiny model with multiple candidate modules | Replacement scope cannot be bounded safely |
| Rewritten Python output differs from backend output | Backend precision/layout differences; custom-op implementation mismatch; wrong expected result; dynamic axes omitted; unsupported op lowered differently | Compare PyTorch, rewritten Python, ONNX graph, and backend output separately; use `expected_result` for backend tests; tolerate only documented small mismatch | Mismatch is semantic, not numeric, and the correct backend behavior is unclear |

## Custom-op and ABI failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| ONNX graph has `onnx::` op instead of `mmdeploy::` op | Symbolic rewrite not active; wrong `is_pytorch` flag; missing autograd function path; `RewriterContext` not used | Ensure the symbolic decorator module is imported; wrap export in `RewriterContext`; assert graph node domain/op type | The target operation cannot be intercepted by symbolic registration |
| Backend says op is unregistered or unknown | Python symbolic op type/domain does not match backend plugin; plugin not compiled/loaded; opset mismatch | Align `g.op('mmdeploy::<OpName>')` with plugin registration; rebuild/load plugin; assert custom op availability | Backend does not support custom op loading in the environment |
| Custom-op build fails with compiler/CUDA/ABI errors | Backend SDK version mismatch; PyTorch/MMCV ABI mismatch; CUDA toolkit/driver mismatch; missing compiler/CMake flags | Rebuild with versions matching the active Python packages and backend SDK; clean stale build artifacts; check compiler and CUDA versions before retry | Required compiler, SDK, CUDA, or hardware is unavailable |
| Test passes in Python but fails in backend | `forward` returns dummy/random export values; backend plugin semantics differ; test did not set `expected_result`; tolerance too strict or too loose | Use deterministic inputs; compute explicit expected output; compare backend output via `run_and_validate`; only allow `tolerate_small_mismatch` for known precision noise | Backend semantic contract is not known well enough to assert correctness |

## Partition-specific failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| `Mark` nodes are absent in ONNX | `@mark` not executed inside rewrite; `apply_marks` false; export did not use `RewriterContext`; TorchScript path removes marks | Move mark into the rewritten function; enable marks in config; export with ONNX and `RewriterContext`; verify `mmdeploy::Mark` nodes | Selected IR is TorchScript or the workflow intentionally disables marks |
| Marker names contain unexpected suffixes | Marked value is a list, tuple, or dict; multiple mark calls increment `func_id` | Inspect mark attributes; update partition config with suffixed names or indexed mark names | Output container structure is dynamic and cannot be named stably |
| Calibration/partition data is missing for marked boundary | Mark forward rewrite did not receive calibration context; partition type not registered; partition config type wrong | Verify partition config type; confirm predefined partition config exists; ensure calibration context fields are passed only in calibration workflows | The partition policy cannot be mapped to a known codebase task processor |
