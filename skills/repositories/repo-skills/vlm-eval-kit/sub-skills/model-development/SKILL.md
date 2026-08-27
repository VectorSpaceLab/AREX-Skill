---
name: model-development
description: "Configure and extend VLMEvalKit model wrappers, API providers,
  registries, and prompt adapters."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# VLMEvalKit model development

Use this sub-skill when the task is to configure an existing VLMEvalKit model name, add or adapt a local VLM wrapper, use LiteLLM/LMDeploy/OpenAI-compatible APIs, register model aliases, or implement dataset-aware prompt adapters. VLMEvalKit is the distribution/import package `vlmeval`; its main evaluation CLI is `run.py`, and the console helper is `vlmutil`.

## Route here when

- A user needs to choose between an existing `supported_VLM` name, JSON model config, `--base-url`, or a new wrapper/adapter.
- A wrapper must satisfy `BaseModel.generate()` / `generate_inner()` / optional `chat_inner()` contracts.
- An API provider must satisfy `BaseAPI.generate()` / `generate_inner()` ret-code contracts.
- A LiteLLM, LMDeploy, OpenAI-compatible, or custom prompt-adapter setup fails before or during model invocation.
- A model-specific prompt, image/video conversion, device split, dependency version, or thinking-output issue must be diagnosed.

## Route elsewhere

- Running evaluation jobs, reuse/resume behavior, output files, `status.json`, scans, and summaries: [evaluation](../evaluation/SKILL.md).
- Dataset/benchmark authoring, TSV/video formats, prompt construction on the dataset side, metrics, judges, and converters: [benchmark-authoring](../benchmark-authoring/SKILL.md).

## First decision: configure or implement?

1. **Existing registry name:** discover names with `vlmutil mlist all` or narrower categories, then use the exact key from `vlmeval/config.py`.
2. **JSON config:** use `run.py --config` when the user needs local aliases or per-model kwargs without editing package files.
3. **OpenAI-compatible endpoint:** use `run.py --base-url` when a local/remote service already exposes a chat-completions-compatible endpoint; this route constructs `LMDeployAPI` without editing `config.py`.
4. **New wrapper or adapter:** implement the smallest contract in `vlmeval/vlm/`, `vlmeval/api/`, or `vlmeval/api/adapters/`, then register it in `vlmeval/config.py` or a JSON config.

## Reference map

- [API reference](references/api-reference.md): `BaseModel`, `BaseAPI`, LiteLLM, LMDeploy/OpenAI-compatible invocation contracts.
- [Model registry](references/model-registry.md): `supported_VLM`, `model_groups`, `vlmutil mlist`, JSON config, and `--base-url` selection rules.
- [Prompt adapters](references/prompt-adapters.md): adapter registry, `use_custom_prompt`, `process_inputs`, `process_payload`, `postprocess`, and thinking split patterns.
- [Troubleshooting](references/troubleshooting.md): missing deps/keys, bad base URLs, media formats, custom prompt mismatches, device/WORLD_SIZE issues, compatibility notes, and thinking-output failures.

## Validation checklist

Before routing a model-development change back to evaluation:

- Confirm the chosen model name appears in `supported_VLM` or is defined in the JSON `model` section, unless `--base-url` is intentionally used.
- Confirm wrappers accept VLMEvalKit message lists with allowed types `text`, `image`, and when supported `video`.
- Confirm local VLM wrappers implement `generate_inner(message, dataset=None)`; only add `chat_inner` when multi-turn chat is supported.
- Confirm API wrappers return `(ret_code, answer, log)` from `generate_inner` and let `BaseAPI.generate()` handle retry/failure behavior.
- Confirm prompt adapters are registered and selected by name when using `--custom-prompt` or `custom_prompt` kwargs.
- Treat CUDA, live provider calls, dataset downloads, Gradio services, and large model evaluations as unverified unless the current task explicitly verifies them.

## Source evidence distilled

Primary evidence: `docs/en/Development.md`, `docs/en/Quickstart.md`, `docs/en/EvalByLMDeploy.md`, `docs/en/ConfigSystem.md`, `README.md`, `run.py`, `vlmeval/vlm/base.py`, `vlmeval/vlm/__init__.py`, `vlmeval/api/base.py`, `vlmeval/api/litellm_api.py`, `vlmeval/api/lmdeploy.py`, `vlmeval/api/openai_sdk.py`, `vlmeval/api/adapters/base.py`, `vlmeval/api/adapters/internvl2.py`, `vlmeval/api/adapters/internvl3.py`, `vlmeval/api/adapters/interns1_1.py`, `vlmeval/api/__init__.py`, `vlmeval/config.py`, and `tests/test_litellm_api.py`.
