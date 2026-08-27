---
name: data-preparation
description: "Prepare DeepKE data for supervised formats, NER weak supervision,
  and RE distant supervision."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepKE data preparation

Use this sub-skill when a task asks to prepare or validate data before DeepKE supervised NER, RE, or AE training/prediction. It covers manual annotation schemas, doccano-style exports, conversion into DeepKE text/CSV formats, NER weak supervision from dictionaries, RE distant supervision from triples, train/dev/test split expectations, and data-prep failure diagnosis.

## Route by task

- **Manual annotation or doccano export planning**: read [references/data-formats.md](references/data-formats.md) for the span/relation fields DeepKE expects and [references/workflows.md](references/workflows.md) for when to annotate manually instead of auto-labeling.
- **Convert labeled JSON/DOCX/XLSX into DeepKE-ready files**: use [scripts/convert_supervised_data.py](scripts/convert_supervised_data.py). See [references/data-formats.md](references/data-formats.md) for accepted schemas and [references/troubleshooting.md](references/troubleshooting.md) before assuming offsets or labels are valid.
- **Prepare weakly supervised NER data from an entity dictionary**: use [scripts/prepare_weaksupervised_data.py](scripts/prepare_weaksupervised_data.py). See [references/workflows.md](references/workflows.md) for dictionary-matching trade-offs and split behavior.
- **Label RE examples from a triple table**: use [scripts/ds_label_data.py](scripts/ds_label_data.py). See [references/data-formats.md](references/data-formats.md) for source and triple schemas.
- **Debug bad or empty training data**: start with [references/troubleshooting.md](references/troubleshooting.md), then rerun the relevant bundled script with a tiny sample and stricter validation flags.

## What this sub-skill owns

- DeepKE standard NER `txt`, `json`, and `docx` preparation.
- DeepKE standard RE and AE-style `csv`, `json`, and `xlsx` conversion where the first row/object keys define the columns.
- Doccano sequence-labeling exports for NER and relation-labeling exports for RE schema planning.
- Dictionary-based NER weak supervision into BIO-tagged train/dev/test text files.
- Distant-supervision RE relation assignment from `(head, tail, relation)` triples.
- Validation gotchas that commonly produce unusable DeepKE datasets.

## What this sub-skill does not own

- Model architecture selection, Hydra config tuning, or running DeepKE training; route those to the supervised-extraction sub-skill.
- LLM instruction-data conversion; route LLM-specific data shaping to the llm-workflows sub-skill.
- Triple-extraction model output post-processing; route that to the triple-extraction sub-skill.
- Downloading large corpora, credentials, model checkpoints, or remote annotation services.

## Recommended order

1. Choose the workflow in [references/workflows.md](references/workflows.md).
2. Check the target schema in [references/data-formats.md](references/data-formats.md).
3. Run the smallest applicable bundled script command first.
4. Inspect split sizes, labels, offsets, and a few rendered BIO rows before using the data in training.
5. Use [references/troubleshooting.md](references/troubleshooting.md) for nonzero script failures or suspicious outputs.
