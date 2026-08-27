---
name: setup-and-backends
description: "Install, import, backend selection, runtime smoke checks, and
  setup troubleshooting for Flash Linear Attention."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Setup and Backends

Use this sub-skill when the task is about installing Flash Linear Attention (FLA), checking whether `fla` imports, choosing a backend extra, diagnosing backend wheel mismatches, or deciding whether optional runtime backends are active.

## Route here for

- Installing `flash-linear-attention` or `fla-core` from PyPI, source, editable checkouts, or prebuilt wheels.
- Choosing backend extras: `cuda`, `rocm`, `xpu`, `npu`, or `cpu`.
- Explaining why a bare install lacks `torch` / `triton`, or why ROCm / XPU / NPU need backend-specific wheel indexes.
- Running safe import/runtime checks before attempting operators, models, training, or benchmarks.
- Troubleshooting `torch.cuda.is_available()`, wrong backend wheels, optional backend gates, and FLA environment variables.

## Do not use this sub-skill for

- Deep operator correctness, numerical tolerances, or dispatch verifier changes. Use the ops/kernel sub-skill.
- Layer/model construction recipes, checkpoint compatibility, or Hugging Face model APIs. Use the layers/models sub-skill.
- Benchmark methodology, optimization loops, Nsight profiling, or performance claims. Use the benchmarking/optimization sub-skill.

## Fast workflow

1. Pick exactly one backend family for the user's machine and package policy. Use `references/install-and-backends.md` for the install matrix and package split notes.
2. Install `flash-linear-attention[...]` for layer/model users, or `fla-core[...]` only when the task needs kernels/modules without `fla.layers` or `fla.models`.
3. Run the bundled safe checker before invoking native tests or examples:

   ```bash
   python scripts/check_fla_runtime.py --show-env-vars
   python scripts/check_fla_runtime.py --require-cuda
   ```

   Use `--require-cuda` only when the chosen backend is CUDA/NVIDIA and a CUDA device is expected.
4. If imports, CUDA allocation, or optional backend activation fail, use `references/troubleshooting.md` before changing code.

## Key facts to preserve

- The import package is `fla`; the distribution packages are split into `fla-core` and `flash-linear-attention`.
- `torch` and `triton` are intentionally not base dependencies. A bare `pip install flash-linear-attention` is not a usable runtime install; choose a backend extra.
- ROCm, XPU, and CPU installs should source `torch` from the matching PyTorch wheel index first so pip does not mix incompatible backend wheels.
- Optional backends are selected by environment gates and package availability. Set environment variables before starting Python.
- CPU import checks are useful for package visibility, but they do not verify GPU kernels or accelerator-specific behavior.

## Bundled assets

- `references/install-and-backends.md`: package split, install commands, backend extras, environment variables, and smoke-check procedure.
- `references/troubleshooting.md`: symptom-driven install/import/backend failure recovery.
- `scripts/check_fla_runtime.py`: safe argparse helper for imports, versions, public export counts, selected FLA environment variables, and optional tiny CUDA allocation.
