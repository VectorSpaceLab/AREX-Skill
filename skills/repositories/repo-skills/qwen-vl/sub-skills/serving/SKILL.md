---
name: serving
description: "Operate Qwen-VL Gradio and OpenAI-compatible FastAPI services
  without auto-starting listeners."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Qwen-VL Serving

Use this sub-skill when the user wants to launch, configure, wrap, or debug the
Qwen-VL multimodal Gradio demo or the OpenAI-compatible FastAPI chat service.
Do not start a long-running listener unless the user explicitly asks for it;
prepare commands, inspect flags, and diagnose configuration first.

## Read first

- [Service reference](references/service-reference.md) for launch commands,
  CLI flags, endpoint shapes, function-call formatting, CORS, and Docker notes.
- [Troubleshooting](references/troubleshooting.md) for checkpoint, dependency,
  binding, streaming, function-calling, Gradio, and Docker failure modes.
- [Bundled OpenAI API server](scripts/openai_api.py) and
  [bundled Gradio web demo](scripts/web_demo_mm.py) are copied/adapted runtime
  entrypoints. Run them with `python ... --help` before any launch.

## Choose this sub-skill for

- Preparing a safe localhost or exposed-host launch command for the Gradio
  multimodal demo.
- Preparing a FastAPI command that exposes `/v1/models` and
  `/v1/chat/completions` in an OpenAI-compatible shape.
- Explaining `--checkpoint-path`, `--cpu-only`, `--server-name`,
  `--server-port`, `--share`, and `--inbrowser` behavior.
- Diagnosing API errors such as unsupported streaming, malformed chat/function
  messages, dependency imports, port conflicts, or incomplete checkpoints.
- Reading reference-only Docker build/run patterns for the web demo, the
  OpenAI-compatible API, or the Int4 OpenAI-compatible API image.

## Route elsewhere

- One-off direct model calls, prompt construction, grounding markup, and model
  selection semantics belong in [inference](../inference/SKILL.md).
- Supervised finetuning, LoRA, Q-LoRA, and training data preparation belong in
  [finetuning](../finetuning/SKILL.md).
- Official benchmark execution, scoring, and submission formats belong in
  [evaluation](../evaluation/SKILL.md).

## Operating rules

1. Treat both service scripts as long-running: use `--help`, dependency probes,
   and command construction unless the user asks to launch.
2. Prefer `--server-name 127.0.0.1` for local use. Use `0.0.0.0` only when the
   user intentionally exposes the service and has considered firewall, proxy,
   authentication, and the API server's permissive CORS policy.
3. For Qwen-VL-Chat service behavior, pass an explicit chat checkpoint even
   when a script has a default. The OpenAI API script inherits a text-chat
   default from the source; the Gradio script defaults to Qwen-VL-Chat.
4. Do not promise streaming from the bundled OpenAI-compatible service: the
   current handler returns HTTP 400 for `stream: true`.
