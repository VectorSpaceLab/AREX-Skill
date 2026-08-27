---
name: optimum
description: "Use Hugging Face Optimum for model export routing, accelerated
  pipeline dispatch, Torch FX graph workflows, GPTQ quantization planning, and
  utility/config support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Optimum repo skill

Use this skill when the task involves Hugging Face Optimum: `optimum-cli`, model export task mapping, accelerated pipeline dispatch to partner packages, Torch FX graph transformations, GPTQ quantization planning, dummy inputs, normalized configs, preprocessing processors, or Optimum base save/load support.

Optimum is a namespace-style extension package around Transformers/Diffusers/TIMM/Sentence-Transformers optimization workflows. This base repository supplies shared CLI routing, exporter/task utilities, FX graph utilities, GPTQ integration code, and cross-package support utilities; many hardware-specific implementations live in partner packages such as `optimum-onnx`, `optimum-intel`, `optimum-habana`, `optimum-furiosa`, and related distributions.

## Start here

1. Confirm the installed package and optional dependency surface before deeper work. Prefer the bundled checker over ad-hoc inline Python so the diagnosis matches this skill's optional-dependency policy:

   ```bash
   python scripts/check_optimum_install.py
   python scripts/check_optimum_install.py --json
   ```

2. If the task names a CLI command, exporter backend, task mapping, or accelerated pipeline, read [`sub-skills/exporters-and-cli/SKILL.md`](sub-skills/exporters-and-cli/SKILL.md).
3. If the task is about Torch FX graph rewrites, reversible transformations, `compose`, or optional tensor parallelism, read [`sub-skills/fx-graph-workflows/SKILL.md`](sub-skills/fx-graph-workflows/SKILL.md).
4. If the task is about GPTQ, `GPTQQuantizer`, GPT-QModel dependency checks, saving/loading quantized weights, or custom CausalLM quantization planning, read [`sub-skills/gptq-quantization/SKILL.md`](sub-skills/gptq-quantization/SKILL.md).
5. If the task is about dummy input generators, normalized configs, task processors, run configs, `BaseConfig`, `OptimizedModel`, or support utilities, read [`sub-skills/utilities-and-configs/SKILL.md`](sub-skills/utilities-and-configs/SKILL.md).
6. For cross-cutting installation, import, partner package, or backend failures, read [`references/troubleshooting.md`](references/troubleshooting.md).
7. Before assuming this skill matches a different checkout, read [`references/repo-provenance.md`](references/repo-provenance.md).

## Installation and minimal check

Base install:

```bash
python -m pip install optimum
python - <<'PY'
from importlib.metadata import version
import optimum.version as ov
print(version("optimum"), ov.__version__)
PY
optimum-cli --help
optimum-cli env
```

Common optional surfaces:

- ONNX export / ONNX Runtime accelerated pipelines: install the corresponding `optimum-onnx` or `optimum[onnx]` / `optimum[onnxruntime]` distribution path documented for the target workflow.
- OpenVINO accelerated pipelines: install the `optimum-intel[openvino]` path for OpenVINO-backed model classes and pipeline dispatch.
- GPTQ quantization: install `gptqmodel>=7.0.0` and usually `accelerate`, then verify GPU/backend readiness before running quantization.
- Preprocessing task processors: some imports require `torchvision`, Pillow, and/or `datasets` even when the base package import succeeds.
- Tensor parallelism: treat as an advanced CUDA/distributed workflow; match the repository's tested Python/torch stack before relying on it.

## Route map

| User intent | Read | Safe bundled check |
| --- | --- | --- |
| Diagnose `optimum-cli`, `optimum-cli env`, missing `export onnx`, partner CLI registration | `sub-skills/exporters-and-cli/` | `python sub-skills/exporters-and-cli/scripts/probe_optimum_cli.py --run-env` |
| Query task names, synonyms, exporter backend config constructors, or custom backend registration | `sub-skills/exporters-and-cli/` | `python sub-skills/exporters-and-cli/scripts/tasks_manager_probe.py --json` |
| Use `optimum.pipelines.pipeline(..., accelerator="ort"/"ov")` | `sub-skills/exporters-and-cli/` | `python scripts/check_optimum_install.py --json` plus partner-specific imports |
| Apply or write Torch FX transformations | `sub-skills/fx-graph-workflows/` | `python sub-skills/fx-graph-workflows/scripts/fx_transform_smoke.py --check-compose` |
| Plan tensor parallelism | `sub-skills/fx-graph-workflows/` | No default native run; first verify Python, CUDA, NCCL, `torch.compile`, and distributed process groups |
| Plan GPTQ quantization or load saved GPTQ weights | `sub-skills/gptq-quantization/` | `python sub-skills/gptq-quantization/scripts/gptq_availability_probe.py --json` |
| Generate dummy tensors or standardize config fields | `sub-skills/utilities-and-configs/` | `python sub-skills/utilities-and-configs/scripts/utils_smoke.py` |
| Diagnose utility/preprocessing/config issues | `sub-skills/utilities-and-configs/` and root troubleshooting | `python sub-skills/utilities-and-configs/scripts/utils_smoke.py --check-task-processors` |

## Boundaries and cautions

- Do not assume base `optimum` contains every hardware backend. Missing partner subcommands or model classes are often install/routing issues, not source bugs.
- Do not run Hub model downloads, native export/pipeline tests, full GPTQ quantization, tensor-parallel distributed tests, training, or dataset downloads unless the user explicitly authorizes network/hardware/time requirements.
- A CPU import proves only base package availability. It does not prove ONNX Runtime, OpenVINO, GPTQ kernels, CUDA tensor parallelism, or partner package execution.
- Use bundled scripts for safe local diagnostics before inventing one-off probes. They are designed to run from arbitrary current directories and do not depend on the original repository checkout.
- Keep task-specific details in the nearest sub-skill. Root guidance should only route, install, and triage.
