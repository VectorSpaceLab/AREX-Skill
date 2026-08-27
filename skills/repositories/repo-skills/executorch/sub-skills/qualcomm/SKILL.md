---
name: qualcomm
description: "Build, export, test, and debug ExecuTorch Qualcomm QNN backend
  workflows, including QNN SDK setup, compile specs, model enablement,
  Buck/CMake parity, and intermediate-output accuracy triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# qualcomm

Use this sub-skill when the user mentions Qualcomm, QNN, AI Engine Direct, HTP, Hexagon, QNN SDK, Qualcomm Android SoCs, QNN delegate tests, QNN accuracy divergence, or QNN Buck/CMake parity.

## First Route

- Build or SDK setup: read [Qualcomm workflows](references/qualcomm-workflows.md#build-and-environment).
- Export/lowering/quantization: read [Qualcomm workflows](references/qualcomm-workflows.md#export-lowering-and-quantization).
- Device/x86 tests: read [Qualcomm workflows](references/qualcomm-workflows.md#testing).
- Buck-vs-CMake CI failures: read [Buck/CMake parity](references/buck-cmake-parity.md).
- Per-layer accuracy divergence or intermediate outputs: read [Troubleshooting](references/troubleshooting.md#intermediate-output-debugging).

## Hard Prerequisites

QNN workflows require SDK/toolchain state that a generic CPU environment cannot prove. Confirm `QNN_SDK_ROOT`, Android NDK path, target SoC model, device serial/host if running on device, and build directory before issuing run commands.

## Bundled Planner

Generate a safe command plan without touching SDKs or devices:

```bash
python scripts/plan_qnn_command.py --soc SM8750 --build-dir build-android --artifact-dir /tmp/qnn-artifacts --device SERIAL
python scripts/plan_qnn_command.py --soc SM8750 --x86 --compile-only
```

The planner prints command templates and required environment variables; it does not build, install, push to a device, or download SDKs.

## Cross-Links

- Use `../llm-workflows/SKILL.md` for Llama/LLM model-asset planning before QNN backend execution.
- Use `../profiling-debugging/SKILL.md` for generic ETDump/Inspector work; return here for QNN-specific intermediate-output/debugger workflows.
- Use `../setup-build/SKILL.md` for generic CMake/Python environment failures.

