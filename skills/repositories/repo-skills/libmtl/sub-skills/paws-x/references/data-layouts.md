# PAWS-X Data Layouts

## Raw TSV files

The multilingual benchmark expects a dataset root like this:

```text
pawsx/
├── train-en.tsv
├── dev-en.tsv
├── test-en.tsv
├── train-zh.tsv
├── dev-zh.tsv
├── test-zh.tsv
├── train-de.tsv
├── dev-de.tsv
├── test-de.tsv
├── train-es.tsv
├── dev-es.tsv
└── test-es.tsv
```

The supported languages are:

- `en`
- `zh`
- `de`
- `es`

## Cached features

The loader writes cached tokenized features beside the raw TSV files. The names
follow the pattern:

```text
cached_feature_<split>_<language>_<model>_<max_length>
```

## Preprocessing helpers

The raw preprocess helpers are legacy-sensitive and network-backed. Treat them
as reference material unless the environment is explicitly prepared for that
path.

## Minimal validation idea

A valid setup should have all twelve TSV files and a writable cache directory.
