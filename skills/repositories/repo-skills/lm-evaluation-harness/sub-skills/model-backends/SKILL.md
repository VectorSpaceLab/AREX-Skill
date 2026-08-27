---
name: model-backends
description: "Choose, install, configure, extend, and troubleshoot LM Evaluation
  Harness model backends, including optional extras, API/local backends, custom
  LM implementations, chat templates, and thinking-token behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Backends

Use this sub-skill when the user needs to select or configure an `lm-eval` model backend, install a narrow optional extra, build a custom `LM` or API backend, use chat templates or reasoning-token stripping, or diagnose backend import/credential/hardware/`model_args` failures.

## Route Quickly

- For built-in backend names, optional extras, request-type support, and safe `--model_args` examples, read [references/backend-reference.md](references/backend-reference.md).
- For Python `LM` subclasses, `@register_model`, request method contracts, and registry loading, read [references/custom-models.md](references/custom-models.md).
- For OpenAI-compatible local servers, OpenAI/Anthropic/LiteLLM/TextSynth-style APIs, tokenization, credentials, and completion-vs-chat limitations, read [references/api-models.md](references/api-models.md).
- For `--apply_chat_template`, `--fewshot_as_multiturn`, custom chat-capable backends, and `enable_thinking`/`think_end_token`, read [references/chat-templates.md](references/chat-templates.md).
- For import errors, missing extras, credential failures, loglikelihood on chat endpoints, hardware mismatch, and `model_args` quoting, read [references/troubleshooting.md](references/troubleshooting.md).

## Boundaries

- Stay here for backend selection, backend-specific install extras, `--model` names, `--model_args`, custom model classes, API model classes, and chat-template support implemented by models.
- Route task YAML schema, output types, filters, datasets, and `include_path` authoring to `task-authoring`.
- Route evaluation CLI orchestration, batching strategy, cache flags, seeds, `--limit`, and run configuration files to `evaluation-runs` unless the issue is backend-specific.
- Route result files, W&B, TrackIO, Hugging Face Hub uploads, and sample logging to `result-logging`.

## Bundled Helpers

- Run `python scripts/check_backend_requirements.py --list-known` from this sub-skill directory to inspect known extras and backend aliases without importing heavy concrete backends.
- Run `python scripts/check_backend_requirements.py --backend hf --backend local-completions` to check whether registry aliases resolve and which optional packages appear missing.
- Run `python scripts/model_args_builder.py --set pretrained=EleutherAI/pythia-160m --set dtype=float16` to build shell-safe `--model_args` strings and avoid comma/quote mistakes.

## Safety Notes

- Do not claim every backend works in a base install. The base package intentionally excludes heavy model backends such as `torch`, `transformers`, `vllm`, and `litellm`.
- Prefer the smallest extra that matches the backend: for example `lm_eval[hf]`, `lm_eval[vllm]`, `lm_eval[api]`, `lm_eval[litellm]`, `lm_eval[optimum]`, `lm_eval[ipex]`, or `lm_eval[habana]`.
- For closed or remote APIs, avoid recording API keys in commands, configs, results, or skill content; use environment variables and redact user-provided secrets.
