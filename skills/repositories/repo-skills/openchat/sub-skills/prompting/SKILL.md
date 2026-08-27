---
name: prompting
description: "Format OpenChat conversations, choose model types and aliases, and
  troubleshoot prompt tokenization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenChat prompting

Use this sub-skill when the task is to format OpenChat chat turns, choose the correct model configuration key, choose or override an OpenChat condition, or diagnose tokenization/weight mismatches around `Message`, `Conversation`, and `ConversationTemplate.tokenize_conversations`.

## Start here

- Need to choose a `model_type`, understand a serving alias, or confirm context length? Read [model-overview](references/model-overview.md).
- Need to construct conversations or compare training and inference tokenization? Read [conversation-format](references/conversation-format.md).
- Need to debug mismatched tokens, missing weights, system prompts, EOT, or tokenizer cache behavior? Read [troubleshooting](references/troubleshooting.md).
- Need a deterministic no-download sanity check for the prompting API? Run `python scripts/check_prompting_smoke.py --help`, then `python scripts/check_prompting_smoke.py`.

## Operating checklist

1. Separate three names before formatting anything: weight repository/path, canonical `MODEL_CONFIG_MAP` key, and serving request alias.
2. Build OpenChat data with `Message(role, content, weight=None)` and `Conversation(items, condition="", system="")`; put system text in `Conversation.system`, not as a normal message item unless a specific workflow says otherwise.
3. Pick the condition deliberately. Empty inference uses the template's default condition; training does not. Use `Math Correct` only when that prompt mode is intended.
4. For training tokenization, every message needs `weight`; for inference tokenization, weights are ignored and the last turn intentionally has no EOT token.
5. Treat special tokens and EOT as tokenizer/model compatibility requirements, not prompt decoration.

## Boundaries

This sub-skill covers prompting and model-configuration behavior only. For launching the API server, request schemas, Ray/vLLM settings, or Docker deployment, use [serving](../serving/SKILL.md). For benchmark/evaluation command workflows and answer matching, use [evaluation](../evaluation/SKILL.md). Training, data generation, experimental notebooks, and model surgery are out of scope here.

## Evidence used

Distilled from these OpenChat source evidence paths: `README.md`, `pyproject.toml`, `ochat/config/__init__.py`, `ochat/config/conversation_template.py`, `ochat/config/model_config.py`, `ochat/serving/async_tokenizer.py`, `ochat/serving/openai_api_protocol.py`, `ochat/serving/openai_api_server.py`, `ochat/evaluation/run_eval.py`, `ochat/tests/test_model_config.py`, and `docker/serving/*` as deployment reference only. Verified package facts include `ochat` 3.6.1, serving/evaluation CLI availability, and import availability for CUDA/vLLM/Ray-dependent surfaces.
