---
name: backend-selection
description: "Choose and configure ExecuTorch backends/delegates, including CPU,
  mobile, desktop, GPU, and vendor accelerator paths, while preserving hardware
  and SDK prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# backend-selection

Use this sub-skill when the user asks which ExecuTorch backend to target, how to add partitioners or CMake flags, why delegation fell back to CPU, or how backend prerequisites differ across mobile, desktop, embedded, and accelerator targets.

## Route Here For

- XNNPACK mobile/desktop CPU export, fallback, and quantization placement.
- Core ML, MPS/Metal, Vulkan, CUDA/AOTI, OpenVINO, MediaTek, NXP, Samsung Exynos, Cadence, Arm Ethos-U, and Arm VGF high-level setup/export decisions.
- Backend build flags, optional dependencies, SDK/toolchain prerequisites, and native verification expectations.
- Deciding whether an accelerator can be validated on CPU or must be treated as unverified until device/SDK tests run.

## Route Elsewhere

- General install/build commands: `../setup-build/SKILL.md`.
- Export sequence and `.pte`/`.ptd` validation after the backend is chosen: `../export-runtime/SKILL.md`.
- Qualcomm QNN details: `../qualcomm/SKILL.md`.
- Cortex-M/CMSIS-NN details: `../cortex-m/SKILL.md`.
- LLM model-runner choices: `../llm-workflows/SKILL.md`.

## First Decisions

1. Identify target hardware and platform: CPU, Android GPU/NPU, iOS/macOS, NVIDIA GPU, Intel, embedded MCU, or vendor NPU/DSP.
2. Decide whether the backend is required for correctness or optional for performance. Do not treat CPU export as proof of QNN/Core ML/MPS/Vulkan/CUDA behavior.
3. Choose a fallback strategy. XNNPACK/portable CPU fallback is often useful when a GPU/NPU delegate only covers part of a model.
4. Read [backend matrix](references/backend-matrix.md) for prerequisites and [backend export patterns](references/backend-export-patterns.md) for partitioner/build patterns.
5. Use the bundled import checker for Python-side availability only:

```bash
python scripts/check_backend_imports.py --json
```

## Common Patterns

- Start with no delegate or XNNPACK to prove the model exports and runs functionally.
- Add one backend at a time and inspect which graph partitions were delegated.
- For multiple targets, export one `.pte` per backend/target instead of assuming one artifact is optimal everywhere.
- If backend-specific quantization is required, quantize with that backend's quantizer before lowering.

