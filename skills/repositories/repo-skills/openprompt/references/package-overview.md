# OpenPrompt Package Overview

## Purpose

Read this when you need a fast map of the public OpenPrompt surface before choosing a sub-skill.

## Verified package facts

- Distribution: `openprompt`
- Verified version: `1.0.1`
- Core runtime stack used by the current skill build: PyTorch, Transformers, `sentencepiece`, `datasets`, `scikit-learn`, `scipy`, `rouge`, `tensorboardX`, `yacs`, `dill`, and `pyyaml`
- Root import pulls in the training/routing surface, so missing `torch`, `sklearn`, `rouge`, or `scipy` can break import even if `pip install openprompt` succeeded.

## Public top-level exports

`openprompt.__init__` exposes the package-usage surface most users ask about first:

- `PromptDataLoader`
- `PromptModel`
- `PromptForClassification`
- `PromptForGeneration`
- `Template`
- `Verbalizer`
- `ClassificationRunner`
- `GenerationRunner`
- `LMBFFClassificationRunner`
- `ProtoVerbClassificationRunner`

## Submodule map

- `openprompt.plms` — `load_plm`, `load_plm_from_config`, `get_model_class`, and tokenizer-wrapper selection.
- `openprompt.prompt_base` — the `Template` and `Verbalizer` base classes.
- `openprompt.prompts` — manual, mixed, soft, prefix, P-tuning, PTR, automatic, generation, knowledgeable, and prototypical prompt components.
- `openprompt.data_utils` — `InputExample`, `InputFeatures`, `FewShotSampler`, `load_dataset`, and the processor catalog.
- `openprompt.config` — `get_default_config`, `get_user_config`, `get_config`, and conditional-branch helpers.
- `openprompt.trainer` — the main classification and generation runners.
- `openprompt.lm_bff_trainer` / `openprompt.protoverb_trainer` — the specialized LM-BFF and ProtoVerb flows.

## Route guidance

- Use `pipeline-basics` for the minimal import/load pipeline.
- Use `template-verbalizer-design` for prompt grammar and prompt assets.
- Use `data-and-config-workflows` for YAMLs, processors, and few-shot sampling.
- Use `training-and-generation` for runners, checkpointing, and generation.

## Minimal smoke

Run the bundled script from the root skill directory:

```bash
python scripts/check_openprompt_install.py
```

It checks the published signatures, import path, and a fake-wrapper `PromptDataLoader` path without model or dataset downloads.
