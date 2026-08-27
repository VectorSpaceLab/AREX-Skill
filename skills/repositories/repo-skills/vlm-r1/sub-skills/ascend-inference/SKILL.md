---
name: ascend-inference
description: "Route Huawei Ascend vllm-ascend and XLLM inference for VLM-R1 OVD
  checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ascend-inference

Use this sub-skill when a user needs to deploy or exercise a VLM-R1 OVD checkpoint on Huawei Ascend hardware through `vllm-ascend` or XLLM. It is a recipe and command-template skill: it does not claim that the current host has an Ascend NPU.

## Route first

- **Use here** for Ascend Atlas 800T A2 / 910B or Atlas 300I Duo online service, offline request scaffolds, OpenAI-compatible chat requests, XLLM command rendering, and Ascend performance notes.
- **Route away** for CUDA GRPO training, LoRA/freeze/multi-node training, JSONL/reward design, and REC/OVD CUDA evaluation. Those belong to sibling VLM-R1 sub-skills.
- **Do not ask future agents to reopen the source repository.** The operating facts needed for Ascend workflows are distilled in `references/ascend-inference-workflows.md` and `references/troubleshooting.md`.

## Minimum safe workflow

1. Identify the target hardware and engine:
   - Atlas 800T A2 / 910B: `vllm-ascend` and XLLM recipes are available.
   - Atlas 300I Duo: `vllm-ascend` recipe is available; use float16-oriented settings.
2. Confirm the deployment host has Ascend device visibility (`npu-smi` and required device nodes) before rendering runnable commands.
3. Make the model checkpoint available locally. The examples use `omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321` as the model id and `VLM-R1-Qwen2.5VL-3B-OVD-0321` as a placeholder local directory.
4. Use the bundled renderers instead of copying hard-coded commands:
   - `scripts/ascend_offline_request_template.py --help`
   - `scripts/ascend_server_client_templates.sh --help`
5. If the user requests performance testing, preserve the evalscope multimodal caveat from `references/ascend-inference-workflows.md`; do not silently run text-only stress tests against XLLM's VLM backend.

## Key operating notes

- `vllm-ascend` uses OpenAI-compatible `/v1/chat/completions` requests for online serving and a vLLM Python `LLM.generate` pattern for offline inference.
- Atlas 300I Duo evidence uses the `vllm-ascend` 310P image tag and float16 settings; if a downloaded model metadata declares bfloat16, adjust it to float16 for that deployment target before serving.
- XLLM evidence covers Atlas 800T A2 / 910B only. Its server command needs a built XLLM executable, `--backend=vlm`, `--model`, `--port`, `--max_memory_utilization`, and `--model_id`.
- All bundled scripts are renderers/templates. They should print or write request scaffolds and commands; they should not start a server, call a live service, download a model, or probe a real NPU by default.

## Internal references

- `references/ascend-inference-workflows.md` — hardware matrix, vllm-ascend Docker/server/offline/client flows, XLLM build/server/client flow, prompt schema, evalscope caveat.
- `references/troubleshooting.md` — device initialization, container mounts, dtype, XLLM build, service/client, prompt JSON, and performance triage.
- `scripts/ascend_offline_request_template.py` — offline vLLM request/Python scaffold renderer.
- `scripts/ascend_server_client_templates.sh` — vllm-ascend/XLLM server and client command renderer.
