---
name: "project-workflows"
description: "Routes scispaCy data conversion, evaluation, UMLS export, and
  project.yml-driven packaging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Project Workflows

Use this sub-skill when the task is about scispaCy's data readers, evaluation helpers, or project-yml/config-driven workflow assembly rather than the core pipeline or linker APIs.

## Typical triggers

- Convert word-frequency files into spaCy vocabulary JSONL.
- Count token frequencies from a raw corpus.
- Evaluate NER predictions on MedMentions or TSV data.
- Export UMLS META files to JSONL.
- Summarize packaged model metrics.
- Understand or tweak `project.yml`, `configs/*.cfg`, `base_project_code.py`, or the custom spaCy registries.

## What belongs here

- Frequency counting and vocabulary conversion helpers.
- MedMentions and BIO TSV readers.
- NER evaluation and per-class scoring.
- UMLS export and package-metrics reporting.
- Config-driven workflow names, reader callbacks, and spaCy registry entries.

## What does not belong here

- Tokenization, sentence segmentation, abbreviation handling, or hyponym detection. Use `pipeline-components`.
- ANN candidate generation or KB construction. Use `entity-linking`.
- General package installation/model catalog questions. Read the root installation reference.

## First things to read or run

- `references/api-reference.md` for registered readers/callbacks and scoring helpers.
- `references/data-formats.md` for MedMentions, BIO TSV, frequency-file, and UMLS META layouts.
- `references/workflows.md` for the command-level workflows.
- `references/troubleshooting.md` for malformed data, stale helpers, and evaluation issues.
- `scripts/convert_freqs.py`, `scripts/count_word_frequencies.py`, `scripts/evaluate_ner.py`, `scripts/export_umls_json.py`, and `scripts/print_out_metrics.py` for reusable helpers.

## Fast workflow summary

1. Identify the input format: raw corpus text, BIO TSV, MedMentions, UMLS META, or package metrics JSON.
2. Choose the bundled helper that matches the format.
3. Keep large downloads and long training runs explicit; these workflows are often maintenance-oriented and may require external data.
4. Use the distilled workflow matrix in `references/workflows.md` when you need to understand how the package builds the small, medium, large, scibert, or specialized NER workflows.

## Example route decisions

- If the request says "convert frequency counts into spaCy vocab JSONL", stay here.
- If the request says "evaluate a model on MedMentions", stay here.
- If the request says "change how the tokenizer splits biomedical abbreviations", switch to `pipeline-components`.
- If the request says "build a custom linker from a KB", switch to `entity-linking`.

## Verification mindset

For this sub-skill, the strongest validation is a safe, fixture-backed workflow:

- `convert_freqs.py` can transform a tiny frequency file.
- `count_word_frequencies.py` can process a small raw-corpus directory.
- `read_full_med_mentions` and `read_ner_from_tsv` parse the expected layouts.
- `evaluate_ner` and `PerClassScorer` compute the expected metrics on a tiny fixture.

If one of those checks fails, read the troubleshooting reference before launching a full corpus conversion or a long evaluation run.
