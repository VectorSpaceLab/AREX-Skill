---
name: text-cleaning-and-extraction
description: "Clean raw Chinese text, extract obvious patterns, and normalize
  noisy strings."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Text cleaning and extraction

Use this sub-skill for raw text cleanup, pattern extraction, replacement, sentence splitting, and file-line helpers.

## Include here
- `clean_text`, `clean_html`, `remove_html_tag`, `remove_exception_char`, `remove_redundant_char`, `convert_full2half`
- `extract_*`, `remove_*`, and `replace_*` helpers for email, URL, phone, IP, ID card, QQ, Chinese chars, parentheses, and vehicle plates
- `check_any_chinese_char`, `check_all_chinese_char`, `check_any_arabic_num`, `check_all_arabic_num`
- `split_sentence`
- `remove_stopwords` after tokenization
- `read_file_by_iter`, `read_file_by_line`, `write_file_by_line`, `TimeIt`, `zip_file`, `unzip_file`
- `jio.help()` discovery support

## Exclude or route elsewhere
- Semantic parsing of time, money, location, phone attribution, ID detail, plate interpretation, pinyin, radical, or idiom logic → `parsing-and-normalization`
- Data augmentation → `text-augmentation`
- Tag conversion, lexicon NER, dataset splits, or batching helpers → `annotation-and-dataset-tools`
- Dictionary loaders and higher-level language analysis → `dictionaries-and-language-analysis`

## What to read
- `references/api-reference.md` for exact function groups and return shapes.
- `references/troubleshooting.md` for boundary, HTML, file, and pattern-matching issues.
- `scripts/smoke_text_cleaning.py` for a fast validation run.

## Typical flow
1. Clean or normalize the text before any deeper parsing.
2. Extract or replace obvious entities.
3. Split or filter token lists only after tokenization.
4. Use the file helpers when the task is line-oriented data or temporary fixtures.

## Quick cues
- Ask for this sub-skill when the user says "remove URLs", "mask emails", "clean HTML", "full-width to half-width", "split sentences", or "search docs by keyword".
- Stay here if the task is only about surface text cleanup and not semantic interpretation.
