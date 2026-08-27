---
name: data-preparation
description: "Validate and prepare raw text-classification inputs, label
  dictionaries, n-gram expansions, and cache expectations for the legacy
  brightmart/text_classification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Preparation

Use this sub-skill when you need to validate or normalize repo-style text-classification data before a model-specific workflow runs.

This sub-skill is for the legacy TensorFlow 1.x / TFLearn code paths that back the generated repo skill. Its bundled helpers are plain Python 3.7-compatible scripts and do not require TensorFlow, but they must still respect the repo's older data conventions.

## Covers
- raw single-label lines: `text __label__label`
- raw multi-label lines with repeated or space-separated `__label__` markers
- prediction TSV rows: `question_id<TAB>text`
- relation / two-sentence rows: `text1<TAB>text2 __label__label`
- vocabulary and label dictionaries
- HDF5 cache keys and pickle tuple shapes
- adjacent n-gram expansion
- multi-hot labels and fixed top-label alignment
- seq2seq label shift tokens `_GO`, `_END`, `_PAD`

## Read first
- `references/data-formats.md`
- `references/workflows.md`
- `references/troubleshooting.md`

## Use the bundled scripts
- `scripts/validate_text_classification_data.py`
- `scripts/generate_ngrams.py`

## Do not use for
- model architecture selection
- training loop behavior
- ensemble/logit fusion
- downstream task choice outside data preparation
