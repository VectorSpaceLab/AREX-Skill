# Training Data Formats

## When to read

Read this before preparing custom data for `ltp_core` training/evaluation or before using the bundled validator.

## Common directory convention

Use one directory per task with split files and a `vocabs/` subdirectory when the task needs vocab files:

```text
data-dir/
  train.*
  dev.*
  test.*
  vocabs/
    ...
```

Run:

```bash
python scripts/validate_ltp_training_data.py --task ner --data-dir data-dir
```

## BIO sequence labeling

Used by NER-like examples.

```text
字 B-Nh
符 I-Nh

另 O
句 O
```

Validator expectations:

- split files: `train.bio`, `dev.bio`, `test.bio`
- blank lines separate examples
- non-empty rows have at least token and label columns
- `vocabs/bio.txt` should exist when the config expects label vocabularies

## CoNLL-U dependency-style data

Used by dependency parsing style examples.

```text
1	他	_	_	r	_	2	SBV	_	_
2	叫	_	_	v	_	0	HED	_	_
```

Validator expectations:

- split files: `train.conllu`, `dev.conllu`, `test.conllu`
- token rows have at least 8 tab-separated fields
- common vocab files include `word.txt`, `word_char.txt`, `upos.txt`, `xpos.txt`, `deprel.txt`, and related feature/dependency vocab files when used by configs

## SRL text data

SRL examples use text files plus role/predicate vocabs.

Validator expectations:

- split files: `train.txt`, `dev.txt`, `test.txt`
- files are non-empty and line-oriented
- `vocabs/arguments.txt` and `vocabs/predicate.txt` should exist

## CWS/POS task data

CWS and POS adapters are configured separately but generally need train/dev/test split files and vocab labels consistent with the selected adapter. If using a custom format, document the adapter and tokenizer assumptions with the training command.

## Data-preparation checklist

- Keep train/dev/test splits separate and deterministic.
- Keep vocabs versioned with the dataset and config.
- Validate file encodings as UTF-8 before training.
- Make label sets explicit for custom NER/POS/SRL tasks.
- Use tiny fixtures to test the data loader before running full training.
- Record tokenizer/backbone and `max_length` decisions because neural tokenization can truncate long examples.
