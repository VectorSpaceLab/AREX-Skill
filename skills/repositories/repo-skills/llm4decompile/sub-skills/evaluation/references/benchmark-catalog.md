# Benchmark Catalog

## HumanEval-Decompile

- **Shape**: 164 C functions per optimization level.
- **Purpose**: re-executability on standard-library-only functions.
- **Typical fields**: `task_id`, `type`, `c_func`, `c_test`, `input_asm_prompt`.

## MBPP-Decompile

- **Shape**: additional benchmark data with similar function-recovery layout.
- **Purpose**: broader function reconstruction and metric comparison.

## Decompile-Bench

- **Shape**: large C/C++ evaluation dataset with benchmarked compilation and execution metrics.
- **Purpose**: compare outputs across optimization levels and languages.
- **Metrics**: executable rate, compile rate, edit similarity.

## Legacy evaluation data

- The repo includes older or less central benchmark artifacts under `legacy-test/`.
- Treat them as historical evidence unless a user explicitly asks for the legacy path.
