---
name: serving
description: "Launch and reason about OpenChat's OpenAI-compatible vLLM/FastAPI server."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenChat serving sub-skill

Use this sub-skill when the task is to launch, secure, call, or debug OpenChat's OpenAI-compatible API server implemented by `python -m ochat.serving.openai_api_server`.

## Route by task

- Launching the server, choosing `--model`, `--model-type`, GPU/Ray/tensor-parallel flags, CORS, API keys, or logging: read [references/deployment.md](references/deployment.md).
- Calling `/v1/models` or `/v1/chat/completions`, constructing chat payloads, streaming, `n`, sampling, `condition`, context limits, and model aliases: read [references/api-reference.md](references/api-reference.md).
- Debugging missing dependencies, CUDA/vLLM/Ray errors, 404 model names, 400 context length failures, API-key failures, ignored system prompts, or unsupported request fields: read [references/troubleshooting.md](references/troubleshooting.md).
- Use [scripts/run_openchat_server.sh](scripts/run_openchat_server.sh) as the safe installed-package wrapper; it forwards to the module and refuses non-help launches without `--model`.

## Boundaries

- In scope: serving, deployment, security/logging knobs, OpenAI-compatible API usage, vLLM/Ray/GPU prerequisite reasoning.
- Route prompt-template internals, tokenization details, and `condition` semantics beyond serving behavior to [../prompting/SKILL.md](../prompting/SKILL.md).
- Route benchmark harness, MT-Bench/AlpacaEval/HumanEval evaluation flows, and answer matching to [../evaluation/SKILL.md](../evaluation/SKILL.md).
- Treat Docker, SSH, and cloudflared files as reference-only deployment evidence, not bundled helpers to run from this skill.
- Source training, data generation, scripts, and experimental notebooks are outside this sub-skill.

## Safety defaults

Actual serving requires model weights, compatible CUDA/PyTorch/vLLM/Ray packages, and enough GPU memory for the selected model and tensor-parallel plan. Do not start a long-running listener unless the user explicitly asks for a launch and has supplied the model source, host/port exposure intent, and security requirements.
