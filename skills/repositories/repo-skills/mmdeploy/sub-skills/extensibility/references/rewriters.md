# Rewriters

Use this guide when the task is to make MMDeploy rewrite Python behavior or export symbolic nodes differently by backend.

## Choose the right rewriter

### `FUNCTION_REWRITER`
Use when you need to replace a Python function or method during export.

Typical cases:
- change one operator implementation for a specific backend;
- adapt a method on a model class;
- keep the original Python function for normal execution but use a rewritten path in export context.

Registration shape:
- `func_name`: import path of the target function or method.
- `backend`: backend name, or default when backend-neutral.
- `ir`: IR gate when the rewrite only applies to ONNX or TorchScript.
- `extra_checkers`: optional extra guards for library versions or custom conditions.

### `MODULE_REWRITER`
Use when the entire module should be replaced with a wrapper class.

Typical cases:
- wrap a backbone/head block with a backend-friendly proxy;
- swap a submodule that needs a different `forward` or weight setup;
- patch a nested model tree before export.

### `SYMBOLIC_REWRITER`
Use when the exported ONNX node should differ from the default symbolic behavior.

Typical cases:
- replace a default symbolic for one backend;
- add a custom symbolic for a PyTorch builtin;
- override a custom autograd function symbolic.

## Context fields and access pattern

### Function rewriter context
Inside a rewritten function, use:

- `ctx = FUNCTION_REWRITER.get_context()` or `FUNCTION_REWRITER.get_context('qualified.name')`
- `ctx.cfg`: deployment config passed through the rewrite context
- `ctx.origin_func`: the original callable being replaced
- extra fields from the registration record, if any

Preferred pattern:
- call `ctx.origin_func(...)` when you need the original behavior as a fallback;
- branch on `ctx.cfg` only when the behavior depends on export config;
- keep the rewritten function deterministic and side-effect free.

### Symbolic rewriter context
Inside a symbolic rewrite, use:

- `ctx = SYMBOLIC_REWRITER.get_context()` or `get_context('qualified.name')`
- `ctx.cfg`: deployment config
- extra registration fields, if any

Notes:
- the symbolic callback is still an ONNX symbolic function, not a normal model method;
- backend-specific symbolics should be registered separately instead of branching on the backend inside one symbolic whenever possible;
- do not assume a generic `ctx.origin_func` contract for PyTorch built-in symbolics.

## Backend-specific registration rules

- Register a default rewrite first when the same behavior should work broadly.
- Add a backend-specific rewrite when the node structure or algorithm must vary.
- Keep the default rewrite backend-neutral and let backend-specific registrations override it.
- For symbolic rewrites that differ by backend, register one default symbolic plus one backend-specific symbolic and test both.

## Recovery expectations

### Function rewrites
- Entering `RewriterContext` swaps the target function temporarily.
- Exiting the context restores the original function.
- Missing import paths are skipped with a warning, not a crash.
- If the rewrite path is wrong or the checker blocks it, the original function should remain unchanged.

### Module rewrites
- `patch_model` mutates the model tree by replacing matching modules.
- The replacement is persistent for that model instance; it is not automatically reverted.
- Wrapper constructors receive the original module and deployment config first, then only the kwargs they actually accept.

### Symbolic rewrites
- Entering `RewriterContext` registers the symbolic override for the selected backend/IR.
- Exiting the context unregisters it and restores the previous symbolic.
- For custom autograd functions, the original symbolic should be recovered after context exit.
- For PyTorch built-ins, verify the ONNX node domain/op_type rather than assuming a Python-level callable fallback.

## What to test

- Backend-neutral default path works outside the rewrite context.
- Backend-specific path is selected only for the matching backend.
- Context access returns the expected `cfg` and original callable when available.
- The rewritten output or ONNX node changes only in the intended location.
- Export still succeeds after the rewrite context exits.

## Practical guidance

- Import the module that contains the decorators before exporting.
- Put the rewrite in the codebase package that owns the target model family when possible.
- Prefer tiny wrapper functions around the original callable for backend-specific variants.
- If a rewrite depends on `get_context('name')`, keep the string stable and aligned with the registered target path.
