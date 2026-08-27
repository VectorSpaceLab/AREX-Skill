---
name: model-deployment
description: "Guides LazyLLM model modules, online providers, local serving,
  fine-tuning, multimodal examples, and backend-aware deployment diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LazyLLM Model Deployment

Use this sub-skill for LazyLLM tasks about `TrainableModule`, `OnlineModule`, `OnlineChatModule`, `ServerModule`, `ActionModule`, model type mapping, model deployment, fine-tuning, distillation, local serving, provider calls, streaming tool calls, or multimodal examples.

## Start here when

- The user asks how to wrap a local model or online provider in LazyLLM.
- The task mentions `lazyllm deploy`, vLLM, LMDeploy, LightLLM, Infinity, LLaMA-Factory, model caches, CUDA, or serving ports.
- A provider/chat module fails due to model type, API key, timeout, message inspection, streaming tool calls, or provider response format.
- The user wants to adapt chatbot, online chatbot, multimodal, painting, TTS, STT, OCR, fine-tuning, or distillation examples.

## Files to read

- [model-workflows.md](references/model-workflows.md) for class selection, online/local/multimodal recipes, and safe provider-free checks.
- [backend-matrix.md](references/backend-matrix.md) for optional dependency and backend classification.
- [troubleshooting.md](references/troubleshooting.md) for provider, CUDA, model path, and serving failures.
- [scripts/model_surface_smoke.py](scripts/model_surface_smoke.py) for a no-network check of model type inference and online chat message utilities.

## Safe workflow

1. **Classify the module type.**
   - `OnlineModule` / `OnlineChatModule`: provider or endpoint backed.
   - `TrainableModule`: local model/fine-tune/deploy abstraction.
   - `ServerModule`: wraps functions/modules/services and may start/bind servers.
   - `ActionModule`: wraps deterministic actions in a LazyLLM module chain.
2. **Classify backend requirements.** Do not run a model call until provider credentials or local model/GPU/backend are confirmed.
3. **Perform no-network checks first.**
   ```bash
   python scripts/model_surface_smoke.py
   python ../../scripts/inspect_lazyllm_surface.py --include-optional
   ```
4. **Route composed apps to their owner.** If model modules are only nodes inside a `pipeline`, read [flow-orchestration](../flow-orchestration/SKILL.md). If they serve RAG or agents, read the RAG or agent sub-skill too.
5. **Record optional verification clearly.** Online/GPU/model-download tests are optional unless the user explicitly asks to execute them and supplies resources.

## Verified signatures to remember

- `TrainableModule(base_model='', target_path='', *, stream=False, return_trace=False, trust_remote_code=True, type=None, source=None, use_model_map=True)`
- `OnlineModule(model=None, source=None, *, type=None, url=None, **kwargs)`
- `OnlineChatModule(model=None, source=None, url=None, stream=True, return_trace=False, skip_auth=False, type=None, api_key=None, static_params=None, id=None, name=None, group_id=None, dynamic_auth=False, timeout=180, **kwargs)`
- `ServerModule(m=None, pre=None, post=None, stream=False, return_trace=False, port=None, pythonpath=None, launcher=None, url=None, num_replicas=1, security_key=None)`
- `ActionModule(*action, return_trace=False)`

## Model type and streaming facts

LazyLLM has provider model-name mapping helpers that classify names into categories including `llm`, `vlm`, `stt`, `tts`, `embed`, `sd`, `text2video`, and `cross_modal_embed`. Tests also verify online chat helper behavior that removes prior tool traces and merges streamed tool-call chunks by index.

Use these pure helpers to debug provider message formatting without calling the provider.

## Backend boundaries

- **Safe CPU checks:** signature inspection, model type mapping, chat history sanitization, stream chunk merge utility.
- **Provider-required:** online chat/completion, online multimodal, web-search-backed flows, writer pipeline with cloud LLM.
- **GPU/local backend:** vLLM/LMDeploy/LightLLM, local TrainableModule inference, fine-tuning, distillation, painting, speech, OCR.
- **External service:** deployed server endpoints, k8s/slurm/SCO launcher tests.

## Handoff outputs

When you finish a model-deployment task, leave:

- chosen LazyLLM module class and constructor parameters,
- exact optional extra/backend/provider requirements,
- safe smoke result or reason it was not executable,
- explicit status of credentials, model path/cache, GPU, server port, and budget,
- routes to flow/RAG/agent/writer sub-skills for composed apps.
