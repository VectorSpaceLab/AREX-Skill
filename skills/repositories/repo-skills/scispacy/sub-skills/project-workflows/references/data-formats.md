# Data Formats

## Purpose

Use this when you need the exact input layout for scispaCy's data readers and conversion helpers.

## MedMentions directory layout

`read_full_med_mentions` expects the canonical MedMentions folder contents:

- `corpus_pubtator.txt`
- `corpus_pubtator_pmids_all.txt`
- `corpus_pubtator_pmids_dev.txt`
- `corpus_pubtator_pmids_test.txt`
- `corpus_pubtator_pmids_trng.txt`

The corpus file is parsed as PubTator-style sections:

- title line: `PMID | t | Title text`
- abstract line: `PMID | a | Abstract text`
- entity lines: `PMID<TAB>StartIndex<TAB>EndIndex<TAB>MentionText<TAB>SemanticTypeID<TAB>EntityID`

The helper removes overlap chains greedily and can optionally return spaCy-style `(text, {"entities": ...})` pairs or `MedMentionExample` records.

## BIO TSV layout

`read_ner_from_tsv` expects two tab-separated columns per token:

- column 1: token string
- column 2: BIO tag

Blank lines separate sentences. `-DOCSTART-` lines are ignored.

The returned examples are already tokenized as strings, so they pair naturally with `WhitespaceTokenizer` when you need to load them into a spaCy pipeline.

## Frequency-file layout

`convert_freqs.py` and the raw frequency counting helpers expect tab-separated rows of the form:

- `freq`
- `doc_freq`
- `key`

`key` is often a `repr`-style Python string literal. The converter uses `literal_eval` so it can recover the original token text.

## UMLS META layout

`export_umls_json.py` and the UMLS readers use the standard UMLS `META/` files:

- `MRCONSO.RRF` for concepts and aliases
- `MRSTY.RRF` for semantic types
- `MRDEF.RRF` for definitions
- `MRFILES.RRF` for column-name lookup

## Project workflow outputs

The project workflow convention uses these directories and generated artifacts:

- `project_data/` for converted spaCy corpora
- `output/` for trained model artifacts
- `packages/` for packaged model distributions and evaluation summaries

## Why this matters

Most scispaCy workflow failures are format mismatches rather than model bugs. If the reader or converter returns empty data, check the delimiter, blank-line structure, file names, or split IDs before changing the code.
