# Model Family Overview

## Purpose

Read this reference when you need a compact, self-contained overview of what the Chinese-BERT-wwm repository provides before routing to a sub-skill. It summarizes the public model family, supported loading surfaces, task evidence, and scope limits.

## What this repository is

Chinese-BERT-wwm is a model and dataset-resource repository for HFL Chinese BERT-family checkpoints trained with Whole Word Masking (WWM). It is not an installable Python package and does not bundle executable fine-tuning or pretraining code. The operational APIs are external public libraries such as Hugging Face Transformers and, optionally, PaddleHub.

WWM changes pretraining sample construction: when one subword/character belonging to a segmented word is selected for masking, the other pieces in that word are masked together. For Chinese, word boundaries were produced by Chinese Word Segmentation during pretraining-data construction. Downstream inference and fine-tuning inputs do not need manual segmentation solely because the checkpoint is WWM.

## Released model identifiers

| Human model name | Hugging Face id | PaddleHub module | Main use |
| --- | --- | --- | --- |
| BERT-wwm | `hfl/chinese-bert-wwm` | `chinese-bert-wwm` | Conservative WWM replacement for original Chinese BERT; formal and Traditional Chinese-compatible workflows. |
| BERT-wwm-ext | `hfl/chinese-bert-wwm-ext` | `chinese-bert-wwm-ext` | Base-size WWM model trained on larger extended Chinese data. |
| RoBERTa-wwm-ext | `hfl/chinese-roberta-wwm-ext` | `chinese-roberta-wwm-ext` | Strong base-size RoBERTa-like BERT-family model. |
| RoBERTa-wwm-ext-large | `hfl/chinese-roberta-wwm-ext-large` | `chinese-roberta-wwm-ext-large` | Accuracy-first large model when memory and latency allow. |
| RBT3 | `hfl/rbt3` | `rbt3` | Compact 3-layer model for memory/latency-sensitive tasks. |
| RBT4 | `hfl/rbt4` | not listed in the PaddleHub quick-load table | Intermediate compact checkpoint; validate task performance yourself. |
| RBT6 | `hfl/rbt6` | not listed in the PaddleHub quick-load table | Intermediate compact checkpoint; validate task performance yourself. |
| RBTL3 | `hfl/rbtl3` | `rbtl3` | Compact 3-layer model derived from the large family, stronger than naive truncation. |

Despite the `RoBERTa` names, the repository's loading contract says all listed models use BERT-family loading: `BertTokenizer` and `BertModel`, or `AutoTokenizer` and `AutoModel`. Do not use `RobertaTokenizer` or `RobertaModel` for these identifiers.

## Main operating routes

- Use `sub-skills/model-loading/SKILL.md` for model id normalization, Transformers/PaddleHub loading, offline cache checks, TensorFlow checkpoint versus PyTorch/Hugging Face file decisions, and class-mismatch troubleshooting.
- Use `sub-skills/task-selection-and-finetuning/SKILL.md` for model-family selection, WWM interpretation, learning-rate starting points, compact model tradeoffs, Traditional Chinese advice, and reproducibility expectations.
- Use `sub-skills/data-and-benchmarks/SKILL.md` for dataset source pointers, included zip schemas, benchmark metrics, copyright/download constraints, and local schema validation.

## Public evidence scope

The generated skill distilled:

- Chinese and English repository documentation for model catalogs, loading snippets, model-comparison tables, baseline metrics, useful tips, FAQ, citation, and disclaimers.
- Dataset README files for source pointers and copyright/download constraints.
- Included fixture archives for ChnSentiCorp, Weibo sentiment, and PeopleDaily NER schemas.
- Runtime inspection of Transformers/PyTorch imports and loading API signatures.

The generated skill intentionally does not include:

- Original pretraining code, because the FAQ says it is not released.
- Full checkpoint files or dataset downloads.
- PaddleHub/PaddlePaddle installation as a required dependency.
- Guaranteed reproduction targets for benchmark maxima.

## Quick setup check

For a local Python environment, the root helper verifies Transformers/Torch imports and prints the supported model-id map without downloading checkpoints:

```bash
python scripts/check_chinese_bert_wwm_setup.py --help
python scripts/check_chinese_bert_wwm_setup.py --require-transformers
python scripts/check_chinese_bert_wwm_setup.py --list-models
```

For model-specific cache checks, use `sub-skills/model-loading/scripts/check_transformers_model.py`.
