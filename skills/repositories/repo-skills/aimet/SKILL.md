---
name: aimet
description: "Route AIMET install, PyTorch/ONNX quantization, GenAILab, model
  access, cluster/Pod, Qualcomm SDK, optimization, export, and repository tasks
  to focused operating guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET repo skill

AIMET (AI Model Efficiency Toolkit) is a toolkit for quantizing, compressing, analyzing, and exporting trained PyTorch and ONNX models, with repository-side GenAILab scorecard tooling and Qualcomm target-deployment guidance. Use this skill when a task names AIMET, `aimet-torch`, `aimet-onnx`, `aimet_torch`, `aimet_onnx`, `QuantizationSimModel`, AIMET encodings, AIMET compression, GenAILab, QNN/QAIRT/AI Hub, or AIMET repository build/test workflows.

This skill is a router. Open the focused sub-skill and bundled references before changing code, adjusting build settings, or running expensive examples.

## Start here

1. **Identify the surface.** Decide whether the task is about installation/build, PyTorch quantization, ONNX quantization, GenAILab LLM/VLM evaluation, model/download credentials, cluster/Pod execution, or Qualcomm target deployment.
2. **Verify the environment before debugging AIMET.** For installed-package tasks, run `python scripts/quick_smoke.py --framework both` from this skill directory or copy it into a clean working area. For GenAILab configs, run `python scripts/genai_config_preflight.py <config.yaml> --framework <torch|onnx|both> --print-command` before long runs.
3. **Do not assume CUDA is required.** Core PyTorch and ONNX QuantSim workflows are CPU-valid; CUDA is required only for GPU provider checks, CUDA-marked tests, source CUDA builds, GenAILab runs whose model size needs GPU memory, or user workloads that cannot run on CPU.
4. **Treat examples as evidence, not mandatory runtime.** AIMET examples often expect ImageNet-scale data, Hugging Face models, cluster credentials, or target SDKs. Use the distilled workflows and preflight scripts here unless the user has explicitly supplied those assets.

## Route map

| User task | Read first | Why |
| --- | --- | --- |
| Install `aimet-torch`/`aimet-onnx`, repair dependency conflicts, choose CPU vs CUDA, build from source, or run focused repo checks | [install-and-build](sub-skills/install-and-build/SKILL.md) | Captures package names, build flags, dependency variants, and safe smoke checks. |
| Quantize a PyTorch model, prepare a model for AIMET, run calibration, use QAT, or export a Torch QuantSim model | [torch-quantization](sub-skills/torch-quantization/SKILL.md) | Covers `aimet_torch` workflows, model preparation, BatchNorm folding, QuantSim, encodings, and Torch export. |
| Quantize an ONNX model, choose ONNX Runtime providers, compute/load encodings, export QDQ, or run ONNX PTQ utilities such as SeqMSE/AdaRound | [onnx-quantization](sub-skills/onnx-quantization/SKILL.md) | Covers `aimet_onnx` graph/session workflows, precision controls, PTQ utilities, and provider decisions. |
| Diagnose accuracy loss, use QuantAnalyzer/visualization, mixed precision, compression, deployment artifacts, or on-target inference handoff | [optimization-analysis-deployment](sub-skills/optimization-analysis-deployment/SKILL.md) | Covers cross-framework optimization, compression, debugging workflow, export artifacts, and target-runtime boundaries. |
| Configure or run AIMET GenAILab LLM/VLM scorecards, recipe chains, local Torch/ONNX GenAI tests, online scorecards, exports, caches, or summaries | [genai-lab](sub-skills/genai-lab/SKILL.md) | Covers `python -m GenAILab`, YAML contracts, framework choice, cache/export/result directories, and safe preflight. |
| Use Hugging Face tokens, gated/private models, GitHub Actions dispatch/download, AWS/S3 checkpoint artifacts, SAML login, or metric-version-aware result comparisons | [model-access-and-credentialed-evaluation](sub-skills/model-access-and-credentialed-evaluation/SKILL.md) | Covers model downloads, credential boundaries, artifact download, cache planning, and comparability rules. |
| Launch or reuse Argo/Kubernetes pods, sync AIMET to `/scratch`, run GenAILab/source builds on remote GPU pods, list workflows, or stop pods | [cluster-pod-workflows](sub-skills/cluster-pod-workflows/SKILL.md) | Covers resource requests, launch/sync/exec/list/stop helper commands, and remote-state safety. |
| Send AIMET ONNX/encoding exports to Qualcomm AI Hub, QAIRT, QNN, HTP, DLC conversion, profiling, inference, or SDK command generation | [qualcomm-sdk-deployment](sub-skills/qualcomm-sdk-deployment/SKILL.md) | Covers export validation, AI Hub compile/profile/inference, local QAIRT/QNN command generation, and target-runtime boundaries. |

