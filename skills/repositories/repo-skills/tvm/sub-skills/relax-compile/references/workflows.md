# Relax Workflow Playbook

## Tiny CPU compile loop

Use this when the user needs a deterministic sanity check before a larger model
or custom pass:

1. Import `tvm`, `tvm.relax`, and `tvm.script.relax`.
2. Create a small `IRModule` with one `@R.function` or a tiny Relax frontend
   module.
3. Optionally run `relax.get_pipeline("zero")` to legalize and fuse simple ops.
4. Compile with `tvm.compile(mod, target="llvm")`.
5. Create `relax.VirtualMachine(executable, tvm.cpu())` and call the exported
   function with small tensors.

This proves the Python package, compiler library, Relax pass stack, LLVM target,
and VM runtime cooperate. It does not prove CUDA, frontend import packages,
external models, or RPC.

## Create or import an IRModule

| Source | Use when | Risk controls |
|---|---|---|
| Relax NN frontend | The model is small or can be written directly | Keep dimensions tiny for smoke checks; detach or pass parameters explicitly |
| TVMScript Relax | The task is compiler debugging, pass development, or minimal repro construction | Prefer one function and simple tensor shapes; show the module before compiling |
| PyTorch export | The user has a PyTorch model and example inputs | Require `torch`, use `torch.export`, and avoid downloading weights in the first pass |
| ONNX/frontend import | The user already has a local model artifact | Verify optional dependency and model file availability; keep batch/shape assumptions explicit |
| Existing IRModule | A previous pass or tool already produced TVM IR | Print global vars and function types before applying more transforms |

## Optimization pipeline choices

- `relax.get_pipeline("zero")` is useful for tutorial-level CPU validation. It
  includes fundamental legalization and graph/TIR fusion passes.
- `relax_pipeline="default"` in `tvm.compile` delegates to TVM's default Relax
  lowering for the current checkout/release.
- Pass objects and callables are appropriate when the user is developing a
  specific transform. Keep the custom pass isolated and print the IR before and
  after it.
- GPU scheduling or dlight rules belong to the S-TIR route after Relax has
  produced suitable low-level functions.

## Export and load executable

After compilation:

```python
ex = tvm.compile(mod, target="llvm")
ex.export_library("model.tar")
loaded = tvm.runtime.load_module("model.tar")
vm = tvm.relax.VirtualMachine(loaded, tvm.cpu())
```

Use a temporary work directory for smoke tests and a caller-approved artifact
path for user outputs. If export/load is the failing area, distinguish:

- compile failure before an artifact exists,
- filesystem/path failure while exporting,
- missing dependent shared library while loading,
- VM entry-name or parameter mismatch while running.

## Custom codegen boundaries

Bring-your-own-codegen and mixed Python/TVM flows often combine Relax graph IR,
TIR functions, runtime modules, and external compiler/runtime contracts. For a
small repro:

1. Keep one custom-marked function or pattern.
2. Show the IR before and after the partition/codegen pass.
3. Confirm the target and runtime module export format.
4. Run a CPU-only fallback or pure Relax compile before adding external codegen.

## Large model and LLM flows

LLM examples can require weights, tokenizer assets, GPUs, vendor libraries, and
long compile/tuning times. Start with import/pipeline inspection and a tiny
representative IRModule. Only expand to full weights or GPU execution after the
user confirms runtime and budget.
