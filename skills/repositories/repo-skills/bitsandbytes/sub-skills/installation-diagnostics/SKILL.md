---
name: installation-diagnostics
description: "Diagnose and fix bitsandbytes installation, import, backend
  compatibility, native-library loading, and source-build issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Installation Diagnostics

Use this sub-skill when a task involves installing `bitsandbytes`, debugging `import bitsandbytes`, checking CPU/CUDA/ROCm/XPU/HPU/MPS support, interpreting `python -m bitsandbytes`, choosing a source build, resolving native library load failures, or preparing sanitized environment details for an issue.

## Route Here When

- Installation or import fails, or native methods fail after import.
- A user asks whether their Python, PyTorch, CUDA, ROCm, XPU, Gaudi, MPS, CPU, OS, or wheel combination is supported.
- Errors mention `libbitsandbytes_cpu`, `libbitsandbytes_cuda*`, `libbitsandbytes_rocm*`, `libcudart`, `amdhip64`, `fatbinwrap`, `no kernel image`, `Configured CUDA binary not found`, or CPU-only native methods.
- The environment uses `BNB_CUDA_VERSION` or `BNB_ROCM_VERSION`, or the selected binary does not match PyTorch's reported accelerator runtime.
- The user is in CPU-only CI and needs import/signature/package inspection without GPU kernels.
- The user needs source-build decisions for CUDA, ROCm, CPU, XPU, MPS, Jetson/aarch64, Windows, or macOS.

## Do Not Handle Here

- Hugging Face `BitsAndBytesConfig`, QLoRA, PEFT, Accelerate, Diffusers, or model-loading choices: route to `../transformers-integrations/SKILL.md`.
- Direct `bitsandbytes.nn`, `bitsandbytes.functional`, quantized layer, state dict, or primitive API usage: route to `../quantized-modules-functions/SKILL.md`.
- Optimizer selection, `GlobalOptimManager`, training-loop integration, or paged optimizer usage: route to `../optimizers-training/SKILL.md`.

## First Response Workflow

1. Ask for the exact command, traceback, OS/architecture, Python version, PyTorch version, and whether the user expects CPU, CUDA, ROCm, XPU, HPU, or MPS.
2. Prefer read-only checks first: `python -m bitsandbytes`, `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.version.hip, torch.cuda.is_available())"`, and `python scripts/backend-report.py --json` from this sub-skill when available.
3. Compare PyTorch's reported runtime (`torch.version.cuda` or `torch.version.hip`) plus any `BNB_*_VERSION` override against the bundled `libbitsandbytes_*` filenames.
4. Separate import/package inspection from accelerator execution: CPU-only environments can validate imports and signatures but cannot prove CUDA/ROCm/XPU kernels work.
5. Use `references/backend-compatibility.md` for support matrices and expected binaries, `references/source-builds.md` for safe build choices, and `references/troubleshooting.md` for symptom-to-fix guidance.

## Safe Commands

```bash
python -m bitsandbytes
python sub-skills/installation-diagnostics/scripts/backend-report.py --help
python sub-skills/installation-diagnostics/scripts/backend-report.py --json
python -c "import bitsandbytes, torch; print(bitsandbytes.__version__, torch.__version__)"
```

Avoid running GPU optimizer or quantized model smoke tests unless the user confirms accelerator hardware is available and they want kernel execution. Avoid installer scripts that download or mutate CUDA/ROCm; distill their intent into source-build guidance instead.

## Issue Info Checklist

Collect only sanitized details: OS and architecture, Python/PyTorch/bitsandbytes versions, `torch.version.cuda` or `torch.version.hip`, `torch.cuda.is_available()`, visible device names if the user agrees, `BNB_CUDA_VERSION`/`BNB_ROCM_VERSION` values, expected/bundled native library names, the minimal traceback, and whether the install came from a wheel or source build. Do not include access tokens, usernames, full home paths, private project paths, or complete environment dumps.
