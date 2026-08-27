---
name: genai-lab
description: "Run and configure AIMET GenAILab LLM/VLM quantization scorecards
  with Torch or ONNX backends, exports, caches, and summaries."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET GenAILab

Use this sub-skill when the user asks about AIMET GenAI scorecards, `python -m GenAILab`, LLM/VLM quantization recipes, YAML configs, recipe caches, FP/model caches, exported GenAI artifacts, local Torch/ONNX GenAI runs, online GitHub Actions scorecards, or result summaries.

## Read/run first

- Read [GenAILab workflows](../../references/genai-lab.md) for local, online, export, cache, and result-summary flows.
- Read [model access and credentialed evaluation](../model-access-and-credentialed-evaluation/SKILL.md) when the model or metric needs Hugging Face, GitHub CLI, AWS/S3, SAML, or external benchmark data.
- Read [backend compatibility](../../references/backend-compatibility.md) before claiming CUDA, ONNX Runtime CUDA provider, or large-model capacity.
- Run [genai_config_preflight.py](../../scripts/genai_config_preflight.py) before launching a local or online run; it validates YAML shape without downloading models or datasets.
- Run [genai_results_summary.py](../../scripts/genai_results_summary.py) on `profiling_data.json` when you only need to inspect results or detect mixed metric scoring versions.

## Core workflow

1. **Preflight the config.** Validate required `model`, `metrics`, `precision`, `recipe`, datasets, and adaptations before allocating GPU time.
2. **Choose framework.** Use `torch` for AIMET Torch recipes, `onnx` for ONNX QuantSim/Runtime recipes, or `both` to run both sequentially locally.
3. **Plan credentials and caches.** Hugging Face access is needed for gated or remote models/datasets. Use explicit cache directories for FP outputs, recipe checkpoints, and ONNX model exports when runs are expensive.
4. **Run locally when the environment is ready.** Use `python -m GenAILab --framework <torch|onnx|both> --config cfg.yaml` plus output/cache flags.
5. **Run online only when GitHub credentials and pushed code are appropriate.** `--online` dispatches GitHub Actions and uses the last pushed commit, not uncommitted local files.
6. **Inspect outputs.** Results append to profiling JSON/CSV, while exports contain tokenizer/config, ONNX/encodings, and optional secondary ONNX-eval artifacts.

## Decision points

- **Model size and context length:** LLM recipes can require tens of GB of VRAM; validate sequence/context length and precision before launch.
- **Metrics:** PPL uses Wikitext; MMLU/MMMU-style metrics require benchmark datasets and scoring-version compatibility.
- **Recipe chain:** A chain that does not end with `Calibration`, `RemoveQuantization`, or `Skip` has calibration auto-inserted by the parser.
- **Export:** `export: true` or `eval_in_onnx: true` creates artifacts under the selected export root. Use the export inspector and SDK sub-skill before target handoff.

## Boundaries

- Route pod launch/sync/stop work to [cluster-pod-workflows](../cluster-pod-workflows/SKILL.md).
- Route S3 checkpoint downloads, Hugging Face tokens, GitHub Actions download/merge, and result comparability to [model-access-and-credentialed-evaluation](../model-access-and-credentialed-evaluation/SKILL.md).
- Route QNN/QAIRT/AI Hub deployment from exported artifacts to [qualcomm-sdk-deployment](../qualcomm-sdk-deployment/SKILL.md).
- Route ordinary CNN/ResNet/MobileNet quantization outside GenAILab to the Torch/ONNX sub-skills.

## Expected answer shape

For a GenAILab task, include the config document or patch, the framework, local/online decision, credential requirements, cache/export/results directories, expected outputs, and a bounded validation command before starting long runs.
