---
name: parsing-and-normalization
description: "Parse and normalize Chinese time, money, location, and related
  entity strings."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Parsing and normalization

Use this sub-skill when a string should be interpreted as a structured Chinese entity rather than just cleaned.

## Include here
- Time parsing and extraction: `parse_time`, `jio.ner.extract_time`
- Money parsing and extraction: `parse_money`, `jio.ner.extract_money`, `money_num2char`
- Location parsing and recognition: `parse_location`, `recognize_location`
- Phone attribution: `phone_location`, `cell_phone_location`, `landline_phone_location`
- Identity and plate parsing: `parse_id_card`, `extract_id_card`, `parse_motor_vehicle_licence_plate`, `extract_motor_vehicle_licence_plate`
- Character and idiom helpers: `pinyin`, `char_radical`, `idiom_solitaire`, `lunar2solar`, `solar2lunar`
- String-level parsers that depend on dictionary-backed semantics

## Exclude or route elsewhere
- Raw cleanup, replacement, or HTML stripping → `text-cleaning-and-extraction`
- Augmentation → `text-augmentation`
- BIO/BIOES conversion, lexicon NER, or dataset batching → `annotation-and-dataset-tools`
- Dictionary loaders and higher-level analytics → `dictionaries-and-language-analysis`

## What to read
- `references/api-reference.md` for signatures, return shapes, and edge notes.
- `references/troubleshooting.md` for noisy input, boundary, and ambiguity issues.
- `scripts/smoke_parsers.py` for a representative CPU-only smoke run.

## Typical flow
1. Remove obvious noise first if the input is a sentence, paragraph, or clause.
2. Choose the parser that matches the target structure.
3. Read the parsed result before chaining to other helpers.
4. Keep the parser-specific options visible when the input is ambiguous.

## Quick cues
- Ask for this sub-skill when the user says "parse this time string", "normalize this amount", "find the province/city", "get the pinyin", "convert lunar to solar", or "what is this car plate or ID card".
- Stay here if the task is semantic interpretation, not surface cleanup.
