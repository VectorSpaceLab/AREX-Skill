---
name: relax-compile
description: "Guides TVM Relax IR construction/import, optimization pipelines,
  tvm.compile, executable export/load, and custom codegen boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Relax Compile Workflows

Use this sub-skill when a task involves high-level TVM Relax IR, model import,
optimization pipelines, `tvm.compile`, VM execution, or deployable executable
artifacts.

## Route

1. Confirm TVM imports and has the target backend required by the task. If not,
   first use [`../install-build/SKILL.md`](../install-build/SKILL.md).
2. Decide how the IRModule is created: Relax NN frontend, TVMScript Relax,
   PyTorch/ONNX frontend import, or an existing IRModule.
3. Apply the smallest needed pipeline or pass sequence. `relax.get_pipeline("zero")`
   is a safe baseline for tutorial-style CPU workflows; larger model and dlight
   flows need backend-specific checks.
4. Compile through `tvm.compile(mod, target, relax_pipeline=..., tir_pipeline=...)`.
5. Run the executable locally with `relax.VirtualMachine` or export/load it for a
   deployment workflow.
6. Use [`references/troubleshooting.md`](references/troubleshooting.md) when the
   failure is about target mismatch, optional frontend dependencies, export/load,
   or pass/codegen boundaries.

## Common decisions

- **Tiny local CPU compile:** create or adapt a small Relax IRModule and target
  `llvm`. Run [`scripts/relax_compile_smoke.py`](scripts/relax_compile_smoke.py)
  before diagnosing a larger model.
- **PyTorch or ONNX import:** require the matching frontend dependency and a
  small example input. Keep model downloads, weights, and external datasets out
  of the first debugging loop.
- **Custom optimization:** keep Relax graph passes and TIR/S-TIR scheduling
  passes separate. Route schedule/meta-schedule decisions to
  [`../s-tir-tuning/SKILL.md`](../s-tir-tuning/SKILL.md).
- **Remote execution:** compile/export locally, then use
  [`../rpc-deployment/SKILL.md`](../rpc-deployment/SKILL.md) for upload/load/run
  and tracker/server details.

## API anchor

The verified top-level compile entry point is:

```python
tvm.compile(
    mod,
    target=None,
    *,
    relax_pipeline="default",
    tir_pipeline="default",
)
```

It accepts a Relax/TIR IRModule or TIRx PrimFunc and returns a runtime
`Executable`. The pipeline arguments accept a named pipeline, pass object, or
callable depending on the workflow.

## Boundaries

- Build/import failures are not Relax failures; route to install-build.
- TIRx PrimFunc authoring and tile primitive lowering use tirx-kernels.
- S-TIR schedule primitives and meta-schedule tuning use s-tir-tuning.
- RPC trackers, servers, proxies, and remote-device triage use rpc-deployment.
