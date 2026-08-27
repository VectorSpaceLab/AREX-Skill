# Data Preparation for Stanza Training

## When to read

Read this before creating training data or converting corpora for Stanza models. Most preparation steps are file-format work; run them on tiny fixtures first and only then on full corpora.

## Directory and environment model

Stanza's training helpers expect task-specific roots. The bundled `scripts/config_template.sh` names the common variables:

- `UDBASE`: Universal Dependencies treebanks in CoNLL-U format.
- `NERBASE`: NER source data root; many converters emit BIO/BIOES-style files.
- `CONSTITUENCY_BASE`: source treebank root for constituency conversion.
- `DATA_ROOT`: common output root for prepared task data.
- `TOKENIZE_DATA_DIR`, `MWT_DATA_DIR`, `LEMMA_DATA_DIR`, `POS_DATA_DIR`, `DEPPARSE_DATA_DIR`, `NER_DATA_DIR`, `CHARLM_DATA_DIR`, `CONSTITUENCY_DATA_DIR`, `SENTIMENT_DATA_DIR`: per-task prepared data outputs.
- `WORDVEC_DIR`: external word vector root when training uses raw vectors instead of prebuilt Stanza pretrains.

Do not export placeholder values. Replace every placeholder with an explicit working directory, preferably outside the installed package and under a task-owned output root.

## Format families

### CoNLL-U / Universal Dependencies

Used by tokenizer, MWT, POS/morphology, lemma, dependency parsing, and many pipeline tests.

Checklist:

1. Validate 10 CoNLL-U columns and blank-line sentence boundaries.
2. Preserve `# sent_id`, `# text`, and `# doc_id` comments when they carry corpus semantics.
3. Keep train/dev/test splits separate before running any training wrapper.
4. Use `documents-and-conllu/scripts/validate_conllu.py` for a no-network structural check.
5. Confirm treebank short names match Stanza's expected `lang_treebank` form, such as `en_ewt`.

### Tokenizer labels and MWT JSON

Tokenizer training uses plain text plus character-level label files. MWT expansion data is passed as JSON where needed.

Checks:

- `--txt_file` and `--label_file` must describe the same text stream.
- `--dev_txt_file` and `--dev_label_file` must exist for training.
- Use `--mwt_json_file` when the tokenizer should output MWT expansions.
- For languages with dictionary features, make sure the external dictionary file name follows the expected shorthand convention.

### NER BIO / BIOES / BEIOS

NER conversion utilities handle multiple public corpora and schemes.

Checks:

- Decide the scheme before training (`--scheme`, `--train_scheme`).
- Convert or normalize mixed schemes before training; do not mix BIO and BIOES silently.
- Validate that every token has the expected number of tag columns when using multi-tag NER.
- Keep evaluation output separate via explicit output paths.

### Constituency trees

Constituency workflows expect bracketed trees or converted datasets, depending on language/corpus.

Checks:

- Run converter logic on a tiny fixture before processing full corpora.
- Preserve tree labels expected by the selected parser.
- If retagging is needed, plan the dependent POS/tokenization pipeline separately.

### Coref and classifier data

Coref and classification workflows are more experiment/config driven.

Checks:

- Keep config files, input data, weights, and output files separate.
- Avoid enabling W&B, remote downloads, or large transformer finetuning without explicit approval.
- For coref, confirm split names (`train`, `dev`, `test`) and batch/length limits.

## Pretrains, charlms, and word vectors

Stanza models often depend on pretrained word vectors and character language models.

- Prefer explicit `--wordvec_pretrain_file` when a prebuilt `.pt` exists.
- If relying on default download logic, document that it may download resources.
- Stanza's original large word-vector download workflow is intentionally not bundled because it performs large external downloads and file mutations. If you need word vectors, make an operator-approved download plan with target size, URL, and checksum expectations.
- Use `--no_charlm` or model-family equivalents when you need a no-download, no-charlm baseline.

## Safe preparation pattern

1. Create a small fixture under a scratch output root.
2. Run the relevant converter/helper in dry-run or `--help` form first.
3. Validate outputs with CoNLL or scheme-specific checks.
4. Only then run the full conversion.
5. Capture data source, command, package version, and output layout in your task notes.
