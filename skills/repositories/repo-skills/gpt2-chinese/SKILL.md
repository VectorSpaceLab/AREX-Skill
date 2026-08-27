---
name: "gpt2-chinese"
description: "Routes GPT2-Chinese training, generation, perplexity evaluation,
  and tokenizer or vocabulary workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GPT2-Chinese

Use this repo skill when the task is about the GPT2-Chinese repository or its Chinese GPT-2 workflows.

## Start here

- Read `references/repo-provenance.md` before deciding whether this skill matches the checkout you are using.
- Read `references/workflows.md` for the end-to-end training, evaluation, generation, and tokenizer flows.
- Read `references/cli-reference.md` for the exact CLI flags and default paths.
- Read `references/model-overview.md` when choosing a config file or vocabulary bundle.
- Run `scripts/check_install.py` after installing dependencies or when imports look suspicious.

## Install baseline

The repo is not packaged as a wheel. A typical working setup is:

1. Install a compatible PyTorch build for your machine.
2. Install the repo runtime dependencies from `requirements.txt`.
3. Add `tensorboard`, `sentencepiece`, and `scikit-learn` when they are missing.
4. Use the bundled smoke script to confirm the checkout can import and instantiate the tiny model.

See `references/troubleshooting.md` if `train.py --help` warns about missing optional packages, if `generate.py` cannot find a model directory, or if the word-level tokenizer cannot locate its dictionary.

## Routing

### Training and perplexity
Read `sub-skills/training/SKILL.md` when the user wants to:
- train from `train.json` or another JSON-list corpus
- use `--raw` preprocessing or the single-corpus training path
- resume from a checkpoint
- evaluate perplexity with `eval.py`
- reason about `output_dir`, `tokenized_data_path`, `log_step`, `gradient_accumulation`, or `fp16`

### Generation
Read `sub-skills/generation/SKILL.md` when the user wants to:
- generate text from a checkpoint
- compare `generate.py` and `generate_texts.py`
- choose `prefix`, `topk`, `topp`, `temperature`, or `fast_pattern`
- save samples to files or diagnose repeated or hanging generation

### Tokenizers and vocabulary
Read `sub-skills/tokenization/SKILL.md` when the user wants to:
- choose between char/BERT, word-level, or BPE tokenization
- build or replace a vocabulary file
- understand `cache/vocab_*.txt`, `tokenizations/*.py`, or the legacy vocabulary builder
- fix path-sensitive tokenizer or dictionary issues

## How to use the sub-skills

- Start with the narrowest sub-skill that matches the user request.
- If a request spans training plus generation, read the training sub-skill first and then the generation sub-skill.
- If the request includes vocabulary generation or tokenizer selection, read the tokenization sub-skill before training or generation so the config and vocabulary stay aligned.
- Use the bundled helper scripts rather than source-checkout paths when a workflow can be checked locally.
- Keep generated outputs inside the current checkout or the user-specified artifact area; do not put review or test artifacts inside this skill directory.
