---
name: chinese-bert-wwm
description: "Route Chinese-BERT-wwm model loading, model selection, benchmark
  data, and troubleshooting workflows for HFL Chinese BERT-family resources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chinese-BERT-wwm

Use this repo skill when a task involves HFL Chinese BERT/RoBERTa/RBT checkpoints released from the Chinese-BERT-wwm resource repository, Chinese Whole Word Masking (WWM), model loading through Transformers or PaddleHub, downstream Chinese NLP benchmark interpretation, or the bundled sentiment/NER dataset schemas.

## What this skill covers

- HFL model ids such as `hfl/chinese-bert-wwm`, `hfl/chinese-bert-wwm-ext`, `hfl/chinese-roberta-wwm-ext`, `hfl/chinese-roberta-wwm-ext-large`, `hfl/rbt3`, `hfl/rbt4`, `hfl/rbt6`, and `hfl/rbtl3`.
- Correct Transformers class choice: use `BertTokenizer`/`BertModel` or `AutoTokenizer`/`AutoModel`; do not use RoBERTa classes for the RoBERTa-wwm-named checkpoints.
- Offline/cache-aware model-id validation and optional online checkpoint loading decisions.
- Model selection and fine-tuning expectations for Chinese reading comprehension, sentiment, sentence-pair matching, NLI, document classification, and Traditional Chinese tasks.
- Dataset source pointers, copyright/download constraints, benchmark metrics, and schema validation for included ChnSentiCorp, Weibo, and PeopleDaily fixture archives.

## First steps

1. Read `references/model-family-overview.md` for the compact model catalog, WWM meaning, and route map.
2. If the task is about loading a checkpoint or validating a model id/cache, open `sub-skills/model-loading/SKILL.md`.
3. If the task is about choosing a model, learning rates, compact variants, WWM/CWS implications, or reproduction expectations, open `sub-skills/task-selection-and-finetuning/SKILL.md`.
4. If the task is about datasets, benchmark metrics, included zip schemas, or missing/copyright-restricted data, open `sub-skills/data-and-benchmarks/SKILL.md`.
5. For setup failures that span multiple workflows, open `references/troubleshooting.md`.

## Sub-skill routes

| User task | Read |
| --- | --- |
| "Load `hfl/chinese-roberta-wwm-ext` with Transformers", "is `RobertaTokenizer` correct?", "check offline cache for `hfl/rbt3`", "what PaddleHub module name should I use?" | `sub-skills/model-loading/SKILL.md` |
| "Which checkpoint should I fine-tune for CMRC/DRCD/XNLI/LCQMC?", "what LR did the README use?", "do I need Chinese word segmentation for WWM?", "should I use RBTL3 or truncate a large model?" | `sub-skills/task-selection-and-finetuning/SKILL.md` |
| "Where is BQ Corpus/LCQMC data?", "validate `chnsenticorp.zip`", "what metric does DRCD use?", "is CJRC test data official?" | `sub-skills/data-and-benchmarks/SKILL.md` |

## Minimal setup check

This repository is not an installable Python package. Transformers workflows require an environment with `transformers` and, for full model materialization, a backend such as PyTorch. In the user's chosen Python environment, a typical public setup is:

```bash
python -m pip install transformers torch
```

The root helper performs an offline import/model-id check and never downloads checkpoints:

```bash
python scripts/check_chinese_bert_wwm_setup.py --help
python scripts/check_chinese_bert_wwm_setup.py --require-transformers
python scripts/check_chinese_bert_wwm_setup.py --list-models
```

For model-specific cache/load checks, use `sub-skills/model-loading/scripts/check_transformers_model.py`. For included dataset archive schemas, use `sub-skills/data-and-benchmarks/scripts/validate_dataset_schema.py`.

## Key operating facts

- WWM is a pretraining data-construction strategy. It does not require manual word segmentation of downstream input text.
- The RoBERTa-wwm-ext models are RoBERTa-like BERT-family models. Load them as BERT models or through `Auto*` classes.
- TensorFlow checkpoint zip downloads and Hugging Face/PyTorch model directories are different file formats; choose the loading/conversion path explicitly.
- Published benchmark values are empirical references, often max/average over multiple runs, not guaranteed reproduction targets.
- Some dataset folders provide only source pointers due to copyright, large file size, or in-house test constraints. Do not create downloaders that bypass those constraints.

## Required references

- `references/repo-provenance.md`: source commit, evidence paths, package/library context, and refresh baseline.
- `references/repo-routing-metadata.json`: structured scenario metadata used if this verified skill is later imported into the managed repo-skill library.
- `references/model-family-overview.md`: shared model catalog and route map.
- `references/troubleshooting.md`: cross-cutting environment, cache, dataset, and reproducibility failures.

## Boundaries

This skill does not provide the unreleased original pretraining implementation, full model weights, full dataset downloads, PaddleHub/PaddlePaddle as required dependencies, or guaranteed benchmark reproduction. Ask for user approval before downloading large checkpoints, installing broad optional frameworks, using credentials, mutating caches, or redistributing restricted datasets.
