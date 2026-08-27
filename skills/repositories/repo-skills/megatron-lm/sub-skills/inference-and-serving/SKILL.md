---
name: inference-and-serving
description: "Use Megatron-LM offline inference, high-level LLM APIs,
  coordinator mode, and serving command templates."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# inference-and-serving

Use this sub-skill when the user asks for Megatron offline generation, dynamic/static inference, high-level `MegatronLLM` / `MegatronAsyncLLM`, coordinator mode, OpenAI-compatible serving, or text-generation server troubleshooting.

## Read first

- For offline and server workflows, command shapes, and mode choices, read [references/inference-workflows.md](references/inference-workflows.md).
- For high-level API signatures and lifecycle, read [references/api-reference.md](references/api-reference.md).
- For coordinator, prompt length, checkpoint/tokenizer, CUDA graph, and server failures, read [references/troubleshooting.md](references/troubleshooting.md).
- Use [scripts/render_offline_inference_command.py](scripts/render_offline_inference_command.py) or [scripts/render_inference_server_command.py](scripts/render_inference_server_command.py) to render safe templates without starting inference.

## Route by task

| Task | Action |
|---|---|
| Batch/offline generation | Choose sync direct vs coordinator vs async; render an offline command template. |
| Start HTTP/OpenAI-compatible server | Use coordinator mode and server template; confirm ports and frontend replicas. |
| Use Python high-level API | Read API reference for `MegatronLLM`, `MegatronAsyncLLM`, `ServeConfig`, and `SamplingParams`. |
| Debug checkpoint/tokenizer load | Route checkpoint-format issues to checkpointing, then return to inference context limits. |
| Compare legacy tools vs high-level API | Prefer high-level API for new usage; keep legacy server flags only when needed. |

## Required inputs before an inference answer

- Checkpoint root and format.
- Tokenizer type/files/model and vocabulary compatibility.
- Model architecture args and parallel sizes.
- Number of GPUs/ranks and whether coordinator mode is desired.
- Prompt source: inline prompts, prompt file, generated tokens per request, output JSON path.
- Sampling controls: temperature, top-k/top-p, max tokens.

## Safety and validation

- Do not start a long-running server unless the user explicitly requests it.
- For command templates, prefer `--help`/dry command rendering first.
- For server tasks, clarify bind host/port and whether external network exposure is intended.
- Validate prompt lengths against context limits; chunked prefill changes the constraint.
- Ensure all ranks receive a shutdown path in coordinator/server mode.

## Boundaries

- Install/CUDA readiness belongs to [../install-and-environment/SKILL.md](../install-and-environment/SKILL.md).
- Checkpoint conversion/resharding belongs to [../checkpointing-and-conversion/SKILL.md](../checkpointing-and-conversion/SKILL.md).
- Training and data preprocessing belong to [../training-cli-and-data/SKILL.md](../training-cli-and-data/SKILL.md).
