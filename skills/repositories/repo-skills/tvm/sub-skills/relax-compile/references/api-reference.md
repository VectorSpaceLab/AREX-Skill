# Relax API Reference Notes

## Verified compile signature

```python
tvm.compile(
    mod: tvm.tirx.function.PrimFunc | tvm.ir.module.IRModule,
    target: tvm.target.Target | None = None,
    *,
    relax_pipeline: tvm.ir.transform.Pass | callable | str | None = "default",
    tir_pipeline: tvm.ir.transform.Pass | callable | str | None = "default",
) -> tvm.runtime.executable.Executable
```

The entry point automatically routes IRModules containing Relax or TIR and also
accepts TIRx PrimFuncs. For Relax workflows, the return value is used with
`relax.VirtualMachine` or exported as a deployable runtime artifact.

## Related API families

- `tvm.IRModule`: container for Relax functions, TensorIR/TIRx functions, and
  metadata. Inspect `mod.get_global_vars()` and `mod["main"]` before applying a
  pass to an unknown module.
- `tvm.relax.frontend.nn`: Python-first way to define small Relax modules. It is
  useful for smoke tests because it avoids external model files.
- `tvm.relax.frontend.torch.from_exported_program`: PyTorch import path when the
  environment has `torch` and a `torch.export` program.
- `tvm.script.ir` and `tvm.script.relax`: TVMScript route for compact compiler
  repros.
- `tvm.relax.transform`: Relax pass namespace for explicit pass sequences.
- `tvm.relax.get_pipeline(name)`: named pipeline lookup such as `"zero"`.
- `tvm.relax.VirtualMachine`: executes a compiled Relax executable on a TVM
  device such as `tvm.cpu()`.

## Pipeline and target rules

- `target="llvm"` is the default CPU validation target when LLVM is enabled.
- A CUDA target requires both compile-time CUDA support and a runtime device for
  execution. Do not infer CUDA readiness from a visible GPU alone.
- `relax_pipeline` controls high-level Relax lowering and graph transformations.
- `tir_pipeline` controls lower-level TIR/TIRx lowering. Use
  `tir_pipeline="tirx"` for explicit TIRx flows, not ordinary Relax-only smoke
  checks.
- Passing `None` for a pipeline is an advanced choice and can expose raw IR to a
  later stage; use only when the user is debugging pass boundaries.

## Minimal inspection pattern

```python
print(mod.get_global_vars())
print(mod["main"])
mod = tvm.relax.get_pipeline("zero")(mod)
ex = tvm.compile(mod, target="llvm")
vm = tvm.relax.VirtualMachine(ex, tvm.cpu())
```

If any line fails, stop and classify the failure before adding model import,
custom codegen, export/load, or RPC.
