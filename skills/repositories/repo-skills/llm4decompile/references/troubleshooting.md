# Troubleshooting

This file collects cross-cutting issues that show up across several LLM4Decompile workflows. Workflow-specific failures live in the nearest sub-skill troubleshooting reference.

## Python and CUDA stack

### `ImportError: ... libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent`
- **Likely cause**: Intel OpenMP / ITT runtime mismatch in the Python environment.
- **What to try**: install or repair the `ittapi` / `intel-openmp` runtime in the target prefix, then retry the `torch` import.
- **Validation**: `python -I -c "import torch; print(torch.__version__, torch.version.cuda)"`

### `CUDA_HOME does not exist` warnings
- **Likely cause**: a package is probing for local CUDA toolkit headers to build optional extensions.
- **What to try**: if the workflow does not need source compilation, ignore the warning; otherwise install a matching CUDA toolkit and compiler stack in the environment.
- **Validation**: rerun the package import and the smallest CUDA smoke check.

### `torch.cuda.is_available() == False` on a GPU host
- **Likely cause**: CPU-only torch, incompatible wheel, missing driver/runtime passthrough, or a broken environment.
- **What to try**: verify the prefix is the intended CUDA environment and that the driver supports the selected torch wheel.

## Ghidra / Java / formatting

### `java: command not found`
- **Likely cause**: Java 17 is missing from the environment.
- **What to try**: install Java 17 before using the Ghidra workflow.
- **Validation**: `java -version`

### `clang-format: command not found`
- **Likely cause**: the normalization helpers cannot format or clean pseudo-code.
- **What to try**: install `clang-format` and rerun the normalization script.
- **Validation**: `clang-format --version`

### Ghidra headless path errors
- **Likely cause**: the `analyzeHeadless` path or postscript path is wrong.
- **What to try**: confirm the Ghidra unzip location and pass the headless binary and `dump_pseudo.py`/postscript as explicit arguments or env vars.

## Decompilation benchmarks

### `gcc` / `g++` / `objdump` missing
- **Likely cause**: the benchmark toolchain is incomplete.
- **What to try**: install the compiler and binutils tools required by the compile-and-execute metrics.
- **Validation**: `gcc --version`, `g++ --version`, `objdump --version`

### Benchmark script cannot locate function bodies
- **Likely cause**: the inferred source does not match the original function body exactly, or the dataset schema is off.
- **What to try**: inspect the generated file, normalize function names if needed, and confirm the `func_name` / `source` / `pseudo` fields match the expected schema.

## External services and credentials

### TGI / `text-generation-launcher` missing
- **Likely cause**: the text-generation-inference server is not installed.
- **What to try**: install the package or choose the vLLM evaluation path instead.

### OpenAI-compatible embedding / judge failures
- **Likely cause**: missing API key, wrong base URL, or unavailable service.
- **What to try**: verify the service endpoint and credentials; prefer the non-API fallback paths when possible.

### Psychec / header inference failures
- **Likely cause**: the generator/solver toolchain is not installed or `stack` is unavailable.
- **What to try**: either install the required toolchain or treat the header-inference path as intentionally unverified.

## When to stop and narrow scope

If a required backend is missing for the chosen workflow, do not silently claim success with a CPU-only environment. Narrow the scope, switch workflows, or accept an explicitly partial draft only when the user has authorized that limitation.
