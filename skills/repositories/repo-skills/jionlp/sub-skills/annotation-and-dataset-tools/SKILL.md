---
name: annotation-and-dataset-tools
description: "Convert between annotation formats, build lexicon NER, and split
  or batch labeled datasets."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Annotation and dataset tools

Use this sub-skill when the task is about labeled-text formats, sequence-tag conversion, lexicon NER, or batching and splitting annotated corpora.

## Include here
- NER / token conversion: `jio.ner.entity2tag`, `jio.ner.tag2entity`, `jio.ner.char2word`, `jio.ner.word2char`
- CWS conversion: `jio.cws.word2tag`, `jio.cws.tag2word`
- POS conversion: `jio.pos.pos2tag`, `jio.pos.tag2pos`
- `jio.ner.LexiconNER`
- `jio.ner.TokenSplitSentence`, `jio.ner.TokenBreakLongSentence`, `jio.ner.TokenBatchBucket`
- `jio.ner.analyse_dataset` for NER and `jio.text_classification.analyse_dataset` for text-classification corpora
- `jio.ner.collect_dataset_entities`
- `jio.ner.check_person_name`
- `jio.cws.f1` / `jio.ner.f1` helpers when comparing predictions to gold labels

## Exclude or route elsewhere
- Raw text cleanup or HTML stripping → `text-cleaning-and-extraction`
- Semantic parsing of time, money, location, or IDs → `parsing-and-normalization`
- Augmentation → `text-augmentation`
- Dictionary loaders and higher-level analytics → `dictionaries-and-language-analysis`

## What to read
- `references/api-reference.md` for data-format signatures and recoverable wrappers.
- `references/data-formats.md` for BIOES, BI, entity, and split-dataset shapes.
- `references/troubleshooting.md` for NumPy and tag-alignment issues.
- `scripts/smoke_annotation.py` for a fast validation run.

## Typical flow
1. Decide which annotation schema is in use.
2. Convert between entity and tag formats only when token boundaries are aligned.
3. Use the dataset split helper after labels are normalized.
4. Keep `max_sen_len` consistent across the NER batching wrappers.

## Quick cues
- Ask for this sub-skill when the user says "convert BIOES tags", "split the NER dataset", "build lexicon NER", "batch long sentences", or "count labeled entities".
- Stay here if the task is about annotation plumbing rather than raw text parsing.
