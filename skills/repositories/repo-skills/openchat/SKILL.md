---
name: openchat
description: "Use OpenChat/ochat for prompt formatting, OpenAI-compatible
  serving, and benchmark evaluation of conversational LLMs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenChat repo skill

Use this skill when the task names OpenChat, `ochat`, `openchat_3.6`, `openchat_3.5`, C-RLFT prompt conditions, OpenChat's OpenAI-compatible server, or OpenChat benchmark/evaluation utilities.

## Quick routing

| User task | Read next |
| --- | --- |
| Choose a model type, serving alias, context length, prompt condition, EOT token, or Hugging Face chat-template behavior | [prompting](sub-skills/prompting/SKILL.md) |
| Build `Message`/`Conversation` objects or diagnose `ConversationTemplate.tokenize_conversations` weights and inference EOT placement | [prompting](sub-skills/prompting/SKILL.md) |
| Start or secure the OpenAI-compatible vLLM/FastAPI server, call `/v1/models` or `/v1/chat/completions`, or debug server request errors | [serving](sub-skills/serving/SKILL.md) |
| Run OpenChat benchmark evaluation, resume partial results, inspect answer matchers, or convert HumanEval outputs to EvalPlus JSONL | [evaluation](sub-skills/evaluation/SKILL.md) |
| Fix package import, CUDA, vLLM/Ray, tokenizer-cache, or broad dependency problems before using any workflow | [installation and backends](references/installation-and-backends.md) and [troubleshooting](references/troubleshooting.md) |

Training/data generation, DeepSpeed training loops, experimental notebooks, and model-embedding surgery scripts were intentionally excluded from this skill run. Do not route those tasks here unless this skill is refreshed or extended with that scope.

## Install and smoke check

OpenChat imports as `ochat`. A practical setup usually needs Python, PyTorch, Transformers, vLLM/Ray for serving/evaluation, and CUDA-capable hardware for local model serving. Read [installation and backends](references/installation-and-backends.md) before changing dependencies or deciding whether a CPU-only environment is enough.

Minimal no-download import check:

```bash
python scripts/check_openchat_import.py
```

CUDA/backends check:

```bash
python scripts/check_openchat_import.py --check-cuda
```

These scripts only inspect imports and device availability. They do not download model weights, start a server, call external APIs, or run benchmark suites.

## Core OpenChat concepts

- **Distribution/import**: the package distribution is `ochat`, and public modules live under `ochat.*`.
- **Model type**: canonical keys such as `openchat_3.6` and `openchat_v3.2_mistral` select a conversation template and max context.
- **Serving alias**: aliases such as `openchat_3.5` are accepted by the server after loading the canonical model type; they are not always keys in `MODEL_CONFIG_MAP`.
- **Condition**: strings such as `GPT4 Correct` and `Math Correct` are prompt-mode labels, not separate models.
- **Local runtime**: server and local benchmark inference use vLLM/Ray and require suitable model weights plus enough GPU memory.

## Evidence and freshness

Read [repo provenance](references/repo-provenance.md) before deciding whether this skill matches a current OpenChat checkout. If the source commit, tag, package version, public model registry, server CLI, or evaluation harness changed, run `refresh-repo-skill` rather than patching stale guidance manually.

## Useful bundled helpers

- [scripts/check_openchat_import.py](scripts/check_openchat_import.py) verifies core imports, model registry availability, optional serving/evaluation imports, and optional CUDA visibility.
- [prompting/scripts/check_prompting_smoke.py](sub-skills/prompting/scripts/check_prompting_smoke.py) runs deterministic prompt/tokenization logic checks without downloading real tokenizers.
- [serving/scripts/run_openchat_server.sh](sub-skills/serving/scripts/run_openchat_server.sh) safely forwards to the installed server module and refuses non-help launches without `--model`.
- [evaluation/scripts/run_eval.sh](sub-skills/evaluation/scripts/run_eval.sh) forwards to the installed evaluation harness.
- [evaluation/scripts/check_answer_matchers.py](sub-skills/evaluation/scripts/check_answer_matchers.py) runs tiny no-model checks for answer extraction behavior.
