---
name: extensibility
description: "Extend MMDeploy with rewriters, backend/codebase support, custom
  ops, partition marks, and focused developer tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDeploy Extensibility Router

Use this sub-skill when the task is to modify or extend MMDeploy internals rather than run routine model conversion. It covers developer work for:

- function, module, and symbolic rewrites used during export;
- new backend managers, backend wrappers, backend configs, and backend API packages;
- new codebase/task-processor support;
- backend custom ops and partition marks;
- focused rewrite/custom-op tests and skip-aware backend checks.

## Route by task

| User need | Go to |
| --- | --- |
| Make a PyTorch/MMCV/OpenMMLab function exportable, replace a module during export, or emit backend-specific ONNX nodes | [references/rewriters.md](references/rewriters.md) |
| Add a backend, make a backend wrapper discoverable, extend backend/codebase/task enums, or add a codebase task processor | [references/backend-and-codebase-support.md](references/backend-and-codebase-support.md) |
| Add or debug backend custom ops, write a backend op unit test, mark partition boundaries, or connect marks to extraction | [references/custom-ops-and-partitioning.md](references/custom-ops-and-partitioning.md) |
| Write focused tests for rewrites, custom ops, or wrappers; choose pytest targets and interpret backend skips | [references/testing.md](references/testing.md) |
| Diagnose import, checker, backend, config, ABI, symbolic-domain, dynamic-axis, or partition failures | [references/troubleshooting.md](references/troubleshooting.md) |

## Operating boundaries

- Do not use this sub-skill for ordinary deployment commands, checkpoint conversion, quantization runs, benchmarking, SDK runtime inference, or regression orchestration.
- Do not treat backend installation/build as solved here. This sub-skill can identify the required backend/package/plugin evidence and then defer installation-heavy work to the backend/install owner.
- Treat native tests as evidence and future verification candidates. Do not assume every backend stack or optional OpenMMLab codebase is installed.
- Prefer minimal, deterministic developer tests with tiny tensors and explicit expected outputs before attempting full model conversion.

## Standard extension workflow

1. Identify the extension point: function rewrite, module rewrite, symbolic rewrite, backend manager/wrapper, codebase task processor, custom op, or partition mark.
2. Confirm registration/import flow. Decorated rewrites, backend managers, wrappers, and codebase task processors only exist after their containing modules are imported.
3. Add the smallest failing test first. Use direct `RewriterContext` or `patch_model` tests for Python behavior, and use backend-aware export tests only when the backend/plugin is available.
4. Implement the extension with backend-specific registration where behavior diverges by backend. Keep default registrations backend-neutral.
5. Assert recovery: functions and symbolics should revert after `RewriterContext`; module rewrites should be intentionally permanent because `patch_model` mutates the model.
6. If the change depends on a backend package, plugin, or upstream codebase, make skip behavior explicit and stop when the required runtime is unavailable.

## Important invariants

- `RewriterContext` activates function and symbolic rewriters for the selected backend/IR and restores them on exit.
- `patch_model` activates module rewriters and mutates the model by replacing matching submodules.
- `Backend`, `Codebase`, and `Task` enum values must match `backend_config.type` and `codebase_config` values.
- Backend managers are discovered by importing `mmdeploy.backend.<backend_name>`; the backend package `__init__` must import/register the manager.
- Backend wrappers should consume named tensor dictionaries and return output-name keyed dictionaries.
- `@mark` partition nodes must be inside a rewrite path and require `partition_config.apply_marks=True` to appear in exported ONNX.
