---
name: quantization
description: "Plan LMDeploy Lite quantization, KV-cache quantization, and
  quantized model handoff workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Quantization

Use this sub-skill when the task is to create, select, validate, or hand off quantized LMDeploy model artifacts. It covers LMDeploy Lite weight quantization, online KV-cache quantization, and the minimum inference/server commands needed to prove a quantized artifact is usable.

## Owns

- `lmdeploy lite auto_awq`, `auto_gptq`, `calibrate`, and `smooth_quant` command planning.
- AWQ/GPTQ weight-only W4A16 artifacts, SmoothQuant W8A8/FP8 artifacts, and calibration dataset/sample/sequence-length choices.
- `quant_policy` selection for online KV-cache quantization: none, INT4, INT8, FP8, FP8_E5M2, and TurboQuant.
- Quantized-artifact handoff commands for `pipeline`, `lmdeploy chat`, and `lmdeploy serve api_server`.
- Dependency, GPU memory, disk, model-format, and calibration troubleshooting for quantization workflows.

## Route Away

- Route ordinary unquantized offline text inference, generation settings, chat templates, and `pipeline()` usage depth to `pipeline-inference`.
- Route API endpoint behavior, OpenAI-compatible clients, proxy routing, and production server operations to `serving-apis`.
- Route multimodal media inputs and VLM prompt formatting to `vision-language`.
- Route backend kernel internals, scheduler tuning, model patching, and new-model backend support to `backend-extension`.

## Start Here

- Use `references/cli-reference.md` for command flags, defaults, artifact formats, and `quant_policy` values.
- Use `references/workflows.md` for AWQ, GPTQ, SmoothQuant/FP8, KV-cache quantization, and validation workflows.
- Use `references/qwen3-quantization-recipes.md` for adaptable Qwen3 `llm-compressor` AWQ/GPTQ recipes.
- Use `references/troubleshooting.md` when quantization fails or a quantized output will not load.
- Use `scripts/plan_quantization_command.py` to generate safe, non-executing command plans and catch common incompatible options.

## Safe Default Decisions

- Prefer AWQ with `--w-bits 4 --w-group-size 128 --calib-samples 128 --calib-seqlen 2048 --batch-size 1` for a first W4A16 artifact.
- Lower `--calib-seqlen` and keep `--batch-size 1` before reducing samples when calibration OOMs.
- Name `--work-dir` after the base model and quantization format, such as `model-name-awq-4bit`, so LMDeploy can more easily infer the intended chat template.
- Use `--model-format awq` for LMDeploy AWQ artifacts and `--model-format gptq` for GPTQ artifacts; do not swap them.
- For KV cache, start with `--quant-policy 8` when accuracy matters, use `4` for more memory pressure, and reserve `42` for PyTorch TurboQuant-compatible workloads.
