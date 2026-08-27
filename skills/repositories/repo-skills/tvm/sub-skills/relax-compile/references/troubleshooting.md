# Relax Troubleshooting

## Import and frontend issues

**Symptom:** `from tvm import relax` fails.

This is an install/build issue. Run the install-build import probe and confirm
the compiler/runtime libraries match the Python package.

**Symptom:** PyTorch or ONNX import fails.

The Relax core may be fine while the optional frontend dependency is missing or
the model format is unsupported. Verify the frontend package, use a tiny local
model, and postpone downloads or large weights until the import path works.

## Pipeline and pass failures

**Symptom:** A pass fails after model import.

- Print the IRModule before the pass.
- Apply one transform at a time rather than a long pipeline.
- Confirm the IR contains the expected Relax functions and any TIR functions
  needed by the pass.
- If the failure is a schedule or dlight rule, switch to s-tir-tuning.

**Symptom:** `tvm.compile` fails with target or lowering errors.

- Re-run a tiny `llvm` smoke. If that fails, the install/build or compiler
  library is broken.
- Check whether the pipeline emitted backend-specific TIR that requires CUDA,
  tensor cores, or another unavailable backend.
- Separate `relax_pipeline` failures from `tir_pipeline` failures by simplifying
  the arguments.

## Export/load/run failures

**Symptom:** `export_library` fails.

Check the output directory, compiler toolchain for the export format, and
whether the module contains target-specific objects that need additional
packaging support.

**Symptom:** `tvm.runtime.load_module` fails after export.

Inspect dynamic-library dependencies and runtime library search paths. Loading a
compiled artifact can fail even when compilation succeeded if the runtime cannot
find dependent shared libraries.

**Symptom:** `VirtualMachine` runs but entry invocation fails.

Inspect global var names, function attributes, parameter order, tensor dtype,
shape, and whether parameters were detached or kept as explicit inputs.

## Backend claims

A CPU `llvm` Relax run is good evidence for core Relax lowering and VM execution.
It is not evidence for CUDA runtime execution, external codegen, RPC devices, or
large-model performance.
