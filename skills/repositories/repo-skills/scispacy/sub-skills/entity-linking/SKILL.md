---
name: "entity-linking"
description: "Routes scispaCy candidate generation, knowledge-base loading, ANN
  index creation, and entity-linking workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Entity Linking

Use this sub-skill when the task is about scispaCy's knowledge-base and entity-linking stack rather than the tokenizer or project-data workflows.

## Typical triggers

- Build or debug `scispacy_linker`.
- Build an ANN index for a custom knowledge base.
- Load UMLS, MeSH, GO, HPO, or RxNorm knowledge bases.
- Inspect `CandidateGenerator` results or linker thresholds.
- Work with `KnowledgeBase`, `UmlsKnowledgeBase`, or UMLS semantic type trees.
- Handle `cached_path` downloads or linker cache issues.

## What belongs here

- Candidate generation and ANN index construction.
- Built-in and custom knowledge-base loading.
- UMLS semantic type tree helpers.
- Linker factory configuration and abbreviation-aware linking.
- Cache and remote-artifact behavior for KB/index downloads.

## What does not belong here

- Tokenization, sentence segmentation, abbreviation extraction, or hyponym detection. Use `pipeline-components`.
- MedMentions/BIO readers, NER evaluation, and package/workflow scripts. Use `project-workflows`.
- Package installation and model catalog details. Read the root installation reference.

## First things to read or run

- `references/api-reference.md` for verified signatures, defaults, and output shapes.
- `references/workflows.md` for building custom linkers and querying candidates.
- `references/troubleshooting.md` for cache, threshold, and `nmslib` issues.
- `../../scripts/smoke_scispacy.py` for the tiny linker smoke used to validate the environment.
- `scripts/build_linker_index.py` when you want a bundled helper to build a linker index from a local KB.

## Fast workflow summary

1. Decide whether you need a built-in KB (`umls`, `mesh`, `go`, `hpo`, or `rxnorm`) or a custom KB file.
2. Load or construct the KB.
3. Build a candidate index with `create_tfidf_ann_index` or a bundled wrapper.
4. Create the linker with `EntityLinker` or `EntityLinker.from_kb`.
5. If you want abbreviation-aware linking, add the abbreviation detector first.

## Example route decisions

- If the request says "link biomedical mentions to UMLS", stay here.
- If the request says "build an index from a JSONL knowledge base", stay here.
- If the request says "count token frequencies from corpus text", switch to `project-workflows`.
- If the request says "change how text is tokenized", switch to `pipeline-components`.

## Verification mindset

For this sub-skill, the strongest validation is a tiny linker smoke:

- `KnowledgeBase` can load a tiny local KB.
- `create_tfidf_ann_index(None, kb)` can build a candidate index.
- `CandidateGenerator` returns at least one candidate for a simple mention.
- `scispacy_linker` can resolve abbreviations when the abbreviation detector is already in the pipeline.

If that smoke fails, read the troubleshooting reference before attempting a large KB build or a remote download.
