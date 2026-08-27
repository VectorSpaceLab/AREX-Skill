---
name: litgpt
description: "Use LitGPT to run local LLM inference, chat, finetuning,
  pretraining, checkpoint conversion, evaluation, and LitServe deployment with
  safe checks and workflow routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LitGPT Repo Skill

Use this skill when a user asks about LitGPT, the `litgpt` CLI, the `litgpt` Python package, local LLM generation, finetuning, pretraining, checkpoint conversion, evaluation, or serving. This root skill routes tasks to focused sub-skills and keeps long workflows self-contained.

## Install And Import Baseline

Public installation patterns:

```bash
pip install litgpt
pip install 'litgpt[extra]'
```

Use the base package for core CLI/API inspection and local checkpoint workflows. Use `litgpt[extra]` only when the user needs optional surfaces such as evaluation harness support, LitServe, dataset helpers, logging integrations, quantization, or tokenizer/model conversion extras.

Run the bundled environment check before relying on optional routes:

```bash
python scripts/check_litgpt_environment.py --json
```

Minimal import check:

```python
from litgpt import Config, GPT, LLM, Tokenizer
print(Config.from_name("pythia-14m").name)
```

## Route By Task

- `sub-skills/inference-chat/`: local generation, chat REPLs, Python `LLM.load` / `LLM.generate`, prompt styles, sampling, quantized inference, sequential/tensor-parallel generation, and offline generation planning.
- `sub-skills/training-data/`: `finetune_lora`, QLoRA, full finetuning, adapter/adapter_v2, pretraining, continued pretraining, JSON/JSONL SFT data, built-in data modules, config recipes, training args, resume/logging, and OOM-safe command construction.
- `sub-skills/checkpoint-conversion/`: `download`, `validate`, HF-to-LitGPT conversion, LitGPT-to-HF conversion, pretrained checkpoint export, LoRA merge, model config lookup, tokenizer/config layout, and checkpoint directory classification.
- `sub-skills/evaluation-serving/`: `evaluate`, LM Evaluation Harness task planning, result files, `serve`, LitServe simple/streaming/OpenAI-compatible endpoints, curl examples, and optional dependency checks.

## Common Routing Patterns

- If the user has a model name but no local files, start with `sub-skills/checkpoint-conversion/` for `litgpt download` and format decisions.
- If the user has a local checkpoint and wants text output, start with `sub-skills/inference-chat/` after a checkpoint layout check.
- If the user has training data or wants LoRA/QLoRA/full finetuning, start with `sub-skills/training-data/`, then return to checkpoint conversion for LoRA merge or to inference/evaluation for downstream use.
- If the user asks for benchmarks, `lm_eval`, HTTP endpoints, OpenAI-compatible requests, or streaming APIs, start with `sub-skills/evaluation-serving/`.
- If multiple workflows apply, validate checkpoint layout first, validate data second, and only then run expensive model loading, training, evaluation, or serving.

## Shared References

- `references/capability-map.md`: workflow-to-sub-skill routing, optional dependency ownership, and safe native verification candidates.
- `references/troubleshooting.md`: cross-cutting install/import, optional dependency, hardware, download, CLI config, data, checkpoint, and path failures.
- `references/repo-provenance.md`: source repository snapshot and refresh baseline for detecting stale skill content.
- `references/repo-routing-metadata.json`: structured routing metadata consumed by DisCo import tooling.

## Shared Script

- `scripts/check_litgpt_environment.py`: safe environment and optional dependency probe. It imports metadata and optional packages only; it does not download models, load weights, train, evaluate, or start a server.

## Safety Defaults

- Treat downloads, checkpoint conversion, training, evaluation, and serving as potentially expensive; ask before running them unless the user has already authorized a bounded run.
- Prefer help commands, bundled checkers, static layout validation, `--print_config`, tiny fixtures, and dry planning before running GPU/model workflows.
- Never expose access tokens in commands. Prefer environment variables or the user's secured credential mechanism.
- Avoid assuming CUDA, bitsandbytes, `lm_eval`, LitServe, Thunder, XLA, or logger integrations are installed. Check optional dependencies first.
- Runtime guidance in this skill is self-contained. Do not depend on the original source checkout for docs, tests, examples, or helper scripts.
