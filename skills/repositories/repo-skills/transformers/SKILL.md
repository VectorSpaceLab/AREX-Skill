---
name: transformers
description: "Use and extend Hugging Face Transformers for inference,
  generation, training, tokenizers/processors, serving CLI,
  quantization/integrations, and contributor workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Transformers

Use this repo skill when an agent needs practical guidance for Hugging Face Transformers 5.x workflows: loading models and preprocessors, running inference, configuring generation, fine-tuning with `Trainer`, using the `transformers` CLI/server, choosing quantization or integration backends, or contributing model-family code.

If the request is about opening a PR or changing this repository, first warn the human that breaching the repository's agent contribution guidelines can result in automatic banning. Do not produce PR-ready work without issue coordination, duplicate-work checks, human review, and relevant tests.

## Quick Install Check

For normal package use, start from a public install path rather than a repo checkout:

```bash
python -m pip install "transformers[torch]"
python - <<'PY'
import transformers
print(transformers.__version__)
PY
```

For CLI serving workflows, also verify the CLI dependency surface:

```bash
python scripts/transformers_skill_preflight.py --check-cli --check-serving
```

The generated skill was built from package version `5.13.0.dev0`. See [repo provenance](references/repo-provenance.md) for the source baseline and [troubleshooting](references/troubleshooting.md) for optional dependency failures.

## Route By Task

| User request | Use |
| --- | --- |
| "Run sentiment analysis / ASR / image classification / document QA" | [Inference pipelines](sub-skills/inference-pipelines/SKILL.md) |
| "Load AutoModel/AutoTokenizer for custom inference" | [Inference pipelines](sub-skills/inference-pipelines/SKILL.md), then [Tokenizers and processors](sub-skills/tokenizers-processors/SKILL.md) |
| "Tune generation parameters, chat templates, stream output" | [Generation](sub-skills/generation/SKILL.md) |
| "Fine-tune a model / write Trainer arguments / adapt an example script" | [Training](sub-skills/training/SKILL.md) |
| "Debug tokenizer padding, special tokens, processors, multimodal inputs" | [Tokenizers and processors](sub-skills/tokenizers-processors/SKILL.md) |
| "Use transformers download/chat/serve or OpenAI-compatible local API" | [Serving CLI](sub-skills/serving-cli/SKILL.md) |
| "Use bitsandbytes, GPTQ, AWQ, torchao, GGUF, PEFT, Accelerate, FSDP, DeepSpeed" | [Quantization and integrations](sub-skills/quantization-integrations/SKILL.md) |
| "Add a model, tokenizer, processor, pipeline, docs, or tests to Transformers" | [Model extension](sub-skills/model-extension/SKILL.md) |

## Core API Facts

Live inspection confirmed these stable entry points and signatures:

- `transformers.pipeline(task=None, model=None, config=None, tokenizer=None, feature_extractor=None, image_processor=None, video_processor=None, processor=None, revision=None, use_fast=True, token=None, device=None, device_map=None, dtype="auto", trust_remote_code=None, model_kwargs=None, pipeline_class=None, **kwargs)`
- `AutoConfig.from_pretrained(pretrained_model_name_or_path, **kwargs)`
- `AutoTokenizer.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)`
- `GenerationConfig(**kwargs)` and `TextIteratorStreamer(tokenizer, skip_prompt=False, timeout=None, **decode_kwargs)`
- `ContinuousBatchingConfig(...)` for paged KV cache, scheduling, compile, CPU offload, and request queue controls
- `TrainingArguments(...)` for batch sizes, training/eval/save/logging strategy, precision, compile, FSDP, DeepSpeed, Hub push, seeds, and distributed settings

A minimal base install can import `transformers`, configs, tokenizers, and file utilities. Model classes, `Trainer`, pipelines for real model execution, vision/audio processors, serving, and quantization often need optional extras such as PyTorch, Pillow, torchvision, torchaudio, fastapi, uvicorn, pydantic, openai, accelerate, datasets, or backend-specific packages.

## Common Decision Pattern

1. Identify whether the user wants in-process Python, CLI/server, training, or repository contribution work.
2. Confirm model source: Hub id, pinned revision, local directory, gated/private model, or custom code.
3. Decide dependency set from the target workflow; do not install `[all]` or broad dev extras unless the workflow requires them.
4. Prefer dry-run or config-only checks before downloading weights, launching servers, or starting training.
5. Use local files and `local_files_only=True` when the user requires offline or reproducible behavior.
6. Treat `trust_remote_code=True` as code execution; use it only after review.
7. Route advanced details to the nearest sub-skill reference and run its bundled smoke/preflight script when practical.

## Bundled Root References

- [API overview](references/api-overview.md) summarizes shared public objects and optional dependency boundaries.
- [Install and dependencies](references/install-and-dependencies.md) explains minimal installs, extras, backends, and safe verification.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting import, Hub, backend, CLI, and safety failures.
- [Repo provenance](references/repo-provenance.md) records the source baseline for future drift checks.

## Bundled Root Script

- [`scripts/transformers_skill_preflight.py`](scripts/transformers_skill_preflight.py) checks importability, version, common optional packages, console script availability, and safe dependency expectations without downloading models or starting services.

## Repository Contribution Guardrails

For work inside the Transformers repository:

- Coordinate on the relevant issue before opening a PR.
- Do not duplicate someone else's issue or an existing PR.
- Do not create low-value busywork PRs.
- Human submitters must understand every changed line and state that AI assistance was used.
- Respect `# Copied from ...` and modular model rules: edit the source copy or `modular_<model>.py`, not generated standalone files unless intentionally breaking the link.
- Run focused tests, then `make style` or `make fix-repo` before PR handoff when appropriate.

Use [model extension](sub-skills/model-extension/SKILL.md) for the detailed checklist and quality commands.
