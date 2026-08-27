---
name: executorch
description: "Use ExecuTorch to export PyTorch models to edge runtime artifacts,
  build host/device runtimes, choose delegates, profile/debug execution, and
  operate specialized Qualcomm, Cortex-M, LLM, and binary-size workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ExecuTorch

Use this repo skill when the task involves ExecuTorch, the `executorch` Python package, `.pte` or `.ptd` artifacts, EXIR/export lowering, on-device runtime integration, ExecuTorch backends/delegates, or ExecuTorch build/profiling/debugging workflows.

## Start Here

1. Classify the user's goal before reading deep references:
   - Install, build, configure CMake, cross-compile, or pick tests: `sub-skills/setup-build/SKILL.md`.
   - Export a PyTorch model, create `.pte`/`.ptd`, or validate runtime loading: `sub-skills/export-runtime/SKILL.md`.
   - Choose or configure XNNPACK, Core ML, MPS/Metal, Vulkan, CUDA/AOTI, OpenVINO, MediaTek, NXP, Samsung, Cadence, or Arm VGF backends: `sub-skills/backend-selection/SKILL.md`.
   - Use the Qualcomm QNN backend, QNN SDK, Android device tests, Buck/CMake parity, or QNN intermediate-output debugging: `sub-skills/qualcomm/SKILL.md`.
   - Use Cortex-M/CMSIS-NN, Arm embedded quantization, FVP, or bare-metal tests: `sub-skills/cortex-m/SKILL.md`.
   - Generate or inspect ETRecord/ETDump, use Inspector, visualize graphs, or triage accuracy/performance: `sub-skills/profiling-debugging/SKILL.md`.
   - Export/run LLMs, plan `export_llm` or Optimum ExecuTorch commands, or build LLM runners: `sub-skills/llm-workflows/SKILL.md`.
   - Measure/reduce binary size or compare stripped binaries: `sub-skills/binary-size/SKILL.md`.
2. For mixed workflows, route through the narrowest owner first, then cross-link. Example: a dynamic-shape CV model with XNNPACK and ETRecord starts in `export-runtime`, reads `backend-selection` for XNNPACK, then reads `profiling-debugging` for ETRecord/Inspector.
3. Treat hardware/vendor SDK/device workflows as conditional. A CPU import or export smoke proves Python/export plumbing, not QNN/Core ML/MPS/Vulkan/CUDA/Arm implementation behavior.

## Package and Runtime Baseline

- Public package name: `executorch`; import namespace: `executorch`.
- Python support from package metadata: Python 3.10 through 3.14.
- The direct export path is `torch.export.export(...)` followed by `executorch.exir.to_edge_transform_and_lower(...)` and `.to_executorch()`.
- The higher-level experimental export surface is `executorch.export.export(...)` with `ExportRecipe`, `LoweringRecipe`, and `QuantizationRecipe`.
- Python runtime loading with `executorch.runtime.Runtime` and `executorch.extension.pybindings.portable_lib` requires a build or wheel that includes the native pybindings. If imports fail with missing `_portable_lib`, route to `setup-build` before debugging model logic.

## Minimal Checks

Use these checks only in an environment where ExecuTorch is installed or a source checkout is intentionally on `PYTHONPATH`:

```bash
python - <<'PY'
from executorch.exir import to_edge_transform_and_lower
print("EXIR import OK", callable(to_edge_transform_and_lower))
PY
```

For a more complete read-only diagnostic, run the bundled helper:

```bash
python scripts/check_import_surface.py
```

The helper reports import surfaces and optional backend modules without installing packages, downloading models, or building targets.

## Shared References

- Read `references/package-overview.md` for source/package layout, public artifacts, and terminology.
- Read `references/troubleshooting.md` for cross-cutting installation, import, backend, runtime, and source-build failures.
- Read `references/repo-provenance.md` before deciding whether this skill is current for another ExecuTorch checkout.

