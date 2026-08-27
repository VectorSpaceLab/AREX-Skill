---
name: chat-and-serve
description: "Guides LLaVA image chat, local inference, CLI prompts, model
  workers, controller/Gradio serving, conversation modes, quantized loading, and
  optional SGLang notes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chat and Serve

Use this sub-skill for one-image or few-image LLaVA inference, interactive CLI use, local model workers, controller and Gradio serving, or when a user asks how to choose `--conv-mode`, `--device`, `--load-4bit`, or `--load-8bit` for a LLaVA checkpoint.

## What it covers

- `python -m llava.eval.run_llava`
- `python -m llava.serve.cli`
- `python -m llava.serve.controller`
- `python -m llava.serve.model_worker`
- `python -m llava.serve.gradio_web_server`
- conversation mode selection from `llava.conversation.conv_templates`
- image preprocessing and `<image>` token placement
- optional quantized loading when bitsandbytes is available
- optional SGLang and Replicate deployment notes

## What it excludes

- Fine-tuning, data conversion for training, and checkpoint merge/delta utilities belong to `train-and-finetune`.
- Benchmark answer-file generation and submission conversion belong to `evaluate-and-benchmark`.
- This sub-skill does not claim SGLang is installed by default.

## Read these references

- [`references/api-reference.md`](references/api-reference.md) for verified loader and helper signatures.
- [`references/cli-and-serving.md`](references/cli-and-serving.md) for command templates and launch order.
- [`references/conversation-and-images.md`](references/conversation-and-images.md) for prompt formatting, image tokens, and conversation mode selection.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing CUDA, model load, port, and quantization failures.

## Bundled scripts

- [`scripts/check_chat_runtime.py`](scripts/check_chat_runtime.py) to confirm imports, optional CUDA visibility, and optional SGLang presence.
- [`scripts/build_single_image_command.py`](scripts/build_single_image_command.py) to print a safe command template for either `run_llava` or `llava.serve.cli`.

## Typical routing cues

Choose this sub-skill when the user says any of:

- run LLaVA on one image
- chat with an image
- start the Gradio demo
- start a model worker
- start the controller
- use 4-bit or 8-bit LLaVA inference
- set the conversation mode
- choose between `run_llava` and the serving CLI

## Common decision points

1. **Single-turn or interactive?**
   - Use `llava.eval.run_llava` for a one-shot answer.
   - Use `llava.serve.cli` for an interactive loop.
2. **Do you need a server?**
   - Start the controller, then one or more workers, then the Gradio UI.
3. **Is the checkpoint LoRA-based?**
   - Supply `--model-base` when the checkpoint expects a base model.
4. **Are you choosing a conversation template?**
   - Use the model name and the verified template table in the conversation reference.

## Troubleshooting snapshot

If inference or serving fails, check whether the problem is actually one of these:

- missing CUDA or unsupported GPU architecture
- checkpoint download or gated model access
- wrong `--model-base` for a LoRA checkpoint
- image count mismatch between prompt tokens and provided images
- model worker not registered with the controller
- Gradio started before any worker is available
- port conflict on controller or worker port
- unsupported quantization on macOS or Windows

Read the troubleshooting reference before widening scope to backend or model-download issues.