## Bundled references

- [references/install-and-build.md](references/install-and-build.md) summarizes install commands, source-build variants, dependency files, and safe repo-maintenance test selection.
- [references/api-overview.md](references/api-overview.md) records verified public entry points and signatures for the main `aimet_torch`, `aimet_onnx`, and compression APIs.
- [references/workflows.md](references/workflows.md) distills the main Torch, ONNX, compression, analysis, and export workflows into short recipes.
- [references/backend-compatibility.md](references/backend-compatibility.md) records CPU/CUDA/provider expectations and which backend checks are evidence-bearing.
- [references/troubleshooting.md](references/troubleshooting.md) maps common symptoms to likely causes and recovery steps.
- [references/genai-lab.md](references/genai-lab.md) records self-contained GenAILab local/online/config/cache/export workflows.
- [references/model-access-and-credentialed-evaluation.md](references/model-access-and-credentialed-evaluation.md) records Hugging Face, GitHub Actions, AWS/S3, SAML, cache, and metric-comparability workflows.
- [references/cluster-pod-workflows.md](references/cluster-pod-workflows.md) records Argo/Kubernetes launch, sync, exec, list, and stop workflows.
- [references/qualcomm-sdk-workflows.md](references/qualcomm-sdk-workflows.md) records Qualcomm AI Hub and local QAIRT/QNN deployment sequences.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and included/excluded evidence paths used to create this skill.

## Bundled scripts

- [scripts/quick_smoke.py](scripts/quick_smoke.py) performs a tiny installed-package import plus PyTorch and ONNX QuantSim calibration smoke check.
- [scripts/build_from_source.sh](scripts/build_from_source.sh) is a safe adapter for source builds in a user-created environment; it checks build prerequisites, applies `CMAKE_ARGS`, and can run the bundled smoke check after install.
- [scripts/inspect_export.py](scripts/inspect_export.py) validates exported ONNX and AIMET encodings artifacts before handing them to target-runtime tooling.
- [scripts/genai_config_preflight.py](scripts/genai_config_preflight.py) validates GenAILab YAML documents without downloading models/datasets or importing heavy backends.
- [scripts/genai_results_summary.py](scripts/genai_results_summary.py) summarizes GenAILab `profiling_data.json` files and warns on mixed metric scoring versions.
- [scripts/download_genai_checkpoint.sh](scripts/download_genai_checkpoint.sh) safely validates/downloads S3 GenAI checkpoint/export zips without auto-installing AWS/SAML tooling.
- [scripts/cluster_pod_helper.sh](scripts/cluster_pod_helper.sh) provides self-contained Argo/Kubernetes preflight, launch, sync-once, exec, list, and stop commands.
- [scripts/qairt_command_builder.py](scripts/qairt_command_builder.py) generates local QAIRT/QNN conversion, quantization, context, and inference commands from AIMET exports.
- [scripts/qai_hub_qnn_job.py](scripts/qai_hub_qnn_job.py) provides a dry-run-safe AI Hub QNN compile/profile/inference entry point.

## Scope and limits

This repaired skill covers the public AIMET package surfaces under `aimet_torch` and `aimet_onnx`, common quantization/compression/analysis workflows, maintainer install/build/test orientation, GenAILab LLM/VLM scorecards, model/checkpoint access, credentialed evaluation boundaries, cluster/Pod execution patterns, and Qualcomm AI Hub / QAIRT / QNN target-deployment handoff. Heavy or credentialed actions remain gated: do not run large Hugging Face, ImageNet, S3, GitHub Actions, cluster, or SDK workflows until the user supplies assets/credentials and approves the runtime or remote-state effect.

## Operating rules

- Prefer installed-package introspection and small QuantSim smoke checks before blaming repo source code.
- Use source-build commands only inside a dedicated environment; never mutate Conda `base` or a user production environment without approval.
- Do not run ImageNet, Hugging Face, GenAILab, online scorecards, cluster/Pod, S3/AWS, or on-target SDK examples unless the user has supplied datasets/models/credentials/SDKs and approved the runtime or remote-state cost.
- If CUDA behavior matters, verify an actual CUDA tensor allocation or ONNX Runtime CUDA provider; a CPU import is not GPU evidence.
- Keep exported artifacts together: an `.onnx` model plus the matching AIMET `.encodings` JSON are both needed for downstream quantized deployment flows. Use QDQ exports only when the downstream runtime explicitly expects ONNX `QuantizeLinear`/`DequantizeLinear` nodes.
- Do not import this generated skill into the live router unless a future user explicitly requests import.
