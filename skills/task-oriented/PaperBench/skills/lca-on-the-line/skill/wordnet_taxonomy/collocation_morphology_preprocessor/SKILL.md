---
name: collocation_morphology_preprocessor
description: Preprocess English text with WordNet-style collocation matching, tokenization, and inflectional normalization.
---

# Collocation and Morphology Preprocessor

Use this skill when a recovery or application needs the preprocessing behavior described in the WordNet report: one sentence per line, WordNet collocation search, tokenization, part-of-speech hints, and morphology-aware lookup forms.

## Inputs
- Raw English text.
- A list of known collocations, using spaces or underscores.

## Outputs
- Sentence records with original text, token records, normalized lemmas, POS hints, and collocation spans.

## Workflow
1. Split bounded text into sentence records.
2. Lowercase and remove punctuation for matching while preserving original sentence text.
3. Greedily match known collocations before single-token normalization.
4. Normalize regular plurals and common `-ing` or `-ed` inflections.
5. Emit unknown tokens rather than dropping them, because the ConText-style tagger must record unresolved reasons.

## Validation
Run `python tests/test_preprocessor.py` or the Distiller skill-tree validator with tests enabled.

## Limitations
The POS hints are deterministic and lightweight. They are sufficient for reduced recovery but not a replacement for a full part-of-speech tagger.
