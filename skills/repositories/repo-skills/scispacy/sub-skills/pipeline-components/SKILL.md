---
name: "pipeline-components"
description: "Routes scispaCy custom tokenizer, sentence segmentation,
  abbreviation detection, hyponym detection, and whitespace-tokenization
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipeline Components

Use this sub-skill when the task is about scispaCy's biomedical text-processing components rather than knowledge-base linking or project data workflows.

## Typical triggers

- Add or debug `abbreviation_detector`.
- Add or debug `hyponym_detector`.
- Replace spaCy's tokenizer with `combined_rule_tokenizer`.
- Use `pysbd_sentencizer` for sentence boundaries in biomedical text.
- Use `WhitespaceTokenizer` for pretokenized BIO-style inputs.
- Build or debug a biomedical pipeline around `en_core_sci_sm` or another scispaCy model.

## What belongs here

- Custom tokenization rules and punctuation handling.
- Sentence segmentation with `pysbd`.
- Abbreviation expansion and serialization.
- Hearst-pattern hyponym extraction.
- Whitespace tokenization for already tokenized text.
- The combined-rule model helper used in small pipeline smoke checks.

## What does not belong here

- Entity-linker / KB / ANN-index work. Use `entity-linking`.
- MedMentions readers, evaluation scripts, and UMLS export. Use `project-workflows`.
- Package installation and model catalog details. Read the root installation reference.

## First things to read or run

- `references/api-reference.md` for verified signatures, factory names, and extension attributes.
- `references/workflows.md` for concrete pipeline assembly patterns.
- `references/troubleshooting.md` for registration, serialization, and segmentation failures.
- `../../scripts/smoke_scispacy.py` when you need a quick install or component smoke.

## Fast workflow summary

1. Import the factory-registration modules once in the process:
   - `import scispacy.abbreviation`
   - `import scispacy.hyponym_detector`
2. Load a spaCy model such as `en_core_sci_sm` for biomedical text or `en_core_web_sm` for general-English tokenization checks.
3. Replace the tokenizer or add the sentence-segmentation pipe before downstream components if the text needs custom rules.
4. Add `abbreviation_detector` before `scispacy_linker` when the linker should resolve abbreviations.
5. Use `make_serializable=True` when the document must survive `to_bytes()` or multiprocessing.

## Example route decisions

- If the request says "make the tokenizer split biomedical hyphens correctly", stay here.
- If the request says "detect abbreviations and serialize the doc", stay here.
- If the request says "link entities to UMLS", switch to `entity-linking`.
- If the request says "evaluate NER on MedMentions", switch to `project-workflows`.

## Verification mindset

For this sub-skill, the strongest validation is a small pipeline smoke:

- `abbreviation_detector` finds the long form for a simple abbreviation pair.
- `hyponym_detector` finds a Hearst-pattern match such as `such_as`.
- `WhitespaceTokenizer` preserves pretokenized input.
- A combined pipeline can serialize when abbreviation detection is configured for serialization.

If one of those checks fails, read the troubleshooting reference before changing the broader environment.
