---
name: llm-foundry
description: "Use MosaicML LLM Foundry for LLM data preparation, Composer
  training and fine-tuning YAMLs, ICL evaluation, inference/export, registries,
  MPT/HF model configuration, and workflow troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LLM Foundry repo skill

Use this skill when a task is specifically about MosaicML **LLM Foundry** (`llm-foundry` / `llmfoundry`): preparing streaming LLM datasets, adapting Composer YAMLs for pretraining or fine-tuning, configuring in-context-learning evaluation, running inference/export helpers, inspecting package registries, or troubleshooting LLM Foundry installs and optional backends.

## First checks

1. Confirm the task is about LLM Foundry rather than generic Hugging Face, Composer, vLLM, SGLang, Axolotl, LlamaFactory, or another LLM framework.
2. Verify the installed package before relying on CLI/API behavior:

   ```bash
   python -c "from importlib.metadata import version; print(version('llm-foundry'))"
   python -c "import llmfoundry; print(llmfoundry.__version__)"
   llmfoundry --help
   ```

3. For a non-invasive package and backend check, run [scripts/check_llmfoundry_environment.py](scripts/check_llmfoundry_environment.py). It does not download models/data, train, evaluate, upload, or use credentials.
4. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout or whether `refresh-repo-skill` is needed.
5. For install/import, optional backend, credential, or large-run safety issues that cross workflows, read [references/troubleshooting.md](references/troubleshooting.md).

## Route by task

| User task | Read |
| --- | --- |
| Convert C4/Pile/JSON/raw text/fine-tuning data to MDS; validate JSONL prompt/response rows; plan StreamingDataset `remote`/`local`/`split`/cache fields; reason about Delta/Databricks export or contrastive pairs. | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| Create or adapt Composer YAMLs for pretraining, SFT/instruction fine-tuning, domain/sequence-length adaptation, callbacks/loggers/optimizers, checkpointing, resumption, MCLI training jobs, or bounded training smoke checks. | [sub-skills/training-finetuning/SKILL.md](sub-skills/training-finetuning/SKILL.md) |
| Configure `llmfoundry eval`, custom ICL task JSONL, Eval Gauntlet aggregation, API-wrapper evaluation, in-training eval hooks, or evaluation result interpretation. | [sub-skills/evaluation/SKILL.md](sub-skills/evaluation/SKILL.md) |
| Generate/chat with HF models, convert Composer checkpoints to HF folders, export ONNX, reason about FasterTransformer or endpoint generation prerequisites, or debug dtype/device/export/auth errors. | [sub-skills/inference-conversion/SKILL.md](sub-skills/inference-conversion/SKILL.md) |
| Inspect registries, MPT/HF model class signatures, tokenizers, callbacks, optimizers, schedulers, metrics, loggers, config transforms, optional package imports, or MosaicML platform/MCLI adaptation patterns. | [sub-skills/package-apis-configuration/SKILL.md](sub-skills/package-apis-configuration/SKILL.md) |

## Installation and backend posture

- Public install baseline:

  ```bash
  python -m pip install llm-foundry
  ```

  Use an editable install only for a local checkout or extension development.
- This skill's verified minimum operating scope is CPU/any package inspection plus safe CLI/help/static checks. A torch CUDA allocation was verified during construction, but advanced GPU stacks are intentionally not claimed as fully verified.
- Treat these as optional until the user explicitly needs them and the target environment proves them: `flash_attn`, TransformerEngine, MegaBlocks, FasterTransformer, ROCm, Intel Gaudi, multi-node distributed training/eval, MosaicML platform credentials, and private object-store/model credentials.
- For quick CPU/API work with MPT configs, prefer `attn_impl: torch`. Use `attn_impl: flash` only after flash-attn is installed for the exact torch/CUDA/Python/GPU stack.

## Common safe commands

```bash
# CLI discovery
llmfoundry --help
llmfoundry registry get --group models
llmfoundry data_prep --help
llmfoundry train --help
llmfoundry eval --help

# Skill-bundled checks, run from this generated skill directory
python scripts/check_llmfoundry_environment.py --json
python sub-skills/data-preparation/scripts/llmfoundry_data_prep_smoke.py --help
python sub-skills/training-finetuning/scripts/llmfoundry_config_probe.py --help
python sub-skills/evaluation/scripts/llmfoundry_eval_config_lint.py --help
python sub-skills/inference-conversion/scripts/llmfoundry_inference_smoke.py --help
python sub-skills/package-apis-configuration/scripts/llmfoundry_api_probe.py --help
```

## Safety rules

- Do not start training, evaluation, generation, conversion, Hub upload, endpoint calls, Databricks export, or object-store operations until model/data sizes, credentials, hardware, and budget are explicit.
- Keep secrets out of YAML examples and commands. Prefer environment variables or the platform's secret mechanism.
- Do not use CPU importability as proof of flash attention, TransformerEngine, MegaBlocks, FasterTransformer, distributed, or platform behavior.
- If a task is generic LLM usage with no LLM Foundry-specific CLI, config, registry, or data surface, choose a more appropriate generic LLM or framework skill instead.
