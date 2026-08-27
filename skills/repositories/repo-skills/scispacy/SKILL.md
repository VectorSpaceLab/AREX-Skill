---
name: "scispacy"
description: "Routes scispaCy biomedical spaCy component workflows,
  entity-linking workflows, and project data/evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# scispaCy

scispaCy is a biomedical/scientific spaCy package. Use this skill when you need to load its models, add its custom pipes, build entity linkers, or run the project data/evaluation helpers.

## Quick start

### Install the package

For general use:

```bash
python -m pip install scispacy
```

For development inside a local checkout:

```bash
python -m pip install -e .
```

### Install a model package

scispaCy models are installed separately from the library. Start with one of:

```bash
python -m spacy download en_core_web_sm
python -m pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz
```

See `references/installation.md` for the full model list and the known-good version pairing used in this checkout.

### Minimal import check

Use an isolated import check after installation:

```bash
python -I -c "import scispacy, spacy, scispacy.abbreviation, scispacy.hyponym_detector, scispacy.linking; print(scispacy.__version__)"
```

If you need a fuller smoke, run `scripts/smoke_scispacy.py`.

## Route map

### 1) Biomedical text-processing components

Use `sub-skills/pipeline-components/` for:

- `combined_rule_tokenizer`
- `pysbd_sentencizer`
- `abbreviation_detector`
- `hyponym_detector`
- `WhitespaceTokenizer`
- the combined-rule pipeline helper

This route is the right one when the task is about tokenization, sentence boundaries, abbreviation expansion, or Hearst-pattern hyponym extraction.

### 2) Entity linking and knowledge bases

Use `sub-skills/entity-linking/` for:

- `scispacy_linker`
- `CandidateGenerator`
- `KnowledgeBase` and the built-in KB subclasses
- `create_tfidf_ann_index`
- UMLS semantic-type helpers and cache-backed KB loading

This route is the right one when the task is about UMLS/MeSH/GO/HPO/RxNorm linking, custom KBs, candidate generation, or ANN index creation.

### 3) Project data and evaluation workflows

Use `sub-skills/project-workflows/` for:

- MedMentions and BIO TSV readers
- NER evaluation helpers
- UMLS export to JSONL
- frequency counting / vocabulary conversion
- package metrics summaries
- `project.yml` / `configs/*.cfg` workflow assembly

This route is the right one when the task is about training-data conversion, evaluation, or model packaging rather than the runtime pipes.

## Shared references

- Read `references/installation.md` when you need install commands, model selection, or the verified version pairing.
- Read `references/troubleshooting.md` when install, import, or model-version problems appear.
- Read `references/repo-provenance.md` when checking whether this skill is still aligned with the current repository.
- Read `references/repo-routing-metadata.json` when you need the router metadata used during import and discovery.

## Shared helper scripts

- Run `scripts/smoke_scispacy.py` to check the installed package, biomedical components, whitespace tokenization, and a tiny linker path.

## Practical selection guidance

- If the request names tokenization, sentence splitting, abbreviation detection, or hyponym detection, stay in `pipeline-components`.
- If the request names `scispacy_linker`, KBs, ANN indices, UMLS, or a linker threshold, stay in `entity-linking`.
- If the request names MedMentions, BIO TSV, `project.yml`, `evaluate_ner`, `export_umls_json`, or frequency conversion, stay in `project-workflows`.
- If the request is only about installing the library or choosing a model package, start with `references/installation.md` and the smoke script.

## Freshness check

Use `references/repo-provenance.md` to confirm the checkout and package snapshot before treating this skill as current for a different repository state.
