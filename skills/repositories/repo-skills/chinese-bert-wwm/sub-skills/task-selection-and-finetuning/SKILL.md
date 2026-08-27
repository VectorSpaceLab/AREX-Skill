---
name: task-selection-and-finetuning
description: "Choose Chinese-BERT-wwm family models and fine-tuning strategy for
  Chinese downstream tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Task Selection and Fine-Tuning

Use this sub-skill when the user needs to choose an HFL Chinese whole-word-masked BERT-family model, set first-pass fine-tuning expectations, or diagnose benchmark/reproducibility confusion for Chinese downstream tasks.

## Use this when asked about

- Choosing among BERT-wwm, BERT-wwm-ext, RoBERTa-wwm-ext, RoBERTa-wwm-ext-large, RBT3, RBTL3, RBT4, or RBT6.
- Long-text Chinese reading comprehension, document classification, sentence matching, NLI, sentiment, or Traditional Chinese tasks such as DRCD.
- Whole Word Masking (WWM), Chinese word segmentation during pretraining, and whether downstream inputs must be segmented.
- Initial learning-rate choices, random-seed variation, batch-size effects, and interpreting max/average reported results.
- Whether additional pretraining is needed for a large domain shift.

## Start here

1. Read `references/selection-guide.md` to choose a model family by task, domain, resource budget, and evidence strength.
2. Read `references/fine-tuning-and-reproducibility.md` for the README learning-rate table, run-count assumptions, and reproduction cautions.
3. Read `references/troubleshooting.md` when the issue involves unexpected low scores, CWS misconceptions, RoBERTa naming/class confusion, or missing pretraining code.

## Immediate routing rules

- For code-level loading, model ids, tokenizer/model classes, offline cache checks, or PaddleHub module names, route to `../model-loading/SKILL.md`.
- For dataset file schemas, included zip archives, benchmark table details, metric definitions, or dataset copyright/download notes, route to `../data-and-benchmarks/SKILL.md`.
- For original pretraining implementation code, state the gap: this repository documents that pretraining code is not released. Do not invent a repository-specific pretraining command.

## High-confidence operating facts

- WWM changes pretraining sample construction, not downstream input requirements. Chinese CWS was used to decide which characters belong to the same word during pretraining; future downstream inputs do not need manual Chinese word segmentation solely because the checkpoint is WWM.
- The RoBERTa-wwm-ext names are RoBERTa-like training names for BERT-family models. They should be selected by benchmark/resource fit here, but loading details belong in `../model-loading/SKILL.md`.
- Initial learning rate must be tuned for the target task. The README table provides starting points, not guaranteed optima.
- Published benchmark numbers were reported over 10 runs with different random seeds using maximum and average scores; exact reproduction of the maximum is not expected.
