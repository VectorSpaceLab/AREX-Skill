---
name: serving-deployment
description: "Route Qwen CLI, web UI, OpenAI-compatible API, vLLM, FastChat,
  Docker, TensorRT, Ascend, and DCU serving or deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qwen Serving and Deployment

Use this sub-skill when the user wants to run Qwen as an interactive CLI, Gradio web demo, OpenAI-compatible FastAPI server, vLLM/FastChat service, Docker container, TensorRT deployment, Ascend NPU workflow, or Hygon DCU/fastllm deployment.

## Safe start

- Use `scripts/qwen_launch_advisor.py` to build local CLI/Web/API commands without loading a checkpoint or opening a port.
- Use `scripts/qwen_docker_command_builder.py` to build Docker commands without pulling images or running containers.
- Validate local checkpoint directories before recommending a service launch; Docker scripts and local loaders expect `config.json` plus tokenizer/model assets.
- Bind to `127.0.0.1` by default. Use `0.0.0.0`, `--share`, or Docker port publishing only when the user accepts network exposure.

## Routes

| User request | Read |
| --- | --- |
| `cli_demo.py`, `web_demo.py`, `openai_api.py`, flags, endpoint semantics, streaming, BasicAuth, request schemas | `references/local-demos-and-api.md` |
| vLLM worker, FastChat controller/API server, standalone vLLM OpenAI API, tensor parallel, dtype, ChatML template | `references/vllm-fastchat.md` |
| `qwenllm/qwen` Docker images, checkpoint mounts, web/API/CLI container commands, logs, cleanup | `references/docker-deployment.md` |
| TensorRT-LLM, Ascend NPU, Hygon DCU, fastllm conversion, vendor device prerequisites | `references/accelerator-support.md` |
| Port, auth, checkpoint, Docker, GPU, function-calling, public-share, or vendor-runtime failures | `references/troubleshooting.md` |

## Boundaries

- For raw model loading or batch inference code, use `../inference-model-loading/SKILL.md`.
- For ReAct/function-calling message conversion and tokenizer/ChatML details, use `../prompting-tool-use-tokenization/SKILL.md`.
- For fine-tuning or GPTQ creation, use `../finetuning-quantization/SKILL.md`.
- For benchmark scripts or repo tests, use `../evaluation-reproduction/SKILL.md`.

## Side-effect rules

Never start a long-running server, pull a Docker image, publish a Gradio share link, run a container, launch vLLM, or mount a vendor device as a smoke test. First provide a dry-run command, list prerequisites, and ask/confirm when the user wants the side effect.
