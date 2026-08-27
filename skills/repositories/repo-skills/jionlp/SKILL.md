---
name: jionlp
description: "Chinese NLP preprocessing, parsing, augmentation, and
  language-analysis router for JioNLP."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# JioNLP

Use this skill when the task is about JioNLP's Chinese text preprocessing, rule extraction, parsing, augmentation, annotation helpers, or bundled language-analysis utilities.

## Quick start
- Install: `pip install jionlp`
- Import: `import jionlp as jio`
- Sanity check: `print(jio.__version__)`
- Search APIs interactively: `jio.help()` or `jio_help`
- For a silent smoke check, run `scripts/smoke_core.py`

Importing `jionlp` prints a banner and loads `jiojio`'s C helpers when available. That is expected.

## Route map

| User intent | Use this sub-skill |
| --- | --- |
| Clean raw text, strip URLs/emails/phones, normalize full-width chars, clean HTML, split sentences, read/write line files, or search docstrings | `sub-skills/text-cleaning-and-extraction/` |
| Parse or normalize time, money, location, phone, ID, vehicle plate, pinyin, radicals, idioms, or lunar/solar dates | `sub-skills/parsing-and-normalization/` |
| Augment text with back translation, character swaps, homophone substitution, random add/delete, or entity replacement | `sub-skills/text-augmentation/` |
| Convert NER/CWS/POS tags, build lexicon NER, split annotated datasets, or batch long NER inputs | `sub-skills/annotation-and-dataset-tools/` |
| Load packaged dictionaries, extract keyphrases or summaries, score sentiment, find new words, use BPE, load the LLM test set, or work with MELLM | `sub-skills/dictionaries-and-language-analysis/` |

## How to route quickly
- If the request starts with a noisy paragraph and asks to remove or detect obvious patterns, start with `text-cleaning-and-extraction`.
- If the request asks what a time string, money string, address, phone number, ID card, or plate means, start with `parsing-and-normalization`.
- If the request mentions augmentation, back translation, or replacing entities, start with `text-augmentation`.
- If the request mentions BIO/BIOES tags, entity offsets, CWS/POS conversion, or dataset splits, start with `annotation-and-dataset-tools`.
- If the request mentions loaders, keyphrase, summary, sentiment, new words, BPE, LLM test data, or MELLM, start with `dictionaries-and-language-analysis`.

## Practical notes
- `jio.help()` is interactive. Use `scripts/search_api_docs.py` if you want a noninteractive keyword search.
- `jio.bpe.byte_level_bpe` lives under the `bpe` submodule, not as a root attribute.
- Keyphrase, summary, new-word, NER time extraction, and text-classification helpers are exposed through submodules such as `jio.keyphrase`, `jio.summary`, `jio.new_word`, `jio.ner`, and `jio.text_classification`.
- A NumPy 1.x release older than 1.24 is required for the CWS/POS converters because this repository uses `np.unicode`.
- `phone_location()` is safer on text that contains a leading non-digit boundary before the phone number.
- `llm_test_dataset_loader()` expects version strings such as `'1.0'` or `'1.1'`.

## Read these first when needed
- `references/cli-reference.md` for `jio_help` and the bundled search wrapper.
- `references/troubleshooting.md` for import, NumPy, loader, and external-data issues.
- `scripts/smoke_core.py` for a fast import and sample-API smoke check.
