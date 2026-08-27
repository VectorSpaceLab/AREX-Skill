---
name: mmdeploy
description: "Route MMDeploy model deployment, backend setup, SDK runtime,
  extensibility, and validation workflows for OpenMMLab/PyTorch models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDeploy repo skill

Use this repo skill when a task is about deploying PyTorch/OpenMMLab computer-vision models with MMDeploy: converting checkpoints to backend artifacts, preparing or diagnosing inference backends, using SDK model directories, extending export behavior, or validating/profiling exported models.

Read [repo provenance](references/repo-provenance.md) before relying on version-sensitive behavior or refreshing this skill. Read [root troubleshooting](references/troubleshooting.md) for cross-cutting install/import/version problems before entering a workflow-specific troubleshooting page.

## Minimal public setup

Install MMDeploy in an environment that matches the target OpenMMLab codebase and selected backend. Do not install every optional backend by default.

```bash
python -m pip install -r requirements/runtime.txt -r requirements/optional.txt
python -m pip install -r requirements/build.txt
python -m pip install . --no-build-isolation
python - <<'PY'
import mmdeploy
from mmdeploy.backend.base import get_backend_manager
print('mmdeploy', mmdeploy.__version__)
print('torchscript backend available:', get_backend_manager('torchscript').is_available())
PY
```

Backend-specific packages, vendor toolkits, custom ops, SDK runtime libraries, and hardware drivers are selected per route; a CPU import is not proof that TensorRT, RKNN, Ascend, SNPE, VACC, or SDK runtime execution works.

## Route map

| User intent | Load this route | First files to read |
| --- | --- | --- |
| Convert a model/checkpoint to ONNX, TorchScript, TensorRT, NCNN, OpenVINO, SDK metadata, or another backend artifact | [conversion](sub-skills/conversion/SKILL.md) | `conversion` [workflows](sub-skills/conversion/references/workflows.md), [configuration](sub-skills/conversion/references/configuration.md), bundled `deploy.py` |
| Choose, install, check, or troubleshoot backend packages, converter tools, custom-op libraries, or hardware/toolkit readiness | [backends](sub-skills/backends/SKILL.md) | `backends` [backend matrix](sub-skills/backends/references/backend-matrix.md), [custom ops](sub-skills/backends/references/custom-ops.md), bundled `check_env.py` |
| Run an SDK model directory with `mmdeploy_runtime`, inspect SDK JSON metadata, use C/C++/Java/C# runtime patterns, or analyze SDK profiler output | [sdk](sub-skills/sdk/SKILL.md) | `sdk` [SDK workflows](sub-skills/sdk/references/sdk-workflows.md), [model directory](sub-skills/sdk/references/model-directory.md), bundled `sdk_analyze.py` |
| Modify MMDeploy internals: rewriters, symbolic overrides, backend/codebase/task support, custom ops, partition marks, or developer tests | [extensibility](sub-skills/extensibility/SKILL.md) | `extensibility` [rewriters](sub-skills/extensibility/references/rewriters.md), [backend/codebase support](sub-skills/extensibility/references/backend-and-codebase-support.md), [testing](sub-skills/extensibility/references/testing.md) |
| Evaluate an exported model, profile latency, run regression matrices, or generate supported backend/model tables | [validation](sub-skills/validation/SKILL.md) | `validation` [evaluation](sub-skills/validation/references/evaluation.md), [profiling](sub-skills/validation/references/profiling.md), [regression](sub-skills/validation/references/regression.md) |

## Operating sequence

1. Identify the user's concrete artifact and goal: source checkpoint/config, deployment config, backend target, SDK model directory, backend file set, profiler report, or extension point.
2. Route to exactly one owning sub-skill first. Use sibling sub-skills only at explicit handoff boundaries, such as conversion failing due to missing TensorRT, or SDK runtime failing because a backend library is absent.
3. Prefer bundled helpers in the selected sub-skill over source-repo tools: future agents should run `sub-skills/<id>/scripts/...`, not tools from an original checkout.
4. Keep backend claims scoped to the installed runtime. Optional backend guidance is evidence-backed, but actual runtime success requires the matching backend package/toolkit/hardware.
5. For validation or regression, avoid full matrices, downloads, or accelerator runs unless the user explicitly asks and the environment is ready.

## Common handoffs

- Conversion produced `deploy.json`, `pipeline.json`, and `detail.json`: continue with [sdk](sub-skills/sdk/SKILL.md) for runtime use.
- Conversion exported IR but backend conversion failed: continue with [backends](sub-skills/backends/SKILL.md) using the failing `backend_config.type` and error message.
- A backend model exists and the user asks for accuracy or speed: continue with [validation](sub-skills/validation/SKILL.md), not SDK runtime guidance.
- A model cannot export because a PyTorch/MMCV op is unsupported or partition marks are missing: continue with [extensibility](sub-skills/extensibility/SKILL.md).
- A user asks for general OpenMMLab model training or dataset preparation before deployment: use the relevant upstream codebase skill/documentation; this skill starts at MMDeploy deployment and validation workflows.

## Verification status

The generated skill was built for MMDeploy 1.3.1 source evidence. The production environment verified core package importability, API inspection, and CPU TorchScript backend-manager availability. ONNXRuntime, TensorRT, NCNN, OpenVINO, PPLNN, RKNN, Ascend, CoreML, TVM, VACC, SNPE, and `mmdeploy_runtime` SDK execution are optional/document-backed routes unless the user's current environment verifies them.
