---
name: dictionaries-and-language-analysis
description: "Load packaged dictionaries and use JioNLP's keyphrase, summary,
  sentiment, new-word, BPE, and evaluation helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Dictionaries and language analysis

Use this sub-skill when the task is about packaged resources, corpus statistics, or higher-level language-analysis helpers built on top of JioNLP's dictionaries.

## Include here
- Packaged loaders for stopwords, locations, pinyin, radicals, distributions, sentiment words, quantifiers, and the LLM test set
- `jio.keyphrase.extract_keyphrase`, `jio.summary.extract_summary`, `jio.sentiment.LexiconSentiment`
- `jio.new_word.new_word_discovery`
- `jio.text_classification.analyse_freq_words`
- `jio.text_classification.analyse_dataset` when the task is about label distribution and class splits
- `jio.bpe.byte_level_bpe`
- `jio.mellm.MELLM`

## Exclude or route elsewhere
- Raw cleanup or extraction → `text-cleaning-and-extraction`
- Semantic parsing of time, money, location, or IDs → `parsing-and-normalization`
- Augmentation → `text-augmentation`
- CWS/POS/NER conversion and batching → `annotation-and-dataset-tools`

## What to read
- `references/api-reference.md` for the callable helpers.
- `references/loader-catalog.md` for packaged resource shapes.
- `references/llm-dataset.md` for the LLM test-set loader and MELLM notes.
- `references/troubleshooting.md` for packaged-data and network issues.
- `scripts/smoke_language_tools.py` for a safe smoke run.

## Typical flow
1. Load the packaged resource or sample corpus you need.
2. Decide whether the helper is frequency-based, topic-based, or evaluation-based.
3. For LLM evaluation, load the test dataset first and then wire the API callables.
4. Use the bundled smoke script to confirm the package resources are readable.

## Quick cues
- Ask for this sub-skill when the user says "load the dictionary", "extract keywords", "summarize this text", "score sentiment", "find new words", "use the LLM test set", or "run MELLM".
- Stay here if the task depends on packaged resources, topic statistics, or corpus-level language analysis.
