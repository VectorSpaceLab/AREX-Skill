---
name: text-augmentation
description: "Augment Chinese text with translation, swaps, homophones, random
  edits, or entity replacement."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Text augmentation

Use this sub-skill when the task is about generating plausible alternate training examples rather than parsing or cleaning text.

## Include here
- `BackTranslation` and the translation API wrappers: `BaiduApi`, `YoudaoFreeApi`, `YoudaoApi`, `GoogleApi`, `TencentApi`, `XunfeiApi`
- `SwapCharPosition`
- `HomophoneSubstitution`
- `RandomAddDelete`
- `ReplaceEntity`

## Exclude or route elsewhere
- Raw cleanup or extraction → `text-cleaning-and-extraction`
- Semantic parsing or normalization → `parsing-and-normalization`
- Tag conversion or dataset batching → `annotation-and-dataset-tools`
- Dictionary loaders and higher-level analytics → `dictionaries-and-language-analysis`

## What to read
- `references/api-reference.md` for constructor signatures and expected input shape.
- `references/troubleshooting.md` for network, credential, and offset issues.
- `scripts/smoke_augmentation.py` for a safe local-only smoke run.

## Typical flow
1. Decide whether the augmentation is local and deterministic or network-backed.
2. For local augmenters, fix the seed before generating a small batch.
3. For entity replacement, keep offsets and entity ordering consistent.
4. For back translation, prepare real translation API credentials before running.

## Quick cues
- Ask for this sub-skill when the user says "augment this text", "make more training examples", "swap nearby characters", "replace entities", or "back translate".
- Keep `BackTranslation` separate from the local augmenters when keys or network access are not available.
