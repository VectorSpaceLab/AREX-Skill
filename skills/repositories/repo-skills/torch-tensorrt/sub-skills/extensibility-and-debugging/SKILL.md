---
name: extensibility-and-debugging
description: "Use this sub-skill for Torch-TensorRT dryrun analysis, Debugger
  capture/replay, unsupported-op triage, converter/lowering/plugin authoring,
  QDP kernels, and ModelOpt or quantization debugging."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Torch-TensorRT Extensibility and Debugging

Use this sub-skill when the user needs to understand *why* a model did not compile cleanly, how to inspect graph partitioning, or how to extend Torch-TensorRT with custom lowering or kernels.

## Start with the failure mode

| Visible symptom | Likely workstream |
| --- | --- |
| `no converter`, `unsupported op`, or tiny TRT partition | Unsupported-op triage and converter decisions |
| Compile coverage question | `dryrun`, `require_full_compilation`, `torch_executed_ops`, `min_block_size` |
| Need graph/capture artifacts or layer info | `Debugger` and capture/replay |
| Custom op, converter, or lowering implementation | Converter/plugin extension |
| QDP kernel or custom CUDA/PTX kernel | `torch_tensorrt.kernels` |
| Quantization warning or ModelOpt dependency confusion | Quantization support triage |

## Primary references

- `references/debugging.md` for dryrun, debugger, and issue-reproduction workflows.
- `references/operator-coverage.md` for unsupported-op and fallback decisions.
- `references/custom-ops-and-plugins.md` for converter, lowering, and TensorRT plugin paths.
- `references/kernel-api.md` for QDP kernel APIs and safe skeletons.
- `references/troubleshooting.md` for common error interpretations and dependency gaps.
- `scripts/debugger_capture_template.py --help` for a safe capture template.
- `scripts/qdp_kernel_skeleton.py --help` for a non-running kernel skeleton generator/checker.

## Typical debugging workflow

1. Reproduce on the smallest possible model and input.
2. Run a dryrun or debugger capture to see which operators are partitioned to TensorRT and which stay in PyTorch.
3. Decide whether fallback is acceptable.
4. If not, choose among model rewrite, custom converter, or plugin/QDP implementation.
5. Only after the root cause is identified should you revisit runtime optimization or deployment.

## Guardrails

- Do not promise a converter/plugin path without the exact op, schema, input dtype/layout, and target TensorRT version.
- Do not treat ModelOpt or QDP support as universal; version and dependency gates matter.
- Do not use a generic compile smoke as proof that the problematic op is supported.
- Keep debugging artifacts small and self-contained so the user can paste them into an issue or test case.
