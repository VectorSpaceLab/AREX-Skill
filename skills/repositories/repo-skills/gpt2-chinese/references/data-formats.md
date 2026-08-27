# Data Formats

## Purpose

Read this when you need to know what shape the corpora, tokenized pieces, generated outputs, and vocabulary files must have.

## Corpus inputs

### `train.json` and `eval.json`

The main training and evaluation scripts expect a JSON list of full article strings.

Example:

```json
[
  "第一篇文章的正文",
  "第二篇文章的正文",
  "第三篇文章的正文"
]
```

Important details:

- Each list element is an article, not a filename or URL.
- Newlines inside an article are rewritten to ` [SEP] ` before tokenization.
- Very short articles can be filtered out with `--min_length`.

## Tokenized piece files

### `data/tokenized/tokenized_train_*.txt`

Training and evaluation convert each corpus shard into integer token ids.

Format differences:

- `train.py` and `eval.py` write space-separated ids into one file per shard.
- `train_single.py` writes one shard per file and ends each shard with a newline.
- The scripts then read those files back as plain integer sequences.

The tokenized directory is an intermediate artifact, not a public data format. You can delete and rebuild it with `--raw`.

## Generated outputs

### `generate.py`

- Prints the sampled text to stdout.
- With `--save_samples`, also writes a `samples.txt` file in the chosen output directory.

### `generate_texts.py`

- Writes one file per generated article.
- Filenames follow `<title-index>-<article-index>.txt`.
- The text is postprocessed so `[MASK]` is removed and `[CLS]` / `[SEP]` become line breaks.

## Vocabulary files

### `cache/vocab_small.txt`

Compact BERT-style vocabulary used by the smaller config and most smoke checks.

### `cache/vocab.txt`

Larger BERT-style vocabulary for the broader default config.

### `cache/vocab_seg.txt`

Word-level vocabulary used by the `--segment` path.

### `cache/vocab_all.txt` and `cache/vocab_guwen.txt`

Alternate vocabulary bundles for broader or classical-Chinese coverage.

The vocabulary file and the model config `vocab_size` should match.

## Config files

### `config/model_config_test.json`

Tiny smoke config used for fast local checks.

### `config/model_config_small.json`

Compact default config for smaller experiments.

### `config/model_config.json`

Larger default config for full experiments.

The config files are standard GPT-2 JSON configs with `n_ctx`, `n_layer`, `n_head`, `n_embd`, and `vocab_size` fields.
