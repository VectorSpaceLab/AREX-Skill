---
name: runtime-and-ops
description: "Diagnose and prepare OpenPCDet runtime environments, CUDA
  extensions, spconv/cumm variants, and import readiness."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OpenPCDet Runtime and Ops

Use this sub-skill when OpenPCDet installation, native extension build, CUDA/spconv compatibility, import readiness, or optional visualization dependencies are relevant.

## Fast route

1. Read `references/runtime-build-guide.md` for the supported runtime stack and known build pitfalls.
2. Run the root helper `../../scripts/inspect_openpcdet_runtime.py` against the target environment or checkout.
3. If compiled ops fail, use `references/native-ops-troubleshooting.md` before running train/test/demo.
4. If the task is dataset, command, inference, or model-specific after the environment is healthy, return to the root skill and route to the corresponding sub-skill.

## Required runtime claims

- Full OpenPCDet train/eval/demo workflows require CUDA-capable PyTorch and compiled OpenPCDet CUDA extension modules.
- spconv/cumm must match the CUDA variant used by PyTorch; CPU-only sparse-conv checks are not a substitute.
- Dataset import can be affected by optional dataset dependencies; Argo2 uses kornia/av2 and was sensitive to kornia version in the construction environment.

## Verification hooks

- Safe import probe: `../../scripts/inspect_openpcdet_runtime.py --require-cuda-ops`.
- Config-only sanity probe: `../../scripts/summarize_openpcdet_config.py --cfg <config.yaml>`.
- Native examples/training should run only after the runtime probe, config summary, and dataset-layout checks pass.
