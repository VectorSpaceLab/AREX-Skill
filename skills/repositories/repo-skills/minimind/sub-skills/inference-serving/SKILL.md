---
name: inference-serving
description: "Guides future agents through MiniMind inference, OpenAI-compatible
  serving, tool-call parsing, thinking output handling, and model artifact
  conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MiniMind Inference & Serving Router

Use this sub-skill when the task is about using an already-trained MiniMind model for inference, local serving, API probing, tool-call parsing, thinking-output handling, WebUI constraints, or artifact conversion/export for third-party inference engines.

## Fast routing

1. Identify the artifact format first:
   - **Transformers-format directory**: portable serving path; expected to contain `config.json`, tokenizer files, and `.safetensors` or `.bin` weights. Prefer this for OpenAI-compatible serving and third-party engines.
   - **Raw MiniMind PyTorch weight**: a `.pth` checkpoint named by weight stage, hidden size, and optional MoE suffix. It also needs the MiniMind model Python modules and tokenizer at runtime, so convert/export it when portability matters.
   - **Raw base + LoRA weight**: useful for local raw inference; merge LoRA into a full raw checkpoint before portable Transformers export or third-party serving.
2. Choose the reference:
   - [workflows.md](references/workflows.md): end-to-end decisions for CLI inference, serving, tool loops, WebUI, conversion, and third-party engines.
   - [cli-reference.md](references/cli-reference.md): artifact checks, local inference parameters, raw-vs-Transformers loading rules, LoRA decisions, and conversion command templates.
   - [api-and-serving.md](references/api-and-serving.md): `/v1/chat/completions` request/response fields, streaming behavior, thinking fields, tool-call schema, and one-shot client usage.
   - [troubleshooting.md](references/troubleshooting.md): diagnosis matrix for missing artifacts, dependency gaps, device errors, malformed tool JSON, chat-template mismatches, and thinking/tool instability.
3. Use bundled helpers instead of reopening source scripts:
   - [scripts/check_model_artifacts.py](scripts/check_model_artifacts.py): classify and validate raw/Transformers model artifacts and print safe conversion plans.
   - [scripts/toolcall_smoke.py](scripts/toolcall_smoke.py): parse MiniMind `<think>` and `<tool_call>` text, normalize OpenAI-style tool calls, and execute deterministic mock tools.
   - [scripts/openai_chat_once.py](scripts/openai_chat_once.py): send one non-interactive OpenAI-compatible chat request, with optional streaming, thinking, and tools.

## Scope boundaries

This sub-skill covers inference and serving only. Route tokenizer training, pretraining, SFT, LoRA training data/setup, and training-time tokenizer template work to `training-basics`. Route DPO, PPO, GRPO, CISPO, Agentic RL training, rollout engines, and reward design to `rlhf-agentic`.

It may mention LoRA only to decide whether to stack a LoRA at raw inference time or merge/export it for serving. It does not explain how to train a LoRA.

## Minimum safe procedure

For any serving or conversion task:

1. Run the artifact checker in dry-inspection mode against the user-provided model path.
2. Prefer a Transformers-format directory for serving. If only raw `.pth` weights exist, plan a conversion before using vLLM, llama.cpp, Ollama, or similar engines.
3. Verify the tokenizer has a chat template with `<think>`, `<tool_call>`, and `<tool_response>` behavior before enabling thinking or tools.
4. Probe the API with the bundled one-shot client before wiring a UI or external orchestrator.
5. Use the bundled tool-call smoke helper to debug parser behavior before blaming the model.

## Verification candidates for later

Do not treat these as already run by this sub-skill draft. Recommended later checks are:

- Parse and execute deterministic mock tool calls with `scripts/toolcall_smoke.py`, including malformed JSON and multiple tool calls.
- Smoke the serving parser behavior on text containing complete `<think>...</think>`, dangling `</think>`, valid `<tool_call>`, and invalid `<tool_call>` JSON.
- Import Qwen3/Qwen3MoE classes from Transformers before Qwen3-compatible export.
- Run a tiny local generate or API completion only when real model weights are available and the backend/device is explicitly selected.
