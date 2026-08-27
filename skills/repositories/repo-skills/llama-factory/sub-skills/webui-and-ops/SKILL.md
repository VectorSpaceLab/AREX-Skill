---
name: webui-and-ops
description: "Operate LLaMA Factory's LlamaBoard Web UI, web chat,
  install/runtime checks, CLI help/version/env routes, operational environment
  variables, Docker exposure, and experiment-monitor setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Web UI and Ops

Use this sub-skill when the user needs to install or sanity-check LLaMA Factory, launch or troubleshoot LlamaBoard or WebChat, inspect CLI routes, collect environment/version information, set operational environment variables, expose Docker ports, or configure experiment-monitoring integrations.

## Route by task

- For installation, import, CLI route discovery, `help`, `version`, `env`, Docker, and a quick local health check, use `references/installation-and-commands.md` and `scripts/llamafactory_sanity_check.py`.
- For `llamafactory-cli webui`, `llamafactory-cli webchat`, Gradio host/share settings, UI state files, subprocess logs, and LlamaBoard process behavior, use `references/webui-operations.md`.
- For missing dependencies, port conflicts, hub toggles, version checks, logging verbosity, VRAM recording, forced `torchrun`, and monitors such as W&B, SwanLab, and MLflow, use `references/troubleshooting.md`.
- Route OpenAI-compatible API endpoint behavior, request schemas, vLLM/SGLang serving details, and API authentication to `../inference-and-serving/`.
- Route training YAML semantics, dataset/template choices, LoRA/quantization/deepspeed tuning, and loss/metric interpretation to `../training-and-configs/`.
- Route model loading, adapter merge/export, and tokenizer/model patching to `../model-loading-and-export/`.
- Route experimental v1 behavior to `../v1-experimental/` when present; v0 is the default unless `USE_V1=1` is set.

## Fast workflow

1. Verify the package context with `python sub-skills/webui-and-ops/scripts/llamafactory_sanity_check.py` from an environment where LLaMA Factory may be installed.
2. Confirm routes with `llamafactory-cli help`, `llamafactory-cli version`, and `llamafactory-cli env` when dependencies are complete.
3. Launch the full UI with `llamafactory-cli webui` or pure chat UI with `llamafactory-cli webchat`.
4. If launch fails, check optional imports (`gradio`, `fastapi`, `uvicorn`, `sse-starlette`), port/proxy settings, and `LLAMAFACTORY_VERBOSITY=DEBUG` logs before changing training or inference configs.
