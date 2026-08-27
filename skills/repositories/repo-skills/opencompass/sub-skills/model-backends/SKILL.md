---
name: model-backends
description: "Configure OpenCompass model backends including HuggingFace, API,
  custom wrappers, LMDeploy, vLLM, credentials, resource run_cfg,
  tokenizer/model kwargs, batching, and backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Backends

Use this sub-skill when an OpenCompass task is about model configuration rather than dataset selection, prompt construction, or workflow launch. It covers HuggingFace/local models, API providers, accelerated LMDeploy/vLLM/LightLLM-style backends, custom model wrappers, credentials, and resource sizing.

## Route by Backend

- HuggingFace/local Transformers models: use `references/model-configuration.md` for `HuggingFace`, `HuggingFaceCausalLM`, `HuggingFacewithChatTemplate`, tokenizer/model kwargs, `batch_size`, `max_seq_len`, `max_out_len`, `batch_padding`, and `run_cfg`.
- API models: use `references/api-models.md` for `OpenAI`, `OpenAISDK`, `TurboMindAPIModel`, credential handling, `query_per_second`, `retry`, `rpm_verbose`, `openai_api_base`, and no-network config checks.
- Accelerated local backends: use `references/backend-compatibility.md` for `--accelerator {vllm,lmdeploy,None}`, direct `VLLM` configs, direct `TurboMindModel` configs, service-based acceleration, and optional dependency boundaries.
- New/custom model support: use `references/model-configuration.md#custom-model-extension-route` when an existing OpenCompass backend cannot express the target model.
- Backend failures: use `references/troubleshooting.md` before changing datasets, prompts, summarizers, or evaluation mode.

## Boundaries

- For prompt templates, `meta_template`, and generation prompt behavior, coordinate with `../prompt-and-inference/SKILL.md` if present.
- For dataset imports, config composition, and `read_base()` patterns, coordinate with `../configuration-and-datasets/SKILL.md` if present.
- For `opencompass` CLI launch modes, `--mode`, `--reuse`, runners, and work directories, coordinate with `../evaluation-workflows/SKILL.md` if present.
- Do not claim real HuggingFace/GPU/API inference is verified unless a task explicitly runs it in a suitable environment with required optional extras and credentials.

## Bundled Script

- `scripts/check_api_model_config.py`: loads an OpenCompass config, inspects model dictionaries, identifies likely API models, checks credential placeholders/environment-variable references, validates common API rate/resource fields, and exits before building models or making network calls.
