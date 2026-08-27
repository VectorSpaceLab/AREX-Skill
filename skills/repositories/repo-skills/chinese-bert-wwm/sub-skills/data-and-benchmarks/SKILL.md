---
name: data-and-benchmarks
description: "Interpret Chinese-BERT-wwm benchmark data sources, archive
  schemas, metrics, and dataset constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Benchmarks

Use this sub-skill when the task is about Chinese-BERT-wwm downstream datasets, published benchmark metrics, included fixture archive schemas, or why a dataset is missing from the repository resources.

## Trigger on

- "Where do I get CMRC/DRCD/XNLI/CJRC/LCQMC/BQ/THUCNews data?"
- "Validate `chnsenticorp.zip`, `weibo.zip`, or `peopledaily.zip`."
- "What metrics are reported in the Chinese-BERT-wwm benchmark table?"
- "Prepare sentiment, sentence-pair, reading-comprehension, NLI, document-classification, or NER data."
- "BQ Corpus or LCQMC is missing / not directly downloadable."

## Operating checklist

1. Identify the downstream task and dataset name, then open [references/dataset-reference.md](references/dataset-reference.md) for the source pointer, availability class, expected schema, and copyright note.
2. If the user has one of the supported fixture archives, run the bundled validator instead of guessing the split schema:
   ```bash
   python scripts/validate_dataset_schema.py --task chnsenticorp --archive <archive.zip> --max-rows 100
   python scripts/validate_dataset_schema.py --task weibo --archive <archive.zip> --max-rows 100
   python scripts/validate_dataset_schema.py --task peopledaily --archive <archive.zip> --max-rows 100
   ```
   Use `--max-rows 0` only when the user wants a full archive scan.
3. For benchmark questions, use [references/benchmark-reference.md](references/benchmark-reference.md). Treat reported values as empirical references from the repository's experiments, not guaranteed reproduction targets.
4. For missing data, cite the source pointer and constraint. Do not create downloader scripts, bypass copyright restrictions, or assume the full dataset is bundled.
5. For model IDs, tokenizer/model classes, checkpoint loading, or cache behavior, route to `../model-loading/SKILL.md`.
6. For model choice, learning-rate strategy, task adaptation, or fine-tuning recipes, route to `../task-selection-and-finetuning/SKILL.md`.

## Validator scope

The bundled `scripts/validate_dataset_schema.py` is offline-only and uses Python standard library modules. It validates zip member names and row-level schemas for:

- ChnSentiCorp: TSV members `train.tsv`, `dev.tsv`, `test.tsv`; header `label`, `text_a`; binary labels.
- Weibo: CSV members `train.csv`, `dev.csv`, `test.csv`; header `label`, `review`; binary labels.
- PeopleDaily: text members `train.txt`, `dev.txt`; rows `char TAG`, blank sentence separators, tags `O`, `B-*`, `I-*` for `PER`, `ORG`, and `LOC`.

For failure interpretation, fixes, and stop conditions, use [references/troubleshooting.md](references/troubleshooting.md).
