---
name: cortex-m
description: "Develop, export, build, and test ExecuTorch Cortex-M/CMSIS-NN
  workflows with PT2E quantization, graph rewrites, dialect tests, and Arm
  toolchain prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# cortex-m

Use this sub-skill for ExecuTorch Cortex-M, CMSIS-NN, Arm MCU, Corstone/FVP, bare-metal, or Cortex-M quantizer/pass-manager tasks.

## What This Owns

- PT2E quantization with `CortexMQuantizer`.
- Graph rewrite flow using `CortexMPassManager` and Cortex-M custom ops.
- Distinguishing pure Python/dialect graph tests from implementation tests that require Arm tools/FVP.
- Bare-metal runner planning and troubleshooting.

## Fast Path

1. Decide whether the user is asking for graph/export correctness or hardware implementation correctness.
2. For graph/export, use [API reference](references/api-reference.md) and plan dialect tests first.
3. For implementation, confirm Arm toolchain/FVP and any license/EULA prerequisites before running commands.
4. Use the planner:

```bash
python scripts/plan_cortex_m_test.py --mode dialect
python scripts/plan_cortex_m_test.py --mode implementation --model conv2d
```

## Cross-Links

- Generic source build issues: `../setup-build/SKILL.md`.
- Backend choice and Arm Ethos-U/VGF alternatives: `../backend-selection/SKILL.md`.
- Export runtime sequence outside Cortex-M-specific passes: `../export-runtime/SKILL.md`.

