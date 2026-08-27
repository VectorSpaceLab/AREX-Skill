---
name: inference-deployment
description: "Run and debug ms-swift inference, app, deployment, backend
  selection, OpenAI-compatible serving, multimodal requests, adapters, and
  result/logprob workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Deployment

Use this sub-skill when an agent needs to run `swift infer`, `swift app`, or `swift deploy`, choose an inference backend, call a local OpenAI-compatible server, use `swift.infer_engine` Python APIs, or debug serving/runtime failures.

## Route first

- Use `references/workflows.md` for concrete CLI, app, deploy, client, batch, multimodal, LoRA, logprob, and result-saving recipes.
- Use `references/api-reference.md` for `InferArguments`, `DeployArguments`, `AppArguments`, `InferRequest`, `RequestConfig`, engines, OpenAI endpoints, and Python client shapes.
- Use `references/backend-compatibility.md` before selecting `transformers`, `vllm`, `sglang`, or `lmdeploy`.
- Use `references/troubleshooting.md` for backend/model mismatches, optional dependency failures, QLoRA limitations, multimodal OOM, `vllm_limit_mm_per_prompt`, result/logprob surprises, adapter loading, and unreachable local servers.
- Use `scripts/build_inference_command.py` to print safe `swift infer`, `swift deploy`, or `swift app` command skeletons without launching models.
- Use `scripts/smoke_openai_client.py` to test a local OpenAI-compatible `/v1/chat/completions` server; it targets localhost by default and does not use external network resources.

## Use cases covered here

- Interactive text or multimodal CLI inference with `swift infer`.
- Dataset or batch inference with saved JSONL results and optional metrics/logprobs.
- Local Gradio-style inference UI with `swift app`, either self-hosting a model or connecting to an existing base URL.
- OpenAI-compatible serving with `swift deploy`, including `/v1/models`, `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, health/ping, and Swift client calls.
- Backend selection across `transformers`, `vllm`, `sglang`, and `lmdeploy`, including optional dependency caveats.
- Full checkpoint, LoRA adapter, merged LoRA, and multiple named LoRA serving plans.

## Reroute boundaries

- Training command construction, checkpoint creation, and LoRA training arguments belong to the training sub-skill.
- Dataset schema design and custom dataset registration belong to data/model customization.
- Export, merge-only packaging, quantization, and evaluation pipelines belong to export/evaluation.
- GRPO rollout, Ray, and Megatron serving/sampling internals belong to advanced RL/distributed workflows.
